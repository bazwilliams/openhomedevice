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

class DeviceWithVolume2ServiceTests(unittest.TestCase):

    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/v2description.xml")
        ) as file:
            mocked.get(
                LOCATION,
                body=file.read()
            )
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Product-2/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Volume-2/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Info-1/service.xml', body='')
        self.sut = Device(LOCATION)
        await self.sut.init()
        soap_request_calls = []
        return super().setUp()

    def test_volume_enabled(self):
        self.assertTrue(self.sut.volume_enabled)
