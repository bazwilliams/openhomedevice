import unittest
import os
import asyncio

from openhomedevice.device import Device
from aioresponses import aioresponses
from openhomedevice.didl_lite import generate_string

def escape(str):
    str = str.replace("&", "&amp;")
    return str

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


def pins_actions():
    return {
        "GetDeviceMax": FakeAction({"DeviceMax": 6}),
        "GetIdArray": FakeAction(
            {"IdArray": "[1,2,0,3,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]"}
        ),
        "ReadList": FakeAction(
            {
                "List": '[{"id":1,"mode":"transport","type":"source","uri":"transport:\\/\\/source?udn=4c494e4e-0026-0f22-2963-01387403013f&id=HDMI2&version=1","title":"Sky","description":"","artworkUri":"external:///source?type=Hdmi&systemName=HDMI2","shuffle":false},{"id":2,"mode":"transport","type":"source","uri":"transport:\\/\\/source?udn=4c494e4e-0026-0f22-2963-01387403013f&id=HDMI1&version=1","title":"Playstation 4","description":"","artworkUri":"external:///source?type=Hdmi&systemName=HDMI1","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":3,"mode":"transport","type":"source","uri":"transport:\\/\\/source?udn=4c494e4e-0026-0f22-2963-01387403013f&id=HDMI3&version=1","title":"Fire Stick","description":"","artworkUri":"external:///source?type=Hdmi&systemName=HDMI3","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":4,"mode":"transport","type":"source","uri":"transport:\\/\\/source?udn=4c494e4e-0026-0f22-2963-01387403013f&id=Balanced&version=1","title":"LP12","description":"","artworkUri":"external:///source?type=Analog&systemName=Balanced","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false},{"id":0,"mode":"","type":"","uri":"","title":"","description":"","artworkUri":"","shuffle":false}]'
            }
        ),
        "InvokeIndex": FakeAction(),
    }

def firmware_actions():
    return {
        "GetSoftwareStatus": FakeAction({ "SoftwareStatus": '{"status": "on_latest", "current_software": {"version": "4.100.502", "topic": "main", "channel": "release"}}'}),
        "CheckNow": FakeAction(),
        "Apply": FakeAction()
    }


def info_actions():
    return {
        "Track": FakeAction(
            {
                "Uri": "uri=scd://192.168.1.38:38921",
                "Metadata": escape('<?xml version="1.0" encoding="UTF-8"?><DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item parentID="-1" restricted="1"><upnp:albumArtURI xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">http://192.168.1.38:9100/api/image/cc7cbb0b22dd07348d535f1c0db8278a?scale=fit&width=512&height=512&format=image%2Fpng</upnp:albumArtURI><upnp:artist xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Beastie Boys</upnp:artist><upnp:artist xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Beastie Boys</upnp:artist><upnp:artist role="AlbumArtist" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Beastie Boys</upnp:artist><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Alternative Pop/Rock</upnp:genre><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Alternative Rap</upnp:genre><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Alternative/Indie Rock</upnp:genre><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Pop/Rock</upnp:genre><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Rap</upnp:genre><upnp:album xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Ill Communication</upnp:album><upnp:artist role="composer" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Adam Yauch</upnp:artist><upnp:artist role="composer" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Mike D</upnp:artist><upnp:artist role="composer" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Ad-Rock</upnp:artist><dc:date xmlns:dc="http://purl.org/dc/elements/1.1/">2009</dc:date><dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Sabotage</dc:title><oh:originalDiscNumber xmlns:oh="http://www.openhome.org">1</oh:originalDiscNumber><upnp:originalTrackNumber xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">6</upnp:originalTrackNumber><res duration="0:02:58.000">uri=scd://192.168.1.38:38921</res><upnp:class xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">track</upnp:class></item></DIDL-Lite>'),
            }
        )
    }


def volume_actions():
    return {
        "Volume": FakeAction({"Value": 11}),
        "Mute": FakeAction({"Value": True}),
        "SetVolume": FakeAction(),
        "VolumeInc": FakeAction(),
        "VolumeDec": FakeAction(),
        "SetMute": FakeAction(),
    }


def radio_actions():
    return {"SetChannel": FakeAction(), "Play": FakeAction()}


def transport_actions():
    return {
        "TransportState": FakeAction({"State": "Playing"}),
        "Play": FakeAction(),
        "Pause": FakeAction(),
        "Stop": FakeAction(),
        "SkipNext": FakeAction(),
        "SkipPrevious": FakeAction(),
    }


