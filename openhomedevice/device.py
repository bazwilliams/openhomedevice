import functools
import json
import asyncio

from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.aiohttp import AiohttpRequester, AiohttpSessionRequester
from async_upnp_client.exceptions import (
    UpnpCommunicationError,
    UpnpConnectionError,
    UpnpConnectionTimeoutError,
    UpnpError,
    UpnpResponseError,
)
# from async_upnp_client.aiohttp import AiohttpNotifyServer

import openhomedevice.didl_lite as didl_lite
import xml.etree.ElementTree as etree

from openhomedevice.exceptions import (
    OpenhomeConnectionError,
    OpenhomeDeviceError,
    OpenhomeTimeoutError,
)


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


def _translates_errors(func):
    """Re-raise async_upnp_client errors as this library's own.

    Applied to every public coroutine that talks to the device. Private
    helpers are left undecorated because they are only ever reached through
    a decorated method, so their errors are translated on the way out.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UpnpConnectionTimeoutError as err:
            raise OpenhomeTimeoutError(str(err)) from err
        except UpnpConnectionError as err:
            raise OpenhomeConnectionError(str(err)) from err
        except UpnpResponseError as err:
            # An HTTP error status: the device answered, it just did not
            # like the request. Checked before UpnpCommunicationError,
            # which it subclasses.
            raise OpenhomeDeviceError(str(err)) from err
        except UpnpCommunicationError as err:
            raise OpenhomeConnectionError(str(err)) from err
        except UpnpError as err:
            # SOAP faults, unparseable XML and bad values all land here.
            raise OpenhomeDeviceError(str(err)) from err

    return wrapper


class Device(object):
    def __init__(self, location, session=None):
        """Create a device for the description document at location.

        Pass session, an aiohttp.ClientSession, to reuse an existing session
        and its connection pool. Without one every request opens and closes
        a session of its own, which is wasteful when polling a device. The
        session is not closed by this library: whoever created it owns it.
        """
        self.location = location
        self.session = session

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
        self.update_service = self.device.service_id("urn:linn-co-uk:serviceId:Update")
        self.sender_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Sender"
        )
        self.receiver_service = self.device.service_id(
            "urn:av-openhome-org:serviceId:Receiver"
        )

    @_translates_errors
    async def init(self):
        if self.session is not None:
            requester = AiohttpSessionRequester(self.session)
        else:
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

    def manufacturer(self):
        return self.device.manufacturer
    
    def model_name(self):
        return self.device.model_name
    
    def friendly_name(self):
        return self.device.friendly_name

    @_translates_errors
    async def name(self):
        action = self.product_service.action("Product")
        return (await action.async_call())["Name"]

    @_translates_errors
    async def room(self):
        action = self.product_service.action("Product")
        return (await action.async_call())["Room"]

    @_translates_errors
    async def set_standby(self, standby_requested):
        await self.product_service.action("SetStandby").async_call(
            Value=standby_requested
        )

    @_translates_errors
    async def is_in_standby(self):
        action = self.product_service.action("Standby")
        return (await action.async_call())["Value"]

    @_translates_errors
    async def transport_state(self):
        if self.transport_service:
            action = self.transport_service.action("TransportState")
            return (await action.async_call()).get("State")

        if (await self.source())["type"] == "Radio":
            action = self.radio_service.action("TransportState")
            return (await action.async_call()).get("Value")

        action = self.playlist_service.action("TransportState")
        return (await action.async_call()).get("Value")

    @_translates_errors
    async def play(self):
        if self.transport_service:
            await self.transport_service.action("Play").async_call()
        else:
            if (await self.source())["type"] == "Radio":
                await self.radio_service.action("Play").async_call()
            else:
                await self.playlist_service.action("Play").async_call()

    @_translates_errors
    async def play_media(self, track_details):
        if self.radio_service and track_details:
            set_channel_action = self.radio_service.action("SetChannel")
            uri = track_details.get("uri", "")
            await set_channel_action.async_call(
                Uri=uri, Metadata=didl_lite.generate_string(track_details)
            )
            await self.radio_service.action("Play").async_call()

    @_translates_errors
    async def stop(self):
        if self.transport_service:
            await self.transport_service.action("Stop").async_call()
        else:
            if (await self.source())["type"] == "Radio":
                await self.radio_service.action("Stop").async_call()
            else:
                await self.playlist_service.action("Stop").async_call()

    @_translates_errors
    async def pause(self):
        if self.transport_service:
            await self.transport_service.action("Pause").async_call()
        else:
            if (await self.source())["type"] == "Radio":
                await self.radio_service.action("Pause").async_call()
            else:
                await self.playlist_service.action("Pause").async_call()

    @_translates_errors
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

    @_translates_errors
    async def source(self):
        index_action = self.product_service.action("SourceIndex")
        source_index = (await index_action.async_call())["Value"]
        source_action = self.product_service.action("Source")
        source_result = await source_action.async_call(Index=source_index)
        return {"type": source_result["Type"], "name": source_result["Name"]}

    @property
    def volume_enabled(self):
        return self.volume_service is not None

    @_translates_errors
    async def volume(self):
        if not self.volume_enabled:
            return None

        action = self.volume_service.action("Volume")
        return (await action.async_call())["Value"]

    @_translates_errors
    async def is_muted(self):
        if not self.volume_enabled:
            return None

        action = self.volume_service.action("Mute")
        result = await action.async_call()
        return result["Value"]

    @_translates_errors
    async def set_volume(self, volume_level):
        if self.volume_enabled:
            action = self.volume_service.action("SetVolume")
            await action.async_call(Value=volume_level)

    @_translates_errors
    async def increase_volume(self):
        if self.volume_enabled:
            await self.volume_service.action("VolumeInc").async_call()

    @_translates_errors
    async def decrease_volume(self):
        if self.volume_enabled:
            await self.volume_service.action("VolumeDec").async_call()

    @_translates_errors
    async def set_mute(self, mute_requested):
        if self.volume_enabled:
            await self.volume_service.action("SetMute").async_call(Value=mute_requested)

    @_translates_errors
    async def set_source(self, index):
        await self.product_service.action("SetSourceIndex").async_call(Value=index)

    @_translates_errors
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

    @_translates_errors
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

    @_translates_errors
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

    @_translates_errors
    async def invoke_pin(self, pin_id):
        if self.pins_enabled:
            await self.pins_service.action("InvokeIndex").async_call(Index=(pin_id - 1))

    @_translates_errors
    async def software_status(self):
        if self.update_service:
            action = self.update_service.action("GetSoftwareStatus")
            result = await action.async_call()
            return json.loads(result["SoftwareStatus"])

    @_translates_errors
    async def check_latest_firmware(self):
        if self.update_service:
            action = await self.update_service.action("CheckNow").async_call()

    @_translates_errors
    async def update_firmware(self):
        if self.update_service:
            await self.update_service.action("Apply").async_call()

    @property
    def songcast_sender_enabled(self):
        return self.sender_service is not None

    @property
    def songcast_receiver_enabled(self):
        return self.receiver_service is not None

    @_translates_errors
    async def songcast_sender_status(self):
        """Sending state of this device: Enabled, Disabled or Blocked."""
        if not self.songcast_sender_enabled:
            return None

        action = self.sender_service.action("Status")
        return (await action.async_call())["Value"]

    @_translates_errors
    async def songcast_sender_audio(self):
        """True when this device is actively broadcasting audio."""
        if not self.songcast_sender_enabled:
            return None

        action = self.sender_service.action("Audio")
        return (await action.async_call())["Value"]

    @_translates_errors
    async def songcast_sender(self):
        """This device as a songcast sender, or None if it cannot send."""
        if not self.songcast_sender_enabled:
            return None

        action = self.sender_service.action("Metadata")
        metadata = (await action.async_call())["Value"]
        uri = didl_lite.parse(metadata).get("uri")

        if not uri:
            return None

        return {"uri": uri, "metadata": metadata}

    @_translates_errors
    async def songcast_receiver_sender(self):
        """The sender this device is following, or None if it is not in a group."""
        if not self.songcast_receiver_enabled:
            return None

        action = self.receiver_service.action("Sender")
        result = await action.async_call()
        uri = result.get("Uri")

        if not uri:
            return None

        return {"uri": uri, "metadata": result.get("Metadata")}

    @_translates_errors
    async def songcast_receiver_transport_state(self):
        if not self.songcast_receiver_enabled:
            return None

        action = self.receiver_service.action("TransportState")
        return (await action.async_call())["Value"]

    async def _receiver_source_index(self):
        """Index of the Receiver source, which may be hidden from sources()."""
        action = self.product_service.action("SourceXml")
        result = await action.async_call()

        for index, source_xml in enumerate(etree.fromstring(result["Value"])):
            if source_xml.find("Type").text == "Receiver":
                return index

        return None

    @_translates_errors
    async def songcast_receiver_join(self, sender):
        """Follow a sender, as returned by songcast_sender() on another device.

        Linn firmware selects the Receiver source itself in response to Play, so
        the source is only set explicitly when it has not already switched.
        """
        if not self.songcast_receiver_enabled or not sender:
            return

        await self.receiver_service.action("SetSender").async_call(
            Uri=sender["uri"], Metadata=sender.get("metadata", "")
        )
        await self.receiver_service.action("Play").async_call()

        index = await self._receiver_source_index()
        if index is None:
            return

        current = (await self.product_service.action("SourceIndex").async_call())[
            "Value"
        ]
        if current != index:
            await self.set_source(index)

    @_translates_errors
    async def songcast_receiver_leave(self):
        """Stop following a sender and clear it, so no stale sender is left set."""
        if not self.songcast_receiver_enabled:
            return

        await self.receiver_service.action("Stop").async_call()
        await self.receiver_service.action("SetSender").async_call(Uri="", Metadata="")
