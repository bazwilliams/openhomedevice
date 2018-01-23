import requests
import re

from openhomedevice.RootDevice import RootDevice
from openhomedevice.TrackInfoParser import TrackInfoParser
from openhomedevice.Soap import soapRequest

import xml.etree.ElementTree as etree

class Device(object):

    def __init__(self, location):
        xmlDesc = requests.get(location).text.encode('utf-8')
        self.rootDevice = RootDevice(xmlDesc, location)

    def Uuid(self):
        return self.rootDevice.Device().Uuid()

    def HasTransportService(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        return service is not None

    def Name(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        product = soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return productXml[0].find("{%s}ProductResponse/Name" % service.Type()).text.encode('utf-8')

    def Room(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        product = soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return productXml[0].find("{%s}ProductResponse/Room" % service.Type()).text.encode('utf-8')

    def SetStandby(self, standbyRequested):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")

        valueString = None
        if standbyRequested:
            valueString = "<Value>1</Value>"
        else:
            valueString = "<Value>0</Value>"
        soapRequest(service.ControlUrl(), service.Type(), "SetStandby", valueString)

    def IsInStandby(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        standbyState = soapRequest(service.ControlUrl(), service.Type(), "Standby", "")

        standbyStateXml = etree.fromstring(standbyState)
        return standbyStateXml[0].find("{%s}StandbyResponse/Value" % service.Type()).text == "1"

    def TransportState(self):
        if self.HasTransportService():
            service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
            transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

            transportStateXml = etree.fromstring(transportState)
            return transportStateXml[0].find("{%s}TransportStateResponse/State" % service.Type()).text
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.RadioTransportState()
            if source["type"] == "Playlist":
                return self.PlaylistTransportState()
            return ""

    def Play(self):
        if self.HasTransportService():
            self.PlayTransport()
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.PlayRadio()
            if source["type"] == "Playlist":
                return self.PlayPlaylist()

    def PlayMedia(self, track_details):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")

        didl_lite = '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">' \
                    '<item id="" parentID="" restricted="True">' \
                    '<dc:title>' + track_details['title'] + '</dc:title>' \
                    '<res protocolInfo="*:*:*:*">' + track_details['uri'] + '</res>' \
                    '<upnp:albumArtURI>' + track_details['albumArtwork'] + '</upnp:albumArtURI>' \
                    '<upnp:class>object.item.audioItem</upnp:class>' \
                    '</item>' \
                    '</DIDL-Lite>'

        channelValue = ("<Uri>%s</Uri><Metadata>%s</Metadata>" % (track_details["uri"], didl_lite))
        soapRequest(service.ControlUrl(), service.Type(), "SetChannel", channelValue)

        self.PlayRadio()

    def Stop(self):
        if self.HasTransportService():
            self.StopTransport()
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.StopRadio()
            if source["type"] == "Playlist":
                return self.StopPlaylist()

    def Pause(self):
        if self.HasTransportService():
            self.PauseTransport()
        else:
            source = self.Source()
            if source["type"] == "Radio":
                return self.StopRadio()
            if source["type"] == "Playlist":
                return self.PausePlaylist()

    def Skip(self, offset):
        if self.HasTransportService():
            service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")

            command = None
            if offset > 0:
                command = "SkipNext"
            else:
                command = "SkipPrevious"

            for x in range(0, abs(offset)):
                soapRequest(service.ControlUrl(), service.Type(), command, "")
        else:
            source = self.Source()
            if source["type"] == "Playlist":
                service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")

                command = None
                if offset > 0:
                    command = "Next"
                else:
                    command = "Previous"

                for x in range(0, abs(offset)):
                    soapRequest(service.ControlUrl(), service.Type(), command, "")

    def RadioTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{%s}TransportStateResponse/Value" % service.Type()).text

    def PlaylistTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{%s}TransportStateResponse/Value" % service.Type()).text

    def PlayTransport(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PlayRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PlayPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PauseTransport(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    def PausePlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    def StopTransport(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Transport")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def StopRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def StopPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def Source(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        source = soapRequest(service.ControlUrl(), service.Type(), "SourceIndex", "")

        sourceXml = etree.fromstring(source)
        sourceIndex = sourceXml[0].find("{%s}SourceIndexResponse/Value" % service.Type()).text

        sourceInfo = soapRequest(service.ControlUrl(), service.Type(), "Source", ("<Index>%s</Index>" % int(sourceIndex)))
        sourceInfoXml = etree.fromstring(sourceInfo)

        sourceName = sourceInfoXml[0].find("{%s}SourceResponse/Name" % service.Type()).text
        sourceType = sourceInfoXml[0].find("{%s}SourceResponse/Type" % service.Type()).text

        return {
            "type": sourceType,
            "name": sourceName
        }

    def VolumeEnabled(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        return service is not None

    def VolumeLevel(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")

        if service is None:
            return None

        volume = soapRequest(service.ControlUrl(), service.Type(), "Volume", "")

        volumeXml = etree.fromstring(volume)
        return int(volumeXml[0].find("{%s}VolumeResponse/Value" % service.Type()).text)

    def IsMuted(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")

        if service is None:
            return None

        mute = soapRequest(service.ControlUrl(), service.Type(), "Mute", "")

        muteXml = etree.fromstring(mute)
        return muteXml[0].find("{%s}MuteResponse/Value" % service.Type()).text == "true"

    def SetVolumeLevel(self, volumeLevel):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        valueString = ("<Value>%s</Value>" % int(volumeLevel))
        soapRequest(service.ControlUrl(), service.Type(), "SetVolume", valueString)

    def IncreaseVolume(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        soapRequest(service.ControlUrl(), service.Type(), "VolumeInc", "")

    def DecreaseVolume(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        soapRequest(service.ControlUrl(), service.Type(), "VolumeDec", "")

    def SetMute(self, muteRequested):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        valueString = None
        if muteRequested:
            valueString = "<Value>1</Value>"
        else:
            valueString = "<Value>0</Value>"
        soapRequest(service.ControlUrl(), service.Type(), "SetMute", valueString)

    def SetSource(self, index):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        valueString = ("<Value>%s</Value>" % int(index))
        soapRequest(service.ControlUrl(), service.Type(), "SetSourceIndex", valueString)

    def Sources(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        sources = soapRequest(service.ControlUrl(), service.Type(), "SourceXml", "")

        sourcesXml = etree.fromstring(sources)
        sourcesList = sourcesXml[0].find("{%s}SourceXmlResponse/Value" % service.Type()).text

        sourcesListXml = etree.fromstring(sourcesList)

        sources = []
        index = 0
        for sourceXml in sourcesListXml:
            visible = sourceXml.find("Visible").text == "true"
            if visible:
                sources.append({
                    "index": index,
                    "name": sourceXml.find("Name").text,
                    "type": sourceXml.find("Type").text
                })
            index = index + 1
        return sources

    def TrackInfo(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Info")
        trackInfoString = soapRequest(service.ControlUrl(), service.Type(), "Track", "")

        trackInfoParser = TrackInfoParser(trackInfoString)

        return trackInfoParser.TrackInfo()

    def GetConfigurationKeys(self):
        import json
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Config")
        keys = soapRequest(service.ControlUrl(), service.Type(), "GetKeys", "")

        keysXml = etree.fromstring(keys)
        keysArray = keysXml[0].find("{%s}GetKeysResponse/KeyList" % service.Type()).text

        return json.loads(keysArray)

    def GetConfiguration(self, key):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Config")
        keyString = ("<Key>%s</Key>" % key)
        configurationValue = soapRequest(service.ControlUrl(), service.Type(), "GetValue", keyString)

        configurationValueXml = etree.fromstring(configurationValue)
        return configurationValueXml[0].find("{%s}GetValueResponse/Value" % service.Type()).text

    def SetConfiguration(self, key, value):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Config")
        configValue = ("<Key>%s</Key><Value>%s</Value>" % (key, value))
        soapRequest(service.ControlUrl(), service.Type(), "SetValue", configValue)

    def GetLog(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Debug")
        return soapRequest(service.ControlUrl(), service.Type(), "GetLog", "").decode('utf-8').split("\n")
