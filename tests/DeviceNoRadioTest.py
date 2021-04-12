import unittest
import os
import asyncio

from openhomedevice.Device import Device
from aioresponses import aioresponses


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


class DeviceWithNoRadioServiceTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/v1description.xml")
        ) as file:
            mocked.get(LOCATION, body=file.read())
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Product-1/service.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Volume-1/service.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Info-1/service.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Playlist-1/service.xml",
                body="",
            )
        self.sut = Device(LOCATION)
        await self.sut.init()
        soap_request_calls = []
        return super().setUp()

    @async_test
    async def test_play_media(self):
        track_details = {
            "uri": "https://host/uri.flac",
            "title": "TITLE",
            "albumArtwork": "https://host/uri.jpg",
        }
        await self.sut.play_media(track_details)
