# import requests
# import re
import json

from async_upnp_client import UpnpFactory
from async_upnp_client.aiohttp import AiohttpRequester

from openhomedevice.TrackInfoParser import TrackInfoParser
from openhomedevice.DidlLite import didlLiteString
import xml.etree.ElementTree as etree


class Device(object):
    def __init__(self, location):
        self.location = location

    async def init(self):
        requester = AiohttpRequester()
        factory = UpnpFactory(requester)
        self.device = await factory.async_create_device(self.location)

    async def uuid(self):
        return self.device.udn

    async def name(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Product:3"
        )
        action = service.action('Product')
        result = await action.async_call()
        return result['Name']

    async def room(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Product:3"
        )
        action = service.action('Product')
        result = await action.async_call()
        return result['Room']

    # def SetStandby(self, standbyRequested):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Product"
    #     )

    #     valueString = None
    #     if standbyRequested:
    #         valueString = "<Value>1</Value>"
    #     else:
    #         valueString = "<Value>0</Value>"
    #     soapRequest(service.ControlUrl(), service.Type(), "SetStandby", valueString)

    async def is_in_standby(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Product:3"
        )
        action = service.action('Standby')
        result = await action.async_call()
        return result['Value']

    async def transport_state(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Transport:1"
        )
        action = service.action('TransportState')
        result = await action.async_call()
        return result['State']

    # def Play(self):
    #     if self.HasTransportService():
    #         self.PlayTransport()
    #     else:
    #         source = self.Source()
    #         if source["type"] == "Radio":
    #             return self.PlayRadio()
    #         if source["type"] == "Playlist":
    #             return self.PlayPlaylist()

    # def PlayMedia(self, track_details):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Radio"
    #     )
    #     if track_details:
    #         uri = track_details.get("uri", "")
    #         channelValueString = "<Uri>{0}</Uri><Metadata>{1}</Metadata>".format(
    #             uri, didlLiteString(track_details)
    #         )
    #         soapRequest(
    #             service.ControlUrl(), service.Type(), "SetChannel", channelValueString
    #         )
    #         self.PlayRadio()

    # def Stop(self):
    #     if self.HasTransportService():
    #         self.StopTransport()
    #     else:
    #         source = self.Source()
    #         if source["type"] == "Radio":
    #             return self.StopRadio()
    #         if source["type"] == "Playlist":
    #             return self.StopPlaylist()

    # def Pause(self):
    #     if self.HasTransportService():
    #         self.PauseTransport()
    #     else:
    #         source = self.Source()
    #         if source["type"] == "Radio":
    #             return self.StopRadio()
    #         if source["type"] == "Playlist":
    #             return self.PausePlaylist()

    # def Skip(self, offset):
    #     if self.HasTransportService():
    #         service = self.device.service(
    #             "urn:av-openhome-org:serviceId:Transport"
    #         )

    #         command = None
    #         if offset > 0:
    #             command = "SkipNext"
    #         else:
    #             command = "SkipPrevious"

    #         for x in range(0, abs(offset)):
    #             soapRequest(service.ControlUrl(), service.Type(), command, "")
    #     else:
    #         source = self.Source()
    #         if source["type"] == "Playlist":
    #             service = self.device.service(
    #                 "urn:av-openhome-org:serviceId:Playlist"
    #             )

    #             command = None
    #             if offset > 0:
    #                 command = "Next"
    #             else:
    #                 command = "Previous"

    #             for x in range(0, abs(offset)):
    #                 soapRequest(service.ControlUrl(), service.Type(), command, "")

    # def RadioTransportState(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Radio"
    #     )
    #     transportState = soapRequest(
    #         service.ControlUrl(), service.Type(), "TransportState", ""
    #     )

    #     transportStateXml = etree.fromstring(transportState)
    #     return (
    #         transportStateXml[0]
    #         .find("{%s}TransportStateResponse/Value" % service.Type())
    #         .text
    #     )

    # def PlaylistTransportState(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Playlist"
    #     )
    #     transportState = soapRequest(
    #         service.ControlUrl(), service.Type(), "TransportState", ""
    #     )

    #     transportStateXml = etree.fromstring(transportState)
    #     return (
    #         transportStateXml[0]
    #         .find("{%s}TransportStateResponse/Value" % service.Type())
    #         .text
    #     )

    # def PlayTransport(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Transport"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    # def PlayRadio(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Radio"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    # def PlayPlaylist(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Playlist"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Play", "")

    # def PauseTransport(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Transport"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    # def PausePlaylist(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Playlist"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Pause", "")

    # def StopTransport(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Transport"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    # def StopRadio(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Radio"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    # def StopPlaylist(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Playlist"
    #     )
    #     soapRequest(service.ControlUrl(), service.Type(), "Stop", "")

    async def source(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Product:3"
        )
        indexAction = service.action('SourceIndex')
        indexResult = await indexAction.async_call()
        sourceIndex = indexResult['Value']

        sourceAction = service.action('Source')
        sourceResult = await sourceAction.async_call(Index=sourceIndex)
        return { "type": sourceResult['Type'], "name": sourceResult['Name'] }

    async def volume_enabled(self):
        return self.device.has_service(
            "urn:av-openhome-org:service:Volume:4"
        )

    async def volume_level(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Volume:4"
        )
        action = service.action('Volume')
        result = await action.async_call()
        return result['Value']

    async def is_muted(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Volume:4"
        )
        action = service.action('Mute')
        result = await action.async_call()
        return result['Value']

    # def SetVolumeLevel(self, volumeLevel):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Volume"
    #     )

    #     if service is None:
    #         return None

    #     valueString = "<Value>%s</Value>" % int(volumeLevel)
    #     soapRequest(service.ControlUrl(), service.Type(), "SetVolume", valueString)

    # def IncreaseVolume(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Volume"
    #     )

    #     if service is None:
    #         return None

    #     soapRequest(service.ControlUrl(), service.Type(), "VolumeInc", "")

    # def DecreaseVolume(self):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Volume"
    #     )

    #     if service is None:
    #         return None

    #     soapRequest(service.ControlUrl(), service.Type(), "VolumeDec", "")

    # def SetMute(self, muteRequested):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Volume"
    #     )

    #     if service is None:
    #         return None

    #     valueString = None
    #     if muteRequested:
    #         valueString = "<Value>1</Value>"
    #     else:
    #         valueString = "<Value>0</Value>"
    #     soapRequest(service.ControlUrl(), service.Type(), "SetMute", valueString)

    # def SetSource(self, index):
    #     service = self.device.service(
    #         "urn:av-openhome-org:serviceId:Product"
    #     )
    #     valueString = "<Value>%s</Value>" % int(index)
    #     soapRequest(service.ControlUrl(), service.Type(), "SetSourceIndex", valueString)

    async def sources(self):
        service = self.device.service(
            "urn:av-openhome-org:service:Product:3"
        )
        action = service.action('SourceXml')
        result = await action.async_call()
        sourcesListXml = etree.fromstring(result['Value'])

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

    async def track_info(self):
        service = self.device.service("urn:av-openhome-org:service:Info:1")
        action = service.action('Track')
        result = await action.async_call()
        track_info_parser = TrackInfoParser(result['Metadata'])

        return track_info_parser.track_info()

    async def pins(self):
        pins = list()

        service = self.device.service("urn:av-openhome-org:service:Pins:1")
        action = service.action('GetDeviceMax')

        max_pins = (await action.async_call())['DeviceMax']
        pin_id_array = await self._get_pin_id_array()
        pin_metadata = await self._pin_metadata(pin_id_array)

        for i in range(max_pins):
            if pin_metadata[i].get("id") > 0:
                pin = {"index": i + 1, "title": pin_metadata[i].get("title"), "artworkUri": pin_metadata[i].get("artworkUri")}
                pins.append(pin)
        return pins

    async def _get_pin_id_array(self):
        service = self.device.service("urn:av-openhome-org:service:Pins:1")
        action = service.action('GetIdArray')
        result = await action.async_call()
        
        return json.loads(result['IdArray'])

    # def InvokePin(self, pinId):
    #     service = self.device.service("urn:av-openhome-org:serviceId:Pins")
    #     if service is None:
    #         return None

    #     indexValue = "<Index>%s</Index>" % (pinId - 1)
    #     soapRequest(service.ControlUrl(), service.Type(), "InvokeIndex", indexValue)

    async def _pin_metadata(self, ids):
        service = self.device.service("urn:av-openhome-org:service:Pins:1")
        action = service.action('ReadList')
        result = await action.async_call(Ids=json.dumps(ids))
        return json.loads(result['List'])
