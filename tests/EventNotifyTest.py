"""End to end from a device's NOTIFY request to the caller's callback.

The other event tests stub the event handler out. These use the real one from
async_upnp_client, driven with the notification bodies a device actually
sends, so the XML parsing, the SID routing and the conversion of a state
variable from its wire format are all exercised rather than assumed.
"""

import os
import re
import unittest
from datetime import timedelta

from aioresponses import aioresponses
from async_upnp_client.const import HttpRequest, HttpResponse
from async_upnp_client.event_handler import UpnpEventHandler, UpnpNotifyServer
from async_upnp_client.utils import CaseInsensitiveDict

from openhomedevice.device import Device

LOCATION = "http://mydevice:12345/desc.xml"
BASE = "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp"
CALLBACK_URL = "http://192.168.1.99:41234/notify"

SERVICES = {
    "av.openhome.org-Product-4": [
        ("Standby", "boolean"),
        ("SourceIndex", "ui4"),
        ("SourceXml", "string"),
    ],
    "av.openhome.org-Volume-4": [("Volume", "ui4"), ("Mute", "boolean")],
    "av.openhome.org-Transport-1": [("TransportState", "string")],
    "av.openhome.org-Info-1": [("Metadata", "string")],
}


def scpd(state_variables):
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


def mock_device(mocked):
    with open(
        os.path.join(os.path.dirname(__file__), "data/linndescription.xml")
    ) as file:
        mocked.get(LOCATION, body=file.read())
    for fragment, state_variables in SERVICES.items():
        mocked.get(f"{BASE}/{fragment}/service.xml", body=scpd(state_variables))
    mocked.get(re.compile(r".*/service\.xml$"), body=scpd([]), repeat=True)


def notification(*properties):
    """The body a device sends when its state changes.

    properties are (name, value) pairs, rendered exactly as ohNet renders
    them: one e:property element each, values as unparsed text.
    """
    body = "".join(
        f"<e:property><{name}>{value}</{name}></e:property>"
        for name, value in properties
    )
    return (
        '<?xml version="1.0"?>'
        '<e:propertyset xmlns:e="urn:schemas-upnp-org:event-1-0">'
        f"{body}"
        "</e:propertyset>"
    )


class FakeRequester:
    """Answers SUBSCRIBE and UNSUBSCRIBE the way a device does.

    Headers come back case insensitively, as they would from aiohttp: a
    device answers with "SID" but async_upnp_client reads "sid".
    """

    def __init__(self, timeout=1800):
        self.timeout = timeout
        self.requests = []
        self._sid_count = 0

    async def async_http_request(self, request):
        self.requests.append(request)
        headers = {"TIMEOUT": f"Second-{self.timeout}"}
        if request.method == "SUBSCRIBE" and "SID" not in request.headers:
            self._sid_count += 1
            headers["SID"] = f"uuid:device-subscription-{self._sid_count}"
        return HttpResponse(200, CaseInsensitiveDict(headers), None)


class FakeNotifyServer(UpnpNotifyServer):
    """A notify server that never opens a socket, only names one."""

    @property
    def callback_url(self):
        return CALLBACK_URL

    async def async_start_server(self):
        pass

    async def async_stop_server(self):
        pass


class Recorder:
    def __init__(self):
        self.changes = []

    def __call__(self, changes):
        self.changes.append(changes)

    @property
    def last(self):
        return self.changes[-1]


