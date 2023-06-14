import unittest
import os
import asyncio

from openhomedevice.device import Device
from aioresponses import aioresponses


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


class FakeAction:
    def __init__(self, response=None):
        self.was_called_times = 0
        self.response = response

    async def async_call(self, **kwargs):
        self.arguments = kwargs
        self.was_called_times += 1
        return self.response


def product_actions():
    return {
        "Product": FakeAction({"Name": b"My Friendly Name", "Room": b"Bathroom"}),
        "SetStandby": FakeAction(),
        "Standby": FakeAction({"Value": True}),
        "SourceIndex": FakeAction({"Value": 3}),
        "Source": FakeAction({"Type": "Radio", "Name": "Radio"}),
        "SetSourceIndex": FakeAction(),
        "SourceXml": FakeAction(
            {
                "Value": "<SourceList><Source><Name>Playlist</Name><Type>Playlist</Type><Visible>true</Visible><SystemName>Playlist</SystemName></Source><Source><Name>Radio</Name><Type>Radio</Type><Visible>false</Visible><SystemName>Radio</SystemName></Source><Source><Name>UPnP AV</Name><Type>UpnpAv</Type><Visible>false</Visible><SystemName>UPnP AV</SystemName></Source><Source><Name>Songcast</Name><Type>Receiver</Type><Visible>false</Visible><SystemName>Songcast</SystemName></Source><Source><Name>Net Aux</Name><Type>NetAux</Type><Visible>false</Visible><SystemName>Net Aux</SystemName></Source><Source><Name>Spotify</Name><Type>Spotify</Type><Visible>false</Visible><SystemName>Spotify</SystemName></Source><Source><Name>Roon</Name><Type>Scd</Type><Visible>true</Visible><SystemName>Roon</SystemName></Source><Source><Name>SpeakerTest</Name><Type>Private</Type><Visible>false</Visible><SystemName>SpeakerTest</SystemName></Source></SourceList>"
            }
        ),
    }


def playlist_actions():
    return {
        "TransportState": FakeAction({"Value": "Playing"}),
        "Play": FakeAction(),
        "Pause": FakeAction(),
        "Stop": FakeAction(),
        "Next": FakeAction(),
        "Previous": FakeAction(),
    }


def radio_actions():
    return {
        "TransportState": FakeAction({"Value": "Playing"}),
        "Play": FakeAction(),
        "Pause": FakeAction(),
        "Stop": FakeAction(),
    }


class FakeService:
    def __init__(self, actions):
        self.actions = actions

    def action(self, action_called):
        return self.actions[action_called]


class OpenhomeDevicePlaylistTest(unittest.TestCase):
    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/softwaredescription.xml")
        ) as file:
            mocked.get(LOCATION, body=file.read())
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Product-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Volume-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Credentials-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Time-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Info-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Config-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Playlist-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Receiver-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Sender-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/softplayer.local/Upnp/av.openhome.org-Radio-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
        self.sut = Device(LOCATION)
        await self.sut.init()
        soap_request_calls = []
        return super().setUp()

    def test_device_parses_uuid(self):
        self.assertEqual(self.sut.uuid(), "uuid:softplayer.local")

    @async_test
    async def test_transport_state(self):
        self.sut.product_service = FakeService(product_actions())
        self.sut.playlist_service = FakeService(playlist_actions())
        self.sut.radio_service = FakeService(radio_actions())
        self.assertEqual(await self.sut.transport_state(), "Playing")

    @async_test
    async def test_play(self):
        self.sut.product_service = FakeService(product_actions())
        self.sut.playlist_service = FakeService(playlist_actions())
        self.sut.radio_service = FakeService(radio_actions())
        await self.sut.play()
        self.assertEqual(self.sut.radio_service.actions["Play"].was_called_times, 1)

    @async_test
    async def test_stop(self):
        self.sut.product_service = FakeService(product_actions())
        self.sut.playlist_service = FakeService(playlist_actions())
        self.sut.radio_service = FakeService(radio_actions())
        await self.sut.stop()
        self.assertEqual(self.sut.radio_service.actions["Stop"].was_called_times, 1)

    @async_test
    async def test_pause(self):
        self.sut.product_service = FakeService(product_actions())
        self.sut.playlist_service = FakeService(playlist_actions())
        self.sut.radio_service = FakeService(radio_actions())
        await self.sut.pause()
        self.assertEqual(self.sut.radio_service.actions["Pause"].was_called_times, 1)

    @async_test
    async def test_skip_forward_does_nothing(self):
        self.sut.product_service = FakeService(product_actions())
        self.sut.playlist_service = FakeService(playlist_actions())
        await self.sut.skip(10)
        self.assertEqual(self.sut.playlist_service.actions["Next"].was_called_times, 0)

    @async_test
    async def test_skip_backwards_does_nothing(self):
        self.sut.product_service = FakeService(product_actions())
        self.sut.playlist_service = FakeService(playlist_actions())
        self.sut.radio_service = FakeService(radio_actions())
        await self.sut.skip(-10)
        self.assertEqual(
            self.sut.playlist_service.actions["Previous"].was_called_times, 0
        )