def product_actions():
    return {
        "Product": FakeAction({"Name": b"My Friendly Name", "Room": b"Bathroom"}),
        "SetStandby": FakeAction(),
        "Standby": FakeAction({"Value": True}),
        "SourceIndex": FakeAction({"Value": 3}),
        "Source": FakeAction({"Type": "Analog", "Name": "Front Aux"}),
        "SetSourceIndex": FakeAction(),
        "SourceXml": FakeAction(
            {
                "Value": "<SourceList><Source><Name>Playlist</Name><Type>Playlist</Type><Visible>true</Visible><SystemName>Playlist</SystemName></Source><Source><Name>Radio</Name><Type>Radio</Type><Visible>false</Visible><SystemName>Radio</SystemName></Source><Source><Name>UPnP AV</Name><Type>UpnpAv</Type><Visible>false</Visible><SystemName>UPnP AV</SystemName></Source><Source><Name>Songcast</Name><Type>Receiver</Type><Visible>false</Visible><SystemName>Songcast</SystemName></Source><Source><Name>Net Aux</Name><Type>NetAux</Type><Visible>false</Visible><SystemName>Net Aux</SystemName></Source><Source><Name>Spotify</Name><Type>Spotify</Type><Visible>false</Visible><SystemName>Spotify</SystemName></Source><Source><Name>Roon</Name><Type>Scd</Type><Visible>true</Visible><SystemName>Roon</SystemName></Source><Source><Name>SpeakerTest</Name><Type>Private</Type><Visible>false</Visible><SystemName>SpeakerTest</SystemName></Source></SourceList>"
            }
        ),
    }


class FakeService:
    def __init__(self, actions):
        self.actions = actions

    def action(self, action_called):
        return self.actions[action_called]


class LinnDeviceTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/linndescription.xml")
        ) as file:
            mocked.get(LOCATION, body=file.read())
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-ConfigApp-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Product-4/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Volume-4/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Credentials-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-OAuth-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Time-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Info-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Config-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Transport-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Pins-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Diagnostics-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Volkano-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Privacy-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Exakt-5/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Configuration-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Exakt2-4/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Update-3/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Cloud-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Playlist-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Radio-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Receiver-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Sender-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-LipSync-1/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Debug-2/service.xml",
                body="<scpd xmlns=\"urn:schemas-upnp-org:service-1-0\"><serviceStateTable/></scpd>",
            )
        self.sut = Device(LOCATION)
        await self.sut.init()
        soap_request_calls = []
        return super().setUp()

    def test_device_parses_uuid(self):
        self.assertEqual(self.sut.uuid(), "uuid:4c494e4e-1234-ab12-abcd-01234567819f")

    def test_device_parses_model_name(self):
        self.assertEqual(self.sut.model_name(), "My Model")

    def test_device_parses_manufacturer(self):
        self.assertEqual(self.sut.manufacturer(), "Leading Technology Firm")

    def test_device_parses_friendly_name(self):
        self.assertEqual(self.sut.friendly_name(), "Music Machine")

    @async_test
    async def test_device_name(self):
        self.sut.product_service = FakeService(product_actions())
        self.assertEqual(await self.sut.name(), b"My Friendly Name")

    @async_test
    async def test_device_room(self):
        self.sut.product_service = FakeService(product_actions())
        self.assertEqual(await self.sut.room(), b"Bathroom")

    @async_test
    async def test_set_standby_off(self):
        self.sut.product_service = FakeService(product_actions())
        await self.sut.set_standby(False)
        self.assertFalse(
            self.sut.product_service.actions["SetStandby"].arguments["Value"]
        )

    @async_test
    async def test_set_standby_on(self):
        self.sut.product_service = FakeService(product_actions())
        await self.sut.set_standby(True)
        self.assertTrue(
            self.sut.product_service.actions["SetStandby"].arguments["Value"]
        )

    @async_test
    async def test_is_in_standby(self):
        self.sut.product_service = FakeService(product_actions())
        self.assertEqual(await self.sut.is_in_standby(), True)

    @async_test
    async def test_transport_state(self):
        self.sut.transport_service = FakeService(transport_actions())
        self.assertEqual(await self.sut.transport_state(), "Playing")

    @async_test
    async def test_play(self):
        self.sut.transport_service = FakeService(transport_actions())
        await self.sut.play()
        self.assertEqual(self.sut.transport_service.actions["Play"].was_called_times, 1)

    @async_test
    async def test_play_media_with_nothing(self):
        self.sut.radio_service = FakeService(radio_actions())
        await self.sut.play_media(None)
        self.assertEqual(
            self.sut.radio_service.actions["SetChannel"].was_called_times, 0
        )
        self.assertEqual(self.sut.radio_service.actions["Play"].was_called_times, 0)

    @async_test
    async def test_play_media_invalid_url(self):
        self.sut.radio_service = FakeService(radio_actions())
        track_details = {"title": "TITLE", "albumArtwork": "https://host/uri.jpg"}
        await self.sut.play_media(track_details)
        self.assertEqual(
            self.sut.radio_service.actions["SetChannel"].arguments["Uri"], ""
        )
        self.assertEqual(
            self.sut.radio_service.actions["SetChannel"].arguments["Metadata"],
            generate_string(track_details),
        )
        self.assertEqual(self.sut.radio_service.actions["Play"].was_called_times, 1)

    @async_test
    async def test_play_media(self):
        self.sut.radio_service = FakeService(radio_actions())
        track_details = {
            "uri": "https://host/uri.flac",
            "title": "TITLE",
            "albumArtwork": "https://host/uri.jpg",
        }
        await self.sut.play_media(track_details)
        self.assertEqual(
            self.sut.radio_service.actions["SetChannel"].arguments["Uri"],
            "https://host/uri.flac",
        )
        self.assertEqual(
            self.sut.radio_service.actions["SetChannel"].arguments["Metadata"],
            generate_string(track_details),
        )
        self.assertEqual(self.sut.radio_service.actions["Play"].was_called_times, 1)

    @async_test
    async def test_stop(self):
        self.sut.transport_service = FakeService(transport_actions())
        await self.sut.stop()
        self.assertEqual(self.sut.transport_service.actions["Stop"].was_called_times, 1)

    @async_test
    async def test_pause(self):
        self.sut.transport_service = FakeService(transport_actions())
        await self.sut.pause()
        self.assertEqual(
            self.sut.transport_service.actions["Pause"].was_called_times, 1
        )

    @async_test
    async def test_skip_forward(self):
        self.sut.transport_service = FakeService(transport_actions())
        await self.sut.skip(10)
        self.assertEqual(
            self.sut.transport_service.actions["SkipNext"].was_called_times, 10
        )

    @async_test
    async def test_skip_backwards(self):
        self.sut.transport_service = FakeService(transport_actions())
        await self.sut.skip(-10)
        self.assertEqual(
            self.sut.transport_service.actions["SkipPrevious"].was_called_times, 10
        )

    @async_test
    async def test_skip_nowhere(self):
        self.sut.transport_service = FakeService(transport_actions())
        await self.sut.skip(0)
        self.assertEqual(
            self.sut.transport_service.actions["SkipPrevious"].was_called_times, 0
        )
        self.assertEqual(
            self.sut.transport_service.actions["SkipNext"].was_called_times, 0
        )

    @async_test
    async def test_source(self):
        self.sut.product_service = FakeService(product_actions())
        self.assertEqual(
            await self.sut.source(), {"type": "Analog", "name": "Front Aux"}
        )
        self.assertEqual(
            self.sut.product_service.actions["Source"].arguments["Index"], 3
        )

    def test_volume_enabled(self):
        self.assertTrue(self.sut.volume_enabled)

    @async_test
    async def test_volume_level(self):
        self.sut.volume_service = FakeService(volume_actions())
        self.assertEqual(await self.sut.volume(), 11)

    @async_test
    async def test_volume_muted(self):
        self.sut.volume_service = FakeService(volume_actions())
        self.assertTrue(await self.sut.is_muted())

    @async_test
    async def test_set_volume(self):
        self.sut.volume_service = FakeService(volume_actions())
        await self.sut.set_volume(11)
        self.assertEqual(
            self.sut.volume_service.actions["SetVolume"].arguments["Value"], 11
        )

    @async_test
    async def test_increase_volume(self):
        self.sut.volume_service = FakeService(volume_actions())
        await self.sut.increase_volume()
        self.assertEqual(
            self.sut.volume_service.actions["VolumeInc"].was_called_times, 1
        )

    @async_test
    async def test_decrease_volume(self):
        self.sut.volume_service = FakeService(volume_actions())
        await self.sut.decrease_volume()
        self.assertEqual(
            self.sut.volume_service.actions["VolumeDec"].was_called_times, 1
        )

    @async_test
    async def test_set_mute(self):
        self.sut.volume_service = FakeService(volume_actions())
        await self.sut.set_mute(True)
        self.assertTrue(self.sut.volume_service.actions["SetMute"].arguments["Value"])

    @async_test
    async def test_set_source(self):
        self.sut.product_service = FakeService(product_actions())
        await self.sut.set_source(4)
        self.assertEqual(
            self.sut.product_service.actions["SetSourceIndex"].arguments["Value"], 4
        )

    @async_test
    async def test_sources(self):
        self.sut.product_service = FakeService(product_actions())
        self.assertEqual(
            await self.sut.sources(),
            [
                {"index": 0, "name": "Playlist", "type": "Playlist"},
                {"index": 6, "name": "Roon", "type": "Scd"},
            ],
        )

    @async_test
    async def test_track_info(self):
        self.sut.info_service = FakeService(info_actions())
        self.assertEqual(
            await self.sut.track_info(),
            {
                "type": "track",
                "title": "Sabotage",
                "uri": "uri=scd://192.168.1.38:38921",
                "artist": ["Beastie Boys", "Adam Yauch", "Mike D", "Ad-Rock"],
                "composer": [],
                "narrator": [],
                "performer": [],
                "conductor": [],
                "albumArtist": ["Beastie Boys"],
                "genre": [
                    "Alternative Pop/Rock",
                    "Alternative Rap",
                    "Alternative/Indie Rock",
                    "Pop/Rock",
                    "Rap",
                ],
                "albumGenre": [
                    "Alternative Pop/Rock",
                    "Alternative Rap",
                    "Alternative/Indie Rock",
                    "Pop/Rock",
                    "Rap",
                ],
                "albumTitle": "Ill Communication",
                "albumArtwork": "http://192.168.1.38:9100/api/image/cc7cbb0b22dd07348d535f1c0db8278a?scale=fit&width=512&height=512&format=image%2Fpng",
                "artwork": None,
                "year": 2009,
                "disc": None,
                "discs": None,
                "track": 6,
                "tracks": None,
                "author": [],
                "publisher": None,
                "published": None,
                "description": None,
                "rating": None,
                "channels": None,
                "bitDepth": None,
                "sampleRate": None,
                "bitRate": None,
                "duration": 178,
                "mimeType": None,
            },
        )

    @async_test
    async def test_pins(self):
        self.sut.pins_service = FakeService(pins_actions())
        self.assertListEqual(
            await self.sut.pins(),
            [
                {
                    "index": 1,
                    "title": "Sky",
                    "artworkUri": "external:///source?type=Hdmi&systemName=HDMI2",
                },
                {
                    "index": 2,
                    "title": "Playstation 4",
                    "artworkUri": "external:///source?type=Hdmi&systemName=HDMI1",
                },
                {
                    "index": 4,
                    "title": "Fire Stick",
                    "artworkUri": "external:///source?type=Hdmi&systemName=HDMI3",
                },
                {
                    "index": 6,
                    "title": "LP12",
                    "artworkUri": "external:///source?type=Analog&systemName=Balanced",
                },
            ],
        )
        self.assertEqual(
            self.sut.pins_service.actions["ReadList"].arguments["Ids"],
            "[1, 2, 0, 3, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]",
        )

    @async_test
    async def test_invoke_pin(self):
        self.sut.pins_service = FakeService(pins_actions())
        await self.sut.invoke_pin(42)
        self.assertEqual(
            self.sut.pins_service.actions["InvokeIndex"].arguments["Index"], 41
        )
    
    @async_test
    async def test_check_software(self):
        self.sut.update_service = FakeService(firmware_actions())
        result = await self.sut.software_status()
        self.assertEqual(result["status"], "on_latest")
        self.assertEqual(result["current_software"]["version"], "4.100.502")

    @async_test
    async def test_check_latest_firmware(self):
        self.sut.update_service = FakeService(firmware_actions())
        await self.sut.check_latest_firmware()
        self.assertEqual(
            self.sut.update_service.actions["CheckNow"].was_called_times, 1)

    @async_test
    async def test_check_latest_firmware(self):
        self.sut.update_service = FakeService(firmware_actions())
        await self.sut.update_firmware()
        self.assertEqual(
            self.sut.update_service.actions["Apply"].was_called_times, 1)

