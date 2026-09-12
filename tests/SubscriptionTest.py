import asyncio
import os
import re
import unittest
from datetime import timedelta
from unittest import mock

from aioresponses import aioresponses
from async_upnp_client.exceptions import UpnpConnectionError, UpnpResponseError

from openhomedevice.device import Device
from openhomedevice.exceptions import OpenhomeConnectionError, OpenhomeDeviceError

LOCATION = "http://mydevice:12345/desc.xml"
LINN_BASE = "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp"
V1_BASE = LINN_BASE

# The state variables each service really events, taken from the service
# descriptions a Linn device serves. Only the ones this library maps are
# needed, plus one it does not, to prove the rest are dropped.
PRODUCT_VARIABLES = [
    ("Standby", "boolean"),
    ("SourceIndex", "ui4"),
    ("SourceCount", "ui4"),
    ("SourceXml", "string"),
    ("ProductRoom", "string"),
    ("ProductName", "string"),
]
VOLUME_VARIABLES = [("Volume", "ui4"), ("Mute", "boolean"), ("Balance", "i4")]
TRANSPORT_VARIABLES = [
    ("TransportState", "string"),
    ("CanPause", "boolean"),
    ("CanSeek", "boolean"),
    ("CanSkipNext", "boolean"),
    ("CanSkipPrevious", "boolean"),
]
INFO_VARIABLES = [("Metadata", "string"), ("Uri", "string")]

SOURCE_XML = (
    "<SourceList>"
    "<Source><Name>Playlist</Name><Type>Playlist</Type><Visible>true</Visible></Source>"
    "<Source><Name>Radio</Name><Type>Radio</Type><Visible>true</Visible></Source>"
    "</SourceList>"
)


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


def scpd(state_variables):
    """A service description declaring only the given state variables."""
    entries = "".join(
        f'<stateVariable sendEvents="yes">'
        f"<name>{name}</name><dataType>{data_type}</dataType>"
        f"</stateVariable>"
        for name, data_type in state_variables
    )
    return (
        '<scpd xmlns="urn:schemas-upnp-org:service-1-0">'
        f"<serviceStateTable>{entries}</serviceStateTable>"
        "</scpd>"
    )


def mock_device(mocked, description, services):
    """Serve a device description and the service descriptions behind it.

    services maps a service.xml path fragment to its state variables. Anything
    the description points at but services does not name gets an empty state
    table, because a device declares far more services than this library
    subscribes to and the factory fetches every one of them.
    """
    with open(os.path.join(os.path.dirname(__file__), "data", description)) as file:
        mocked.get(LOCATION, body=file.read())

    for fragment, state_variables in services.items():
        mocked.get(f"{V1_BASE}/{fragment}/service.xml", body=scpd(state_variables))

    mocked.get(re.compile(r".*/service\.xml$"), body=scpd([]), repeat=True)


LINN_SERVICES = {
    "av.openhome.org-Product-4": PRODUCT_VARIABLES,
    "av.openhome.org-Volume-4": VOLUME_VARIABLES,
    "av.openhome.org-Transport-1": TRANSPORT_VARIABLES,
    "av.openhome.org-Info-1": INFO_VARIABLES,
}


class FakeEventHandler:
    """Stands in for an async_upnp_client UpnpEventHandler.

    Records what was subscribed and unsubscribed so a test can check the
    device left nothing behind, and hands out predictable SIDs.
    """

    def __init__(self, timeout=timedelta(minutes=9)):
        self.subscribed = []
        self.unsubscribed = []
        self.resubscribed = []
        self.timeout = timeout
        self.fail_after = None
        self.resubscribe_error = None
        # The device answers, but no longer knows the subscription.
        self.forgotten = False
        self.subscribed_afresh = []
        self._sid_count = 0

    def _next_sid(self):
        self._sid_count += 1
        return f"uuid:subscription-{self._sid_count}"

    async def async_subscribe(self, service, timeout=None):
        if self.fail_after is not None and len(self.subscribed) >= self.fail_after:
            raise UpnpResponseError(status=500)
        self.subscribed.append(service)
        return self._next_sid(), self.timeout

    async def async_unsubscribe(self, sid):
        self.unsubscribed.append(sid)
        return sid

    async def async_resubscribe(self, sid, timeout=None):
        """Renew, or subscribe afresh where the device has forgotten the SID.

        As UpnpEventHandler does: a device that cannot be reached raises,
        and anything else it answers with, a refusal included, is followed
        by a full subscribe in place of the renewal.
        """
        if self.resubscribe_error is not None:
            raise self.resubscribe_error
        if self.forgotten:
            self.subscribed_afresh.append(sid)
            return self._next_sid(), self.timeout
        self.resubscribed.append(sid)
        return self._next_sid(), self.timeout

    @property
    def subscribed_service_ids(self):
        return [service.service_id for service in self.subscribed]


