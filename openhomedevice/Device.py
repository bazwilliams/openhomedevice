import http3
import re
import json

from openhomedevice.RootDevice import RootDevice
from openhomedevice.TrackInfoParser import TrackInfoParser
from openhomedevice.Soap import soapRequest
from openhomedevice.DidlLite import didlLiteString
import xml.etree.ElementTree as etree

class Device():
    @classmethod
    async def create(cls, location):
        client = http3.AsyncClient()
        self = Device()
        response = await client.get(location)
        if response.status_code == 200:
            xmlDesc = response.text.encode("utf-8")
            self.rootDevice = RootDevice(xmlDesc, location)
            return self
        raise Exception('Device Not Found')

    def Uuid(self):
        return self.rootDevice.Device().Uuid()

    def HasTransportService(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Transport"
        )
        return service is not None

    async def Name(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )
        product = await soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return (
            productXml[0]
            .find("{%s}ProductResponse/Name" % service.Type())
            .text.encode("utf-8")
        )

    async def Room(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )
        product = await soapRequest(service.ControlUrl(), service.Type(), "Product", "")

        productXml = etree.fromstring(product)
        return (
            productXml[0]
            .find("{%s}ProductResponse/Room" % service.Type())
            .text.encode("utf-8")
        )

    async def SetStandby(self, standbyRequested):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )

        valueString = None
        if standbyRequested:
            valueString = "<Value>1</Value>"
        else:
            valueString = "<Value>0</Value>"
        await soapRequest(service.ControlUrl(), service.Type(), "SetStandby", valueString)

    async def IsInStandby(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )
        standbyState = await soapRequest(service.ControlUrl(), service.Type(), "Standby", "")

        standbyStateXml = etree.fromstring(standbyState)
        return (
            standbyStateXml[0].find("{%s}StandbyResponse/Value" % service.Type()).text
            == "1"
        )

    async def TransportState(self):
        if self.HasTransportService():
            service = self.rootDevice.Device().Service(
                "urn:av-openhome-org:serviceId:Transport"
            )
            transportState = await soapRequest(
                service.ControlUrl(), service.Type(), "TransportState", ""
            )

            transportStateXml = etree.fromstring(transportState)
            return (
                transportStateXml[0]
                .find("{%s}TransportStateResponse/State" % service.Type())
                .text
            )
        else:
            source = await self.Source()
            if source["type"] == "Radio":
                return await self.RadioTransportState()
            if source["type"] == "Playlist":
                return await self.PlaylistTransportState()
            return ""

    async def Play(self):
        if self.HasTransportService():
            await self.PlayTransport()
        else:
            source = await self.Source()
            if await source["type"] == "Radio":
                return await self.PlayRadio()
            if await source["type"] == "Playlist":
                return await self.PlayPlaylist()

    async def PlayMedia(self, track_details):
        service = await self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Radio"
        )
        if track_details:
            uri = track_details.get("uri", "")
            channelValueString = "<Uri>{0}</Uri><Metadata>{1}</Metadata>".format(
                uri, didlLiteString(track_details)
            )
            await soapRequest(
                service.ControlUrl(), service.Type(), "SetChannel", channelValueString
            )
            await self.PlayRadio()

    async def Stop(self):
        if self.HasTransportService():
            await self.StopTransport()
        else:
            source = await self.Source()
            if source["type"] == "Radio":
                return await self.StopRadio()
            if source["type"] == "Playlist":
                return await self.StopPlaylist()

    async def Pause(self):
        if self.HasTransportService():
            await self.PauseTransport()
        else:
            source = await self.Source()
            if source["type"] == "Radio":
                return await self.StopRadio()
            if source["type"] == "Playlist":
                return await self.PausePlaylist()

    async def Skip(self, offset):
        if self.HasTransportService():
            service = self.rootDevice.Device().Service(
                "urn:av-openhome-org:serviceId:Transport"
            )

            command = None
            if offset > 0:
                command = "SkipNext"
            else:
                command = "SkipPrevious"

            for x in range(0, abs(offset)):
                await soapRequest(service.ControlUrl(), service.Type(), command, "")
        else:
            source = await self.Source()
            if source["type"] == "Playlist":
                service = self.rootDevice.Device().Service(
                    "urn:av-openhome-org:serviceId:Playlist"
                )

                command = None
                if offset > 0:
                    command = "Next"
                else:
                    command = "Previous"

                for x in range(0, abs(offset)):
                    await soapRequest(service.ControlUrl(), service.Type(), command, "")

    async def RadioTransportState(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Radio"
        )
        transportState = await soapRequest(
            service.ControlUrl(), service.Type(), "TransportState", ""
        )

        transportStateXml = etree.fromstring(transportState)
        return (
            transportStateXml[0]
            .find("{%s}TransportStateResponse/Value" % service.Type())
            .text
        )

    async def PlaylistTransportState(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Playlist"
        )
        transportState = await soapRequest(
            service.ControlUrl(), service.Type(), "TransportState", ""
        )

        transportStateXml = etree.fromstring(transportState)
        return (
            transportStateXml[0]
            .find("{%s}TransportStateResponse/Value" % service.Type())
            .text
        )

    async def PlayTransport(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Transport"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    async def PlayRadio(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Radio"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    async def PlayPlaylist(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Playlist"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    async def PauseTransport(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Transport"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    async def PausePlaylist(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Playlist"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    async def StopTransport(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Transport"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    async def StopRadio(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Radio"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    async def StopPlaylist(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Playlist"
        )
        await soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    async def Source(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )
        source = await soapRequest(service.ControlUrl(), service.Type(), "SourceIndex", "")

        sourceXml = etree.fromstring(source)
        sourceIndex = (
            sourceXml[0].find("{%s}SourceIndexResponse/Value" % service.Type()).text
        )

        sourceInfo = await soapRequest(
            service.ControlUrl(),
            service.Type(),
            "Source",
            ("<Index>%s</Index>" % int(sourceIndex)),
        )
        sourceInfoXml = etree.fromstring(sourceInfo)

        sourceName = (
            sourceInfoXml[0].find("{%s}SourceResponse/Name" % service.Type()).text
        )
        sourceType = (
            sourceInfoXml[0].find("{%s}SourceResponse/Type" % service.Type()).text
        )

        return {"type": sourceType, "name": sourceName}

    async def VolumeEnabled(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )
        return service is not None

    async def VolumeLevel(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )

        if service is None:
            return None

        volume = await soapRequest(service.ControlUrl(), service.Type(), "Volume", "")

        volumeXml = etree.fromstring(volume)
        return int(volumeXml[0].find("{%s}VolumeResponse/Value" % service.Type()).text)

    async def IsMuted(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )

        if service is None:
            return None

        mute = await soapRequest(service.ControlUrl(), service.Type(), "Mute", "")

        muteXml = etree.fromstring(mute)
        return muteXml[0].find("{%s}MuteResponse/Value" % service.Type()).text == "true"

    async def SetVolumeLevel(self, volumeLevel):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )

        if service is None:
            return None

        valueString = "<Value>%s</Value>" % int(volumeLevel)
        await soapRequest(service.ControlUrl(), service.Type(), "SetVolume", valueString)

    async def IncreaseVolume(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )

        if service is None:
            return None

        await soapRequest(service.ControlUrl(), service.Type(), "VolumeInc", "")

    async def DecreaseVolume(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )

        if service is None:
            return None

        await soapRequest(service.ControlUrl(), service.Type(), "VolumeDec", "")

    async def SetMute(self, muteRequested):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Volume"
        )

        if service is None:
            return None

        valueString = None
        if muteRequested:
            valueString = "<Value>1</Value>"
        else:
            valueString = "<Value>0</Value>"
        await soapRequest(service.ControlUrl(), service.Type(), "SetMute", valueString)

    async def SetSource(self, index):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )
        valueString = "<Value>%s</Value>" % int(index)
        await soapRequest(service.ControlUrl(), service.Type(), "SetSourceIndex", valueString)

    async def Sources(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Product"
        )
        sources = await soapRequest(service.ControlUrl(), service.Type(), "SourceXml", "")

        sourcesXml = etree.fromstring(sources)
        sourcesList = (
            sourcesXml[0].find("{%s}SourceXmlResponse/Value" % service.Type()).text
        )

        sourcesListXml = etree.fromstring(sourcesList)

        sources = []
        index = 0
        for sourceXml in sourcesListXml:
            visible = sourceXml.find("Visible").text == "true"
            if visible:
                sources.append(
                    {
                        "index": index,
                        "name": sourceXml.find("Name").text,
                        "type": sourceXml.find("Type").text,
                    }
                )
            index = index + 1
        return sources

    async def TrackInfo(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Info")
        trackInfoString = await soapRequest(service.ControlUrl(), service.Type(), "Track", "")

        trackInfoParser = TrackInfoParser(trackInfoString)

        return trackInfoParser.TrackInfo()

    async def GetConfigurationKeys(self):
        import json

        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Config"
        )
        keys = await soapRequest(service.ControlUrl(), service.Type(), "GetKeys", "")

        keysXml = etree.fromstring(keys)
        keysArray = keysXml[0].find("{%s}GetKeysResponse/KeyList" % service.Type()).text

        return json.loads(keysArray)

    async def GetConfiguration(self, key):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Config"
        )
        keyString = "<Key>%s</Key>" % key
        configurationValue = await soapRequest(
            service.ControlUrl(), service.Type(), "GetValue", keyString
        )

        configurationValueXml = etree.fromstring(configurationValue)
        return (
            configurationValueXml[0]
            .find("{%s}GetValueResponse/Value" % service.Type())
            .text
        )

    async def SetConfiguration(self, key, value):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Config"
        )
        configValue = "<Key>%s</Key><Value>%s</Value>" % (key, value)
        await soapRequest(service.ControlUrl(), service.Type(), "SetValue", configValue)

    async def GetLog(self):
        service = self.rootDevice.Device().Service(
            "urn:av-openhome-org:serviceId:Debug"
        )
        return (
            await soapRequest(service.ControlUrl(), service.Type(), "GetLog", "")
            .decode("utf-8")
            .split("\n")
        )

    async def Pins(self):
        pins = list()
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Pins")
        if service is None:
            return pins
        response = await soapRequest(service.ControlUrl(), service.Type(), "GetDeviceMax", "")
        xml = etree.fromstring(response)
        maxNumberOfPins = int(
            xml[0].find("{%s}GetDeviceMaxResponse/DeviceMax" % service.Type()).text
        )
        pinIdArray = await self._GetPinIdArray()
        pinMetadata = await self._PinMetadata(pinIdArray)
        for i in range(maxNumberOfPins):
            if pinMetadata[i].get("id") > 0:
                pin = {"index": i + 1, "title": pinMetadata[i].get("title"), "artworkUri": pinMetadata[i].get("artworkUri")}
                pins.append(pin)
        return pins

    async def _GetPinIdArray(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Pins")
        idArrayResponse = await soapRequest(
            service.ControlUrl(), service.Type(), "GetIdArray", ""
        )
        idArrayResponseXml = etree.fromstring(idArrayResponse)
        return json.loads(
            idArrayResponseXml[0]
            .find("{%s}GetIdArrayResponse/IdArray" % service.Type())
            .text
        )

    async def InvokePin(self, pinId):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Pins")
        if service is None:
            return None

        indexValue = "<Index>%s</Index>" % (pinId - 1)
        await soapRequest(service.ControlUrl(), service.Type(), "InvokeIndex", indexValue)

    async def _PinMetadata(self, ids):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Pins")
        idsValue = "<Ids>%s</Ids>" % json.dumps(ids)
        response = await soapRequest(
            service.ControlUrl(), service.Type(), "ReadList", idsValue
        )
        responseXml = etree.fromstring(response)
        return json.loads(
            responseXml[0].find("{%s}ReadListResponse/List" % service.Type()).text
        )
