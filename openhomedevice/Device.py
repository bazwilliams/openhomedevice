import requests

from openhomedevice.Upnp.Device import RootDevice
from openhomedevice.Upnp.Soap import soapRequest

import xml.etree.ElementTree as etree

class Device(object):

    def __init__(self, location):
        xmlDesc = requests.get(location).text.encode('utf-8')
        self.rootDevice = RootDevice(xmlDesc, location)

    def Uuid(self):
        return self.rootDevice.Device().Uuid()

    def Name(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        product = soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return productXml[0].find("{urn:av-openhome-org:service:Product:2}ProductResponse/Name").text.encode('utf-8')

    def Room(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        product = soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return productXml[0].find("{urn:av-openhome-org:service:Product:2}ProductResponse/Room").text.encode('utf-8')

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
        return standbyStateXml[0].find("{urn:av-openhome-org:service:Product:2}StandbyResponse/Value").text == "true"

    def TransportState(self):
        source = self.Source()
        if (source["type"] == "Radio"):
            return self.RadioTransportState()
        if (source["type"] == "Playlist"):
            return self.PlaylistTransportState()
        return ""

    def Play(self):
        source = self.Source()
        if (source["type"] == "Radio"):
            return self.PlayRadio()
        if (source["type"] == "Playlist"):
            return self.PlayPlaylist()

    def Stop(self):
        source = self.Source()
        if (source["type"] == "Radio"):
            return self.StopRadio()
        if (source["type"] == "Playlist"):
            return self.StopPlaylist()

    def Pause(self):
        source = self.Source()
        if (source["type"] == "Radio"):
            return self.StopRadio()
        if (source["type"] == "Playlist"):
            return self.PausePlaylist()

    def Skip(self, offset):
        source = self.Source()
        if (source["type"] == "Playlist"):
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
        return transportStateXml[0].find("{urn:av-openhome-org:service:Radio:1}TransportStateResponse/Value").text

    def PlaylistTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{urn:av-openhome-org:service:Playlist:1}TransportStateResponse/Value").text

    def PlayRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def StopRadio(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def PlayPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    def PausePlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    def StopPlaylist(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    def Source(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        source = soapRequest(service.ControlUrl(), service.Type(), "SourceIndex", "")

        sourceXml = etree.fromstring(source)
        sourceIndex = sourceXml[0].find("{urn:av-openhome-org:service:Product:2}SourceIndexResponse/Value").text

        sourceInfo = soapRequest(service.ControlUrl(), service.Type(), "Source", ("<Index>%s</Index>" % int(sourceIndex)))
        sourceInfoXml = etree.fromstring(sourceInfo)

        sourceName = sourceInfoXml[0].find("{urn:av-openhome-org:service:Product:2}SourceResponse/Name").text
        sourceType = sourceInfoXml[0].find("{urn:av-openhome-org:service:Product:2}SourceResponse/Type").text
        
        return {
            "type": sourceType,
            "name": sourceName
        }

    def VolumeLevel(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        volume = soapRequest(service.ControlUrl(), service.Type(), "Volume", "")

        volumeXml = etree.fromstring(volume)
        return int(volumeXml[0].find("{urn:av-openhome-org:service:Volume:2}VolumeResponse/Value").text)

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

    def IsMuted(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Volume")
        mute = soapRequest(service.ControlUrl(), service.Type(), "Mute", "")

        muteXml = etree.fromstring(mute)
        return muteXml[0].find("{urn:av-openhome-org:service:Volume:2}MuteResponse/Value").text == "true"

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
        sourcesList = sourcesXml[0].find("{urn:av-openhome-org:service:Product:2}SourceXmlResponse/Value").text

        sourcesListXml = etree.fromstring(sourcesList)

        sources = []
        index = 0
        for sourceXml in sourcesListXml:
            visible = sourceXml.find("Visible").text == "true"
            if (visible):
                sources.append({
                    "index": index,
                    "name": sourceXml.find("Name").text,
                    "type": sourceXml.find("Type").text
                })
            index = index + 1
        return sources

    def TrackInfo(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Info")
        trackInfo = soapRequest(service.ControlUrl(), service.Type(), "Track", "")
        
        trackInfoXml = etree.fromstring(trackInfo)

        if (trackInfoXml[0][0].find('Metadata').text == None):
            return {}

        metadata = trackInfoXml[0][0].find('Metadata').text.encode('utf-8')

        metadataXml = etree.fromstring(metadata)
        itemElement = metadataXml.find("{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item")
        
        albumArt = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI")
        album = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}album")
        artist = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}artist")
        title = itemElement.find("{http://purl.org/dc/elements/1.1/}title")

        trackDetails = {}

        trackDetails['title'] =  title.text if title != None else None
        trackDetails['album'] =  album.text if album != None else None
        trackDetails['albumArt'] =  albumArt.text if albumArt != None else None
        trackDetails['artist'] =  artist.text if artist != None else None

        return trackDetails
