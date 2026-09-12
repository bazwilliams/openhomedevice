import asyncio
import functools
import inspect
import json
import logging
from datetime import timedelta

from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.aiohttp import (
    AiohttpNotifyServer,
    AiohttpRequester,
    AiohttpSessionRequester,
)
from async_upnp_client.exceptions import (
    UpnpCommunicationError,
    UpnpConnectionError,
    UpnpConnectionTimeoutError,
    UpnpError,
    UpnpResponseError,
)
from async_upnp_client.utils import async_get_local_ip

import openhomedevice.didl_lite as didl_lite
import openhomedevice.source_list as source_list

from openhomedevice.events import EventTranslator
from openhomedevice.services import (
    INFO_SERVICE_ID,
    PINS_SERVICE_ID,
    PLAYLIST_SERVICE_ID,
    PRODUCT_SERVICE_ID,
    RADIO_SERVICE_ID,
    RECEIVER_SERVICE_ID,
    SENDER_SERVICE_ID,
    TRANSPORT_SERVICE_ID,
    UPDATE_SERVICE_ID,
    VOLUME_SERVICE_ID,
)
from openhomedevice.exceptions import (
    OpenhomeConnectionError,
    OpenhomeDeviceError,
    OpenhomeTimeoutError,
)

_LOGGER = logging.getLogger(__name__)

