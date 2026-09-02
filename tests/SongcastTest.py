import unittest
import asyncio

from openhomedevice.device import Device


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


SENDER_METADATA = (
    '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" '
    'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">'
    '<item id="0" restricted="True">'
    "<dc:title>Linn Den Desk</dc:title>"
    '<res protocolInfo="ohz:*:*:u">'
    "ohz://239.255.255.250:51972/4c494e4e-0026-0f22-16cc-01429430013f"
    "</res>"
    "<upnp:class>object.item.audioItem</upnp:class>"
    "</item></DIDL-Lite>"
)

SENDER_URI = "ohz://239.255.255.250:51972/4c494e4e-0026-0f22-16cc-01429430013f"

SOURCE_XML = (
    "<SourceList>"
    "<Source><Name>Playlist</Name><Type>Playlist</Type>"
    "<Visible>true</Visible><SystemName>Playlist</SystemName></Source>"
    "<Source><Name>Radio</Name><Type>Radio</Type>"
    "<Visible>true</Visible><SystemName>Radio</SystemName></Source>"
    "<Source><Name>UPnP AV</Name><Type>UpnpAv</Type>"
    "<Visible>false</Visible><SystemName>UPnP AV</SystemName></Source>"
    "<Source><Name>Songcast</Name><Type>Receiver</Type>"
    "<Visible>false</Visible><SystemName>Songcast</SystemName></Source>"
    "</SourceList>"
)


class FakeAction:
    def __init__(self, response=None):
        self.was_called_times = 0
        self.arguments = None
        self.response = response

    async def async_call(self, **kwargs):
        self.arguments = kwargs
        self.was_called_times += 1
        return self.response


class FakeService:
    def __init__(self, actions):
        self.actions = actions

    def action(self, action_called):
        return self.actions[action_called]


def sender_actions(metadata=SENDER_METADATA, status="Enabled", audio=False):
    return {
        "Metadata": FakeAction({"Value": metadata}),
        "Status": FakeAction({"Value": status}),
        "Audio": FakeAction({"Value": audio}),
    }


def receiver_actions(uri=SENDER_URI, metadata=SENDER_METADATA, state="Playing"):
    return {
        "Sender": FakeAction({"Uri": uri, "Metadata": metadata}),
        "TransportState": FakeAction({"Value": state}),
        "SetSender": FakeAction(),
        "Play": FakeAction(),
        "Stop": FakeAction(),
    }


def product_actions(source_index=0):
    return {
        "SourceXml": FakeAction({"Value": SOURCE_XML}),
        "SourceIndex": FakeAction({"Value": source_index}),
        "SetSourceIndex": FakeAction(),
    }


class SongcastTests(unittest.TestCase):
    def setUp(self):
        self.sut = Device("http://mydevice:12345/desc.xml")
        self.sut.sender_service = FakeService(sender_actions())
        self.sut.receiver_service = FakeService(receiver_actions())
        self.sut.product_service = FakeService(product_actions())

    def test_capability_flags(self):
        self.assertTrue(self.sut.songcast_sender_enabled)
        self.assertTrue(self.sut.songcast_receiver_enabled)

    @async_test
    async def test_sender_status_and_audio(self):
        self.assertEqual(await self.sut.songcast_sender_status(), "Enabled")
        self.assertEqual(await self.sut.songcast_sender_audio(), False)

    @async_test
    async def test_sender_returns_uri_and_metadata(self):
        sender = await self.sut.songcast_sender()
        self.assertEqual(sender["uri"], SENDER_URI)
        self.assertEqual(sender["metadata"], SENDER_METADATA)

    @async_test
    async def test_sender_is_none_when_metadata_empty(self):
        self.sut.sender_service = FakeService(sender_actions(metadata=""))
        self.assertIsNone(await self.sut.songcast_sender())

    @async_test
    async def test_receiver_sender_when_following(self):
        following = await self.sut.songcast_receiver_sender()
        self.assertEqual(following["uri"], SENDER_URI)

    @async_test
    async def test_receiver_sender_is_none_when_not_following(self):
        self.sut.receiver_service = FakeService(receiver_actions(uri="", metadata=""))
        self.assertIsNone(await self.sut.songcast_receiver_sender())

    @async_test
    async def test_receiver_transport_state(self):
        self.assertEqual(await self.sut.songcast_receiver_transport_state(), "Playing")

    @async_test
    async def test_join_leaves_source_alone_when_firmware_switched_it(self):
        """Linn selects the Receiver source on Play, so do not set it again."""
        self.sut.product_service = FakeService(product_actions(source_index=3))

        await self.sut.songcast_receiver_join(
            {"uri": SENDER_URI, "metadata": SENDER_METADATA}
        )

        self.assertEqual(self.sut.receiver_service.actions["Play"].was_called_times, 1)
        self.assertIsNone(
            self.sut.product_service.actions["SetSourceIndex"].arguments
        )

    @async_test
    async def test_join_sets_sender_plays_and_selects_hidden_source(self):
        await self.sut.songcast_receiver_join(
            {"uri": SENDER_URI, "metadata": SENDER_METADATA}
        )

        set_sender = self.sut.receiver_service.actions["SetSender"]
        self.assertEqual(set_sender.arguments["Uri"], SENDER_URI)
        self.assertEqual(set_sender.arguments["Metadata"], SENDER_METADATA)
        self.assertEqual(self.sut.receiver_service.actions["Play"].was_called_times, 1)
        self.assertEqual(
            self.sut.product_service.actions["SetSourceIndex"].arguments["Value"], 3
        )

    @async_test
    async def test_leave_stops_and_clears_sender(self):
        await self.sut.songcast_receiver_leave()

        self.assertEqual(self.sut.receiver_service.actions["Stop"].was_called_times, 1)
        set_sender = self.sut.receiver_service.actions["SetSender"]
        self.assertEqual(set_sender.arguments["Uri"], "")
        self.assertEqual(set_sender.arguments["Metadata"], "")


class NoSongcastTests(unittest.TestCase):
    def setUp(self):
        self.sut = Device("http://mydevice:12345/desc.xml")
        self.sut.sender_service = None
        self.sut.receiver_service = None
        self.sut.product_service = FakeService(product_actions())

    def test_capability_flags(self):
        self.assertFalse(self.sut.songcast_sender_enabled)
        self.assertFalse(self.sut.songcast_receiver_enabled)

    @async_test
    async def test_reads_return_none(self):
        self.assertIsNone(await self.sut.songcast_sender())
        self.assertIsNone(await self.sut.songcast_sender_status())
        self.assertIsNone(await self.sut.songcast_sender_audio())
        self.assertIsNone(await self.sut.songcast_receiver_sender())
        self.assertIsNone(await self.sut.songcast_receiver_transport_state())

    @async_test
    async def test_join_and_leave_are_noops(self):
        await self.sut.songcast_receiver_join(
            {"uri": SENDER_URI, "metadata": SENDER_METADATA}
        )
        await self.sut.songcast_receiver_leave()
        self.assertIsNone(
            self.sut.product_service.actions["SetSourceIndex"].arguments
        )
