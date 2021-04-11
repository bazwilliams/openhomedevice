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


class DidlLiteTests(unittest.TestCase):
    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/softwaredescription.xml")
        ) as file:
            mocked.get(LOCATION, body=file.read())
            mocked.get(
                "http://mydevice:12345/dev/509a3dc9-d32b-30a1-ffff-ffff8842af55/svc/av-openhome-org/Product/desc.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/dev/509a3dc9-d32b-30a1-ffff-ffff8842af55/svc/av-openhome-org/Volume/desc.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/dev/509a3dc9-d32b-30a1-ffff-ffff8842af55/svc/av-openhome-org/Time/desc.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/dev/509a3dc9-d32b-30a1-ffff-ffff8842af55/svc/av-openhome-org/Info/desc.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/dev/509a3dc9-d32b-30a1-ffff-ffff8842af55/svc/av-openhome-org/Playlist/desc.xml",
                body="",
            )
            mocked.get(
                "http://mydevice:12345/dev/509a3dc9-d32b-30a1-ffff-ffff8842af55/svc/av-openhome-org/Credentials/desc.xml",
                body="",
            )
        self.sut = Device(LOCATION)
        await self.sut.init()
        soap_request_calls = []
        return super().setUp()

    def test_device_parses_uuid(self):
        self.assertEqual(self.sut.uuid(), "uuid:509a3dc9-d32b-30a1-ffff-ffff8842af55")

    @async_test
    async def test_skip_forward(self):
        await self.sut.skip(1)
        # self.assertEqual(transport_actions['SkipNext'].was_called_times, 1)

    @async_test
    async def test_skip_backwards(self):
        await self.sut.skip(-1)
        # self.assertEqual(transport_actions['SkipPrevious'].was_called_times, 1)

    @async_test
    async def test_stop(self):
        await self.sut.stop()
        # self.assertTrue(transport_actions["Stop"].was_called)

    @async_test
    async def test_pause(self):
        await self.sut.pause()
        # self.assertTrue(transport_actions["Pause"].was_called)