class NotifyTests(unittest.IsolatedAsyncioTestCase):
    async def subscribed_device(self, mocked):
        mock_device(mocked)
        self.requester = FakeRequester()
        self.handler = UpnpEventHandler(FakeNotifyServer(), self.requester)
        device = Device(LOCATION, event_handler=self.handler)
        await device.init()
        self.recorder = Recorder()
        await device.subscribe(self.recorder)
        return device

    async def notify(self, service, *properties):
        """Deliver a notification for service, as the device would."""
        sid = self.handler.sid_for_service(service)
        request = HttpRequest(
            "NOTIFY",
            CALLBACK_URL,
            {"NT": "upnp:event", "NTS": "upnp:propchange", "SID": sid},
            notification(*properties),
        )
        return await self.handler.handle_notify(request)

    @aioresponses()
    async def test_a_volume_notification_reaches_the_callback(self, mocked):
        device = await self.subscribed_device(mocked)

        status = await self.notify(device.volume_service, ("Volume", "42"))

        self.assertEqual(status, 200)
        self.assertEqual(self.recorder.last, {"volume": 42})
        await device.unsubscribe()

    @aioresponses()
    async def test_wire_values_are_converted_to_python_types(self, mocked):
        """The device sends "1" and "0"; a caller should see True and False."""
        device = await self.subscribed_device(mocked)

        await self.notify(device.volume_service, ("Mute", "1"))
        self.assertIs(self.recorder.last["is_muted"], True)

        await self.notify(device.volume_service, ("Mute", "0"))
        self.assertIs(self.recorder.last["is_muted"], False)

        await device.unsubscribe()

    @aioresponses()
    async def test_a_transport_notification_reaches_the_callback(self, mocked):
        device = await self.subscribed_device(mocked)

        await self.notify(device.transport_service, ("TransportState", "Playing"))

        self.assertEqual(self.recorder.last, {"transport_state": "Playing"})
        await device.unsubscribe()

    @aioresponses()
    async def test_a_full_product_notification_resolves_the_source(self, mocked):
        """The first notification after subscribing carries the whole state."""
        device = await self.subscribed_device(mocked)

        source_xml = (
            "&lt;SourceList&gt;"
            "&lt;Source&gt;&lt;Name&gt;Playlist&lt;/Name&gt;"
            "&lt;Type&gt;Playlist&lt;/Type&gt;&lt;Visible&gt;true&lt;/Visible&gt;"
            "&lt;/Source&gt;"
            "&lt;Source&gt;&lt;Name&gt;Radio&lt;/Name&gt;"
            "&lt;Type&gt;Radio&lt;/Type&gt;&lt;Visible&gt;true&lt;/Visible&gt;"
            "&lt;/Source&gt;"
            "&lt;/SourceList&gt;"
        )
        await self.notify(
            device.product_service,
            ("Standby", "0"),
            ("SourceIndex", "1"),
            ("SourceXml", source_xml),
        )

        self.assertEqual(
            self.recorder.last,
            {
                "is_in_standby": False,
                "sources": [
                    {"index": 0, "name": "Playlist", "type": "Playlist"},
                    {"index": 1, "name": "Radio", "type": "Radio"},
                ],
                "source": {"type": "Radio", "name": "Radio"},
            },
        )
        await device.unsubscribe()

    @aioresponses()
    async def test_track_metadata_reaches_the_callback_parsed(self, mocked):
        device = await self.subscribed_device(mocked)

        metadata = (
            "&lt;DIDL-Lite "
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" '
            'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"&gt;'
            "&lt;item&gt;&lt;dc:title&gt;Echoes&lt;/dc:title&gt;"
            "&lt;upnp:artist&gt;Pink Floyd&lt;/upnp:artist&gt;"
            "&lt;/item&gt;&lt;/DIDL-Lite&gt;"
        )
        await self.notify(device.info_service, ("Metadata", metadata))

        track_info = self.recorder.last["track_info"]
        self.assertEqual(track_info["title"], "Echoes")
        self.assertEqual(track_info["artist"], ["Pink Floyd"])
        await device.unsubscribe()

    @aioresponses()
    async def test_a_notification_for_an_unknown_sid_is_not_delivered(self, mocked):
        """A shared notify server sees traffic for devices that are not ours."""
        device = await self.subscribed_device(mocked)

        request = HttpRequest(
            "NOTIFY",
            CALLBACK_URL,
            {"NT": "upnp:event", "NTS": "upnp:propchange", "SID": "uuid:not-ours"},
            notification(("Volume", "42")),
        )
        await self.handler.handle_notify(request)

        self.assertEqual(self.recorder.changes, [])
        await device.unsubscribe()

    @aioresponses()
    async def test_nothing_is_delivered_after_unsubscribing(self, mocked):
        device = await self.subscribed_device(mocked)
        service = device.volume_service
        sid = self.handler.sid_for_service(service)
        await device.unsubscribe()

        request = HttpRequest(
            "NOTIFY",
            CALLBACK_URL,
            {"NT": "upnp:event", "NTS": "upnp:propchange", "SID": sid},
            notification(("Volume", "42")),
        )
        await self.handler.handle_notify(request)

        self.assertEqual(self.recorder.changes, [])

    @aioresponses()
    async def test_the_device_is_asked_for_the_timeout_we_want(self, mocked):
        """Half an hour, since the device grants whatever it is asked for."""
        device = await self.subscribed_device(mocked)

        subscribes = [r for r in self.requester.requests if r.method == "SUBSCRIBE"]
        self.assertEqual(len(subscribes), 4)
        for request in subscribes:
            self.assertEqual(request.headers["TIMEOUT"], "Second-1800")
            self.assertEqual(request.headers["CALLBACK"], f"<{CALLBACK_URL}>")

        await device.unsubscribe()

    @aioresponses()
    async def test_unsubscribing_releases_every_sid_at_the_device(self, mocked):
        device = await self.subscribed_device(mocked)

        await device.unsubscribe()

        unsubscribes = [r for r in self.requester.requests if r.method == "UNSUBSCRIBE"]
        self.assertEqual(len(unsubscribes), 4)


class RenewalTests(unittest.IsolatedAsyncioTestCase):
    @aioresponses()
    async def test_a_renewal_keeps_events_flowing(self, mocked):
        """After renewing, the new SID must route to the caller just as before."""
        mock_device(mocked)
        requester = FakeRequester()
        handler = UpnpEventHandler(FakeNotifyServer(), requester)
        device = Device(LOCATION, event_handler=handler)
        await device.init()
        recorder = Recorder()
        await device.subscribe(recorder)

        await device.renew()

        sid = handler.sid_for_service(device.volume_service)
        request = HttpRequest(
            "NOTIFY",
            CALLBACK_URL,
            {"NT": "upnp:event", "NTS": "upnp:propchange", "SID": sid},
            notification(("Volume", "11")),
        )
        await handler.handle_notify(request)

        self.assertEqual(recorder.last, {"volume": 11})
        await device.unsubscribe()

    @aioresponses()
    async def test_a_short_grant_is_reported_as_the_device_gave_it(self, mocked):
        """A device may grant far less than the half hour it was asked for.

        The caller renews against what came back, so a grant read wrongly
        here would have it renew too late and lose the subscription.
        """
        mock_device(mocked)
        requester = FakeRequester(timeout=60)
        handler = UpnpEventHandler(FakeNotifyServer(), requester)
        device = Device(LOCATION, event_handler=handler)
        await device.init()

        granted = await device.subscribe(Recorder())

        self.assertEqual(granted, timedelta(seconds=60))
        await device.unsubscribe()