# What subscribe() and renew() ask for when the caller says nothing. The
# device caps this at its own maximum, and both return what it granted.
SUBSCRIBE_TIMEOUT = timedelta(minutes=30)


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
    def __init__(self, location, session=None, event_handler=None):
        """Create a device for the description document at location.

        Pass session, an aiohttp.ClientSession, to reuse an existing session
        and its connection pool. Without one every request opens and closes
        a session of its own, which is wasteful when polling a device. The
        session is not closed by this library: whoever created it owns it.

        Pass event_handler, an async_upnp_client UpnpEventHandler, to receive
        events through a notify server you already run, which is worth doing
        when several devices could otherwise each start a listener of their
        own. Without one subscribe() starts a notify server for this device
        and stops it again on unsubscribe(). As with the session, a handler
        you supply stays yours to shut down.
        """
        self.location = location
        self.session = session

        self._event_handler = event_handler
        self._notify_server = None
        # The SID of each live subscription.
        self._subscriptions = []
        self._callback = None
        self._translator = None
        self._callback_tasks = set()

    def setup_services(self):
        self.product_service = self.device.service_id(PRODUCT_SERVICE_ID)
        self.volume_service = self.device.service_id(VOLUME_SERVICE_ID)
        self.transport_service = self.device.service_id(TRANSPORT_SERVICE_ID)
        self.playlist_service = self.device.service_id(PLAYLIST_SERVICE_ID)
        self.info_service = self.device.service_id(INFO_SERVICE_ID)
        self.pins_service = self.device.service_id(PINS_SERVICE_ID)
        self.radio_service = self.device.service_id(RADIO_SERVICE_ID)
        self.update_service = self.device.service_id(UPDATE_SERVICE_ID)
        self.sender_service = self.device.service_id(SENDER_SERVICE_ID)
        self.receiver_service = self.device.service_id(RECEIVER_SERVICE_ID)

    @_translates_errors
    async def init(self):
        if self.session is not None:
            requester = AiohttpSessionRequester(self.session)
        else:
            requester = AiohttpRequester()
        factory = UpnpFactory(requester)
        self.device = await factory.async_create_device(self.location)
        self.setup_services()

    @property
    def is_subscribed(self):
        return bool(self._subscriptions)

    @property
    def events_enabled(self):
        """Needs Product, Transport and Info. Volume is optional, since a
        device at unity gain has no Volume service to advertise."""
        return all(
            service is not None
            for service in (
                self.product_service,
                self.transport_service,
                self.info_service,
            )
        )

    @_translates_errors
    async def subscribe(self, callback, timeout=SUBSCRIBE_TIMEOUT):
        """Call callback with a dict of changes whenever the device reports one.

        Each key is named for the method returning the same value, and only
        what changed is present, except on the first event after subscribing
        when the device sends its whole state. callback may be a plain
        function or a coroutine function.

        Raises OpenhomeDeviceError when events_enabled is False. Subscribing
        again replaces the callback rather than stacking.

        Returns the lease the device granted, which is the shortest of the
        grants across the services subscribed to and no longer than timeout.
        A subscription lasts only that long: call renew() before it runs out
        or the device forgets it and stops sending events. Nothing here
        renews on your behalf.
        """
        if not self.events_enabled:
            raise OpenhomeDeviceError(
                "This device cannot be subscribed to: it is missing one of "
                "the Product, Transport or Info services. Poll it instead."
            )

        if self._subscriptions:
            await self.unsubscribe()

        self._callback = callback
        self._translator = EventTranslator()
        event_handler = await self._ensure_event_handler()

        granted = []
        try:
            for service in self._evented_services():
                service.on_event = self._on_event
                sid, lease = await event_handler.async_subscribe(
                    service, timeout=timeout
                )
                self._subscriptions.append(sid)
                granted.append(lease)
        except UpnpError:
            # A caller whose subscribe() raised will not call unsubscribe().
            await self.unsubscribe()
            raise

        return min(granted)

    @_translates_errors
    async def renew(self, timeout=SUBSCRIBE_TIMEOUT):
        """Take out the subscriptions again before the device drops them.

        Returns the lease the device granted, as subscribe() does.

        Raises OpenhomeDeviceError when the device no longer recognises a
        subscription, which is how a device that restarted or gave up on an
        undeliverable event says so: nothing else announces it. Everything
        is released first, so is_subscribed is False by the time this
        raises and subscribe() is what picks the device back up.

        It is all or nothing. Half a subscription is worse than none, since
        some values would go stale while others kept arriving with no way to
        tell which.
        """
        if not self._subscriptions:
            raise OpenhomeDeviceError("This device is not subscribed to.")

        event_handler = self._active_event_handler
        pending = self._subscriptions
        # Emptied up front so is_subscribed is honest whichever way this goes.
        self._subscriptions = []

        renewed = []
        granted = []
        for position, sid in enumerate(pending):
            try:
                new_sid, lease = await event_handler.async_resubscribe(
                    sid, timeout=timeout
                )
            except (UpnpError, KeyError) as err:
                _LOGGER.debug("Could not renew subscription %s: %r", sid, err)
                await self._teardown(renewed + pending[position + 1 :])
                raise OpenhomeDeviceError(
                    f"The device no longer holds subscription {sid}"
                ) from err

            renewed.append(new_sid)
            granted.append(lease)

        self._subscriptions = renewed
        return min(granted)

    async def unsubscribe(self):
        """Stop receiving events. Never raises, and safe when not subscribed."""
        # Emptied before awaiting, so a renewal racing this cannot revive one.
        sids = self._subscriptions
        self._subscriptions = []

        await self._teardown(sids)

    async def _teardown(self, sids):
        """Separate from unsubscribe() because the renewal loop tears down
        too, and cannot call it: that awaits the task it runs on."""
        event_handler = self._active_event_handler
        if event_handler is not None:
            for sid in sids:
                try:
                    await event_handler.async_unsubscribe(sid)
                except (UpnpError, KeyError) as err:
                    _LOGGER.debug("Could not unsubscribe %s: %r", sid, err)

        for service in self._evented_services():
            service.on_event = None

        # Only a server we started is ours to stop.
        if self._notify_server is not None:
            await self._notify_server.async_stop_server()
            self._notify_server = None

        self._callback = None
        self._translator = None

    def _evented_services(self):
        candidates = (
            self.product_service,
            self.volume_service,
            self.transport_service,
            self.info_service,
        )
        return [service for service in candidates if service is not None]

    @property
    def _active_event_handler(self):
        if self._event_handler is not None:
            return self._event_handler
        if self._notify_server is not None:
            return self._notify_server.event_handler
        return None

    async def _ensure_event_handler(self):
        if self._event_handler is not None:
            return self._event_handler

        if self._notify_server is None:
            _, local_ip = await async_get_local_ip(self.location)
            # Port 0: a fixed one would stop a second device listening here.
            self._notify_server = AiohttpNotifyServer(
                requester=self.device.requester,
                source=(local_ip, 0),
            )
            await self._notify_server.async_start_server()
            _LOGGER.debug(
                "Listening for events from %s on %s",
                self.location,
                self._notify_server.callback_url,
            )

        return self._notify_server.event_handler

    def _on_event(self, service, state_variables):
        if self._callback is None or self._translator is None:
            return

        changes = self._translator.translate(service.service_id, state_variables)
        if changes:
            self._deliver(changes)

    def _deliver(self, changes):
        if self._callback is None:
            return

        try:
            result = self._callback(changes)
        except Exception:
            # The notify server may be shared, so one bad callback must not
            # bring down everything else subscribed through it.
            _LOGGER.exception("Error in openhomedevice event callback")
            return

        if inspect.isawaitable(result):
            task = asyncio.create_task(result)
            # asyncio only holds a weak reference, so keep one until it ends.
            self._callback_tasks.add(task)
            task.add_done_callback(self._callback_tasks.discard)

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

    async def _stream_capability(self, name):
        if self.transport_service is None:
            return None

        result = await self.transport_service.action("StreamInfo").async_call()
        return result.get(name)

    async def _mode_capability(self, name):
        if self.transport_service is None:
            return None

        result = await self.transport_service.action("ModeInfo").async_call()
        return result.get(name)

    @_translates_errors
    async def can_pause(self):
        return await self._stream_capability("CanPause")

    @_translates_errors
    async def can_skip_next(self):
        return await self._mode_capability("CanSkipNext")

    @_translates_errors
    async def can_skip_previous(self):
        return await self._mode_capability("CanSkipPrevious")

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
        return source_list.visible(source_list.parse(result["Value"]))

    @_translates_errors
    async def track_info(self):
        action = self.info_service.action("Track")
        result = await action.async_call()
        return didl_lite.parse(result["Metadata"])

    @property
    def pins_enabled(self):
        return self.pins_service is not None

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

        for source in source_list.parse(result["Value"]):
            if source["type"] == "Receiver":
                return source["index"]

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
