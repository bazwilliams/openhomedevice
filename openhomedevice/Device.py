import json
import asyncio

from async_upnp_client import UpnpFactory
from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.aiohttp import AiohttpNotifyServer

import openhomedevice.didl_lite as didl_lite
import xml.etree.ElementTree as etree


# def on_event(service, service_variables):
#     """Handle a UPnP event."""
#     print(
#         "State variable change for %s, variables: %s",
#         service,
#         ",".join([sv.name for sv in service_variables]),
#     )
#     obj = {
#         "service_id": service.service_id,
#         "service_type": service.service_type,
#         "state_variables": {sv.name: sv.value for sv in service_variables},
#     }
#     print(json.dumps(obj))


class Device(object):
    def __init__(self, location):
        self.location = location

    def setup_services(self):
        self.product_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Product"
        )
        self.volume_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Volume"
        )
        self.transport_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Transport"
        )
        self.playlist_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Playlist"
        )
        self.info_service = self.device.service_id("urn:av-openhome-org:serviceId:Info")
        self.pins_service = self.device.service_id("urn:av-openhome-org:serviceId:Pins")
        self.radio_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Radio"
        )

    async def init(self):
        requester = AiohttpRequester()
        factory = UpnpFactory(requester)
        self.device = await factory.async_create_device(self.location)
        self.setup_services()

    # async def subscribe(self, service):
    #     service.on_event = on_event
    #     await self.server.event_handler.async_subscribe(service)

    # async def setup_subscriptions(self):
    #     self.server = AiohttpNotifyServer(self.device.requester, 41234)
    #     await self.server.start_server()
    #     print("Listening on: %s", self.server.callback_url)

    #     await self.subscribe(self.product_service)
    #     await self.subscribe(self.volume_service)
    #     await self.subscribe(self.transport_service)
    #     await self.subscribe(self.info_service)

    #     while True:
    #         await asyncio.sleep(120)
    #         await self.server.event_handler.async_resubscribe_all()

    def uuid(self):
        return self.device.udn

    async def name(self):
        action = self.product_service.action("Product")
        return (await action.async_call())["Name"]

    async def room(self):
        action = self.product_service.action("Product")
        return (await action.async_call())["Room"]

    async def set_standby(self, standby_requested):
        await self.product_service.action("SetStandby").async_call(
            Value=standby_requested
        )

    async def is_in_standby(self):
        action = self.product_service.action("Standby")
        return (await action.async_call())["Value"]

    async def transport_state(self):
        if self.transport_service:
            action = self.transport_service.action("TransportState")
            return (await action.async_call()).get("State")

        if (await self.source())["type"] == "Radio":
            action = self.radio_service.action("TransportState")
            return (await action.async_call()).get("Value")

        action = self.playlist_service.action("TransportState")
        return (await action.async_call()).get("Value")

    async def play(self):
        if self.transport_service:
            await self.transport_service.action("Play").async_call()
        else:
            if (await self.source())["type"] == "Radio":
                await self.radio_service.action("Play").async_call()
            else:
                await self.playlist_service.action("Play").async_call()

    async def play_media(self, track_details):
        if self.radio_service and track_details:
            set_channel_action = self.radio_service.action("SetChannel")
            uri = track_details.get("uri", "")
            await set_channel_action.async_call(
                Uri=uri, Metadata=didl_lite.generate_string(track_details)
            )
            await self.radio_service.action("Play").async_call()

    async def stop(self):
        if self.transport_service:
            await self.transport_service.action("Stop").async_call()
        else:
            if (await self.source())["type"] == "Radio":
                await self.radio_service.action("Stop").async_call()
            else:
                await self.playlist_service.action("Stop").async_call()

    async def pause(self):
        if self.transport_service:
            await self.transport_service.action("Pause").async_call()
        else:
            if (await self.source())["type"] == "Radio":
                await self.radio_service.action("Pause").async_call()
            else:
                await self.playlist_service.action("Pause").async_call()

    async def skip(self, offset):
        action = None
        if self.transport_service:
            action = (
                self.transport_service.action("SkipNext")
                if offset > 0
                else self.transport_service.action("SkipPrevious")
            )
        else:
            if (await self.source())["type"] == "Playlist":
                action = (
                    self.playlist_service.action("Next")
                    if offset > 0
                    else self.playlist_service.action("Previous")
                )
        if action:
            for x in range(0, abs(offset)):
                await action.async_call()

    async def source(self):
        index_action = self.product_service.action("SourceIndex")
        source_index = (await index_action.async_call())["Value"]
        source_action = self.product_service.action("Source")
        source_result = await source_action.async_call(Index=source_index)
        return {"type": source_result["Type"], "name": source_result["Name"]}

    @property
    def volume_enabled(self):
        return self.volume_service is not None

    async def volume(self):
        if not self.volume_enabled:
            return None

        action = self.volume_service.action("Volume")
        return (await action.async_call())["Value"]

    async def is_muted(self):
        if not self.volume_enabled:
            return None

        action = self.volume_service.action("Mute")
        result = await action.async_call()
        return result["Value"]

    async def set_volume(self, volume_level):
        if self.volume_enabled:
            action = self.volume_service.action("SetVolume")
            await action.async_call(Value=volume_level)

    async def increase_volume(self):
        if self.volume_enabled:
            await self.volume_service.action("VolumeInc").async_call()

    async def decrease_volume(self):
        if self.volume_enabled:
            await self.volume_service.action("VolumeDec").async_call()

    async def set_mute(self, mute_requested):
        if self.volume_enabled:
            await self.volume_service.action("SetMute").async_call(Value=mute_requested)

    async def set_source(self, index):
        await self.product_service.action("SetSourceIndex").async_call(Value=index)

    async def sources(self):
        action = self.product_service.action("SourceXml")
        result = await action.async_call()
        sources_list_xml = etree.fromstring(result["Value"])

        sources = []
        index = 0
        for source_xml in sources_list_xml:
            visible = source_xml.find("Visible").text == "true"
            if visible:
                sources.append(
                    {
                        "index": index,
                        "name": source_xml.find("Name").text,
                        "type": source_xml.find("Type").text,
                    }
                )
            index = index + 1
        return sources

    async def track_info(self):
        action = self.info_service.action("Track")
        result = await action.async_call()
        return didl_lite.parse(result["Metadata"])

    @property
    def pins_enabled(self):
        return self.device.has_service("urn:av-openhome-org:service:Pins:1")

    async def _get_pin_id_array(self):
        action = self.pins_service.action("GetIdArray")
        result = await action.async_call()
        return json.loads(result["IdArray"])

    async def _pin_metadata(self, ids):
        action = self.pins_service.action("ReadList")
        result = await action.async_call(Ids=json.dumps(ids))
        return json.loads(result["List"])

    async def pins(self):
        if not self.pins_enabled:
            return []

        action = self.pins_service.action("GetDeviceMax")
        max_pins = (await action.async_call())["DeviceMax"]
        pin_id_array = await self._get_pin_id_array()
        pin_metadata = await self._pin_metadata(pin_id_array)

        pins = list()
        for i in range(max_pins):
            if pin_metadata[i].get("id") > 0:
                pin = {
                    "index": i + 1,
                    "title": pin_metadata[i].get("title"),
                    "artworkUri": pin_metadata[i].get("artworkUri"),
                }
                pins.append(pin)
        return pins

    async def invoke_pin(self, pin_id):
        if self.pins_enabled:
            await self.pins_service.action("InvokeIndex").async_call(Index=(pin_id - 1))