class Recorder:
    """Collects the change dicts handed to a subscription callback."""

    def __init__(self):
        self.changes = []

    def __call__(self, changes):
        self.changes.append(changes)

    @property
    def last(self):
        return self.changes[-1]


async def linn_device(event_handler=None):
    device = Device(LOCATION, event_handler=event_handler)
    await device.init()
    return device


class SubscribeTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def test_subscribes_to_product_volume_transport_and_info(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)

        await device.subscribe(Recorder())

        self.assertEqual(
            handler.subscribed_service_ids,
            [
                "urn:av-openhome-org:serviceId:Product",
                "urn:av-openhome-org:serviceId:Volume",
                "urn:av-openhome-org:serviceId:Transport",
                "urn:av-openhome-org:serviceId:Info",
            ],
        )
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_is_subscribed_tracks_the_subscription(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())

        self.assertFalse(device.is_subscribed)
        await device.subscribe(Recorder())
        self.assertTrue(device.is_subscribed)
        await device.unsubscribe()
        self.assertFalse(device.is_subscribed)

    @async_test
    @aioresponses()
    async def test_a_device_with_no_volume_still_subscribes_to_the_rest(self, mocked):
        """Volume control can be switched off, leaving no service to advertise."""
        mock_device(
            mocked,
            "novolumedevice.xml",
            {
                "av.openhome.org-Product-3": PRODUCT_VARIABLES,
                "av.openhome.org-Transport-1": TRANSPORT_VARIABLES,
                "av.openhome.org-Info-1": INFO_VARIABLES,
            },
        )
        handler = FakeEventHandler()
        device = await linn_device(handler)

        self.assertTrue(device.events_enabled)
        await device.subscribe(Recorder())

        self.assertEqual(
            handler.subscribed_service_ids,
            [
                "urn:av-openhome-org:serviceId:Product",
                "urn:av-openhome-org:serviceId:Transport",
                "urn:av-openhome-org:serviceId:Info",
            ],
        )
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_a_device_with_no_transport_service_cannot_event(self, mocked):
        """Transport state would be left behind, so nothing is offered."""
        mock_device(mocked, "v1description.xml", {})
        device = await linn_device(FakeEventHandler())
        self.assertFalse(device.events_enabled)

    @async_test
    @aioresponses()
    async def test_subscribing_to_a_device_that_cannot_event_is_refused(self, mocked):
        """Loudly, rather than quietly subscribing to only part of it."""
        mock_device(mocked, "v1description.xml", {})
        handler = FakeEventHandler()
        device = await linn_device(handler)

        with self.assertRaises(OpenhomeDeviceError):
            await device.subscribe(Recorder())

        self.assertFalse(device.is_subscribed)
        self.assertEqual(handler.subscribed, [])

    @async_test
    @aioresponses()
    async def test_a_full_device_can_event(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        self.assertTrue(device.events_enabled)

    @async_test
    @aioresponses()
    async def test_a_failure_part_way_through_leaves_nothing_subscribed(self, mocked):
        """A caller whose subscribe() raised will not call unsubscribe()."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        handler.fail_after = 2
        device = await linn_device(handler)

        with self.assertRaises(Exception):
            await device.subscribe(Recorder())

        self.assertFalse(device.is_subscribed)
        self.assertEqual(len(handler.unsubscribed), 2)

    @async_test
    @aioresponses()
    async def test_an_unreachable_device_raises_our_own_error(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        handler.fail_after = 0
        device = await linn_device(handler)

        async def refuse(service, timeout=None):
            raise UpnpConnectionError("no route to host")

        handler.async_subscribe = refuse

        with self.assertRaises(OpenhomeConnectionError):
            await device.subscribe(Recorder())

    @async_test
    @aioresponses()
    async def test_subscribing_twice_replaces_the_first_subscription(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)

        await device.subscribe(Recorder())
        second = Recorder()
        await device.subscribe(second)

        # The first four subscriptions were released before the next four.
        self.assertEqual(len(handler.unsubscribed), 4)
        self.assertEqual(len(handler.subscribed), 8)

        device.volume_service.notify_changed_state_variables({"Volume": "5"})
        self.assertEqual(second.last, {"volume": 5})
        await device.unsubscribe()


class EventDeliveryTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def test_a_change_reaches_the_callback_translated(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        recorder = Recorder()
        await device.subscribe(recorder)

        device.volume_service.notify_changed_state_variables(
            {"Volume": "42", "Mute": "1"}
        )

        self.assertEqual(recorder.last, {"volume": 42, "is_muted": True})
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_values_carry_the_types_the_polling_methods_return(self, mocked):
        """Volume is an int and standby a bool, exactly as the wire types say."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        recorder = Recorder()
        await device.subscribe(recorder)

        device.product_service.notify_changed_state_variables({"Standby": "0"})

        self.assertIs(recorder.last["is_in_standby"], False)
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_source_is_resolved_from_the_devices_own_variables(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        recorder = Recorder()
        await device.subscribe(recorder)

        device.product_service.notify_changed_state_variables(
            {"SourceXml": SOURCE_XML, "SourceIndex": "1"}
        )

        self.assertEqual(recorder.last["source"], {"type": "Radio", "name": "Radio"})
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_an_event_of_nothing_we_map_does_not_wake_the_caller(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        recorder = Recorder()
        await device.subscribe(recorder)

        device.volume_service.notify_changed_state_variables({"Balance": "3"})

        self.assertEqual(recorder.changes, [])
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_a_coroutine_callback_is_awaited(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        seen = []

        async def callback(changes):
            seen.append(changes)

        await device.subscribe(callback)
        device.volume_service.notify_changed_state_variables({"Volume": "7"})
        # The callback runs as its own task, so give the loop a turn.
        await asyncio.sleep(0)

        self.assertEqual(seen, [{"volume": 7}])
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_a_raising_callback_does_not_escape(self, mocked):
        """The notify server is shared, so one bad callback must not break it."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())

        def callback(changes):
            raise ValueError("callback is broken")

        await device.subscribe(callback)
        device.volume_service.notify_changed_state_variables({"Volume": "7"})

        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_no_events_are_delivered_after_unsubscribing(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        recorder = Recorder()
        await device.subscribe(recorder)
        await device.unsubscribe()

        device.volume_service.notify_changed_state_variables({"Volume": "42"})

        self.assertEqual(recorder.changes, [])


class UnsubscribeTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def test_every_subscription_is_released(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)

        await device.subscribe(Recorder())
        await device.unsubscribe()

        self.assertEqual(len(handler.unsubscribed), 4)

    @async_test
    @aioresponses()
    async def test_unsubscribing_when_not_subscribed_is_harmless(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_a_device_that_has_gone_away_does_not_raise(self, mocked):
        """Nothing a caller could do about it, and cleanup still has to finish."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)
        await device.subscribe(Recorder())

        async def refuse(sid):
            raise UpnpConnectionError("device has gone")

        handler.async_unsubscribe = refuse
        await device.unsubscribe()

        self.assertFalse(device.is_subscribed)

    @async_test
    @aioresponses()
    async def test_a_supplied_event_handler_is_left_alone(self, mocked):
        """The caller owns the notify server behind it, as with the session."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)

        await device.subscribe(Recorder())
        await device.unsubscribe()

        self.assertIsNone(device._notify_server)


class NotifyServerTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def test_a_server_is_started_when_none_was_supplied(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device()
        server = mock.MagicMock()
        server.async_start_server = mock.AsyncMock()
        server.async_stop_server = mock.AsyncMock()
        server.event_handler = FakeEventHandler()

        with mock.patch(
            "openhomedevice.device.AiohttpNotifyServer", return_value=server
        ) as notify_server, mock.patch(
            "openhomedevice.device.async_get_local_ip",
            mock.AsyncMock(return_value=(2, "192.168.1.10")),
        ):
            await device.subscribe(Recorder())

            server.async_start_server.assert_awaited_once()
            # Port 0, so a second device on this host can start one too.
            self.assertEqual(
                notify_server.call_args.kwargs["source"], ("192.168.1.10", 0)
            )

            await device.unsubscribe()
            server.async_stop_server.assert_awaited_once()

    @async_test
    @aioresponses()
    async def test_the_listener_is_bound_to_the_route_to_the_device(self, mocked):
        """A host with several interfaces must advertise the reachable one."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device()
        server = mock.MagicMock()
        server.async_start_server = mock.AsyncMock()
        server.async_stop_server = mock.AsyncMock()
        server.event_handler = FakeEventHandler()

        local_ip = mock.AsyncMock(return_value=(2, "192.168.1.10"))
        with mock.patch(
            "openhomedevice.device.AiohttpNotifyServer", return_value=server
        ), mock.patch("openhomedevice.device.async_get_local_ip", local_ip):
            await device.subscribe(Recorder())
            await device.unsubscribe()

        local_ip.assert_awaited_once_with(LOCATION)


class RenewTests(unittest.TestCase):
    """renew() is how a caller keeps a subscription, and the only way it
    finds out the device has stopped honouring one."""
    @async_test
    @aioresponses()
    async def test_every_subscription_is_renewed(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)
        await device.subscribe(Recorder())

        await device.renew()

        self.assertEqual(len(handler.resubscribed), 4)
        self.assertTrue(device.is_subscribed)
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_renewing_replaces_the_subscription_ids(self, mocked):
        """Unsubscribing later has to release the new SIDs, not the old ones."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)
        await device.subscribe(Recorder())
        original = set(device._subscriptions)

        await device.renew()
        renewed = set(device._subscriptions)

        self.assertEqual(renewed & original, set())

        await device.unsubscribe()
        self.assertEqual(set(handler.unsubscribed), renewed)

    @async_test
    @aioresponses()
    async def test_a_device_that_has_forgotten_us_is_subscribed_afresh(
        self, mocked
    ):
        """Renewing puts right what nothing reports.

        A device that restarted, or gave up on an event it could not
        deliver, says nothing and answers every other request as usual. It
        refuses the renewal, and a new subscription is taken out in place
        of the one it has forgotten.
        """
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        handler.forgotten = True
        device = await linn_device(handler)
        recorder = Recorder()
        await device.subscribe(recorder)
        original = set(device._subscriptions)

        lease = await device.renew()

        self.assertEqual(lease, handler.timeout)
        self.assertTrue(device.is_subscribed)
        self.assertEqual(len(handler.subscribed_afresh), 4)
        self.assertEqual(set(device._subscriptions) & original, set())
        # Nothing is pushed through the callback to say any of this happened.
        self.assertEqual(recorder.changes, [])
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_an_unreachable_device_makes_renewing_raise(self, mocked):
        """What a refusal is not: a device that cannot be reached at all."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        handler.resubscribe_error = UpnpConnectionError("device has gone")
        device = await linn_device(handler)
        recorder = Recorder()
        await device.subscribe(recorder)

        with self.assertRaises(OpenhomeDeviceError):
            await device.renew()

        self.assertFalse(device.is_subscribed)
        self.assertEqual(recorder.changes, [])
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_losing_one_subscription_releases_them_all(self, mocked):
        """Half a subscription is worse than none: some values would go stale."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)
        await device.subscribe(Recorder())

        # Let the first renewal through, then refuse the rest.
        original = handler.async_resubscribe

        async def fail_after_first(sid, timeout=None):
            handler.async_resubscribe = refuse
            return await original(sid, timeout=timeout)

        async def refuse(sid, timeout=None):
            raise UpnpConnectionError("device has gone")

        handler.async_resubscribe = fail_after_first
        with self.assertRaises(OpenhomeDeviceError):
            await device.renew()

        self.assertFalse(device.is_subscribed)
        # Nothing is left dangling on the device: the one that did renew, and
        # the two never reached, are all handed back.
        self.assertEqual(len(handler.unsubscribed), 3)

    @async_test
    @aioresponses()
    async def test_subscribing_again_recovers_a_lost_subscription(self, mocked):
        """Recovery is the caller's to trigger, so it has to work plainly.

        A device that is switched off is torn down at the next renewal. When
        it comes back the caller calls subscribe() again, with no unsubscribe
        first and nothing else to remember.
        """
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)
        await device.subscribe(Recorder())

        handler.resubscribe_error = UpnpConnectionError("powered off")
        with self.assertRaises(OpenhomeDeviceError):
            await device.renew()
        self.assertFalse(device.is_subscribed)

        handler.resubscribe_error = None
        recorder = Recorder()
        await device.subscribe(recorder)

        self.assertTrue(device.is_subscribed)
        device.volume_service.notify_changed_state_variables({"Volume": "33"})
        self.assertEqual(recorder.last, {"volume": 33})
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_no_events_follow_a_lost_subscription(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        handler.resubscribe_error = UpnpConnectionError("device has gone")
        device = await linn_device(handler)
        recorder = Recorder()
        await device.subscribe(recorder)
        service = device.volume_service

        with self.assertRaises(OpenhomeDeviceError):
            await device.renew()
        before = len(recorder.changes)
        service.notify_changed_state_variables({"Volume": "42"})

        self.assertEqual(len(recorder.changes), before)

    @async_test
    @aioresponses()
    async def test_the_lease_the_device_granted_is_handed_back(self, mocked):
        """The caller renews against it, so it has to come from the device.

        A device caps what it grants at its own maximum, which can be less
        than was asked for, and need not be the same on every service.
        """
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler(timeout=timedelta(minutes=9))
        device = await linn_device(handler)

        self.assertEqual(await device.subscribe(Recorder()), timedelta(minutes=9))

        handler.timeout = timedelta(minutes=4)
        self.assertEqual(await device.renew(), timedelta(minutes=4))
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_the_shortest_grant_is_the_one_reported(self, mocked):
        """Renewing after the shortest has expired would lose that service."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        device = await linn_device(handler)

        leases = iter(
            [timedelta(minutes=9), timedelta(minutes=2), timedelta(minutes=7)]
        )
        original = handler.async_subscribe

        async def varying(service, timeout=None):
            sid, _ = await original(service, timeout=timeout)
            return sid, next(leases, timedelta(minutes=9))

        handler.async_subscribe = varying

        self.assertEqual(await device.subscribe(Recorder()), timedelta(minutes=2))
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_the_lease_asked_for_is_the_callers_to_choose(self, mocked):
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler()
        asked = []
        original = handler.async_subscribe

        async def record(service, timeout=None):
            asked.append(timeout)
            return await original(service, timeout=timeout)

        handler.async_subscribe = record
        device = await linn_device(handler)

        await device.subscribe(Recorder(), timeout=timedelta(minutes=5))

        self.assertEqual(set(asked), {timedelta(minutes=5)})
        await device.unsubscribe()

    @async_test
    @aioresponses()
    async def test_renewing_without_a_subscription_is_refused(self, mocked):
        """There is nothing to renew, and subscribe() is what is wanted."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        device = await linn_device(FakeEventHandler())

        with self.assertRaises(OpenhomeDeviceError):
            await device.renew()

    @async_test
    @aioresponses()
    async def test_nothing_renews_on_its_own(self, mocked):
        """The schedule belongs to the caller: this library keeps no timers."""
        mock_device(mocked, "linndescription.xml", LINN_SERVICES)
        handler = FakeEventHandler(timeout=timedelta(seconds=1))
        device = await linn_device(handler)
        await device.subscribe(Recorder())

        await asyncio.sleep(0.05)

        self.assertEqual(handler.resubscribed, [])
        await device.unsubscribe()
