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


class DeviceWithNoVolumeTests(unittest.TestCase):

    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/novolumedevice.xml")
        ) as file:
            mocked.get(
                LOCATION,
                body=file.read()
            )
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-ConfigApp-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Product-3/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Volume-4/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Credentials-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Time-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Info-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Config-2/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Transport-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Pins-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Update-2/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Diagnostics-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Volkano-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Privacy-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Exakt-4/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Configuration-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Exakt2-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-ExaktInputs-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-Cloud-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Playlist-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Radio-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Receiver-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Sender-2/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/linn.co.uk-LipSync-1/service.xml', body='')
            mocked.get('http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/av.openhome.org-Debug-1/service.xml', body='')
        self.sut = Device(LOCATION)
        await self.sut.init()
        soap_request_calls = []
        return super().setUp()

    def test_volume_enabled(self):
        self.assertFalse(self.sut.volume_enabled)

    @async_test
    async def test_volume_level(self):
        self.assertIsNone(await self.sut.volume())

    @async_test
    async def test_volume_muted(self):
        self.assertIsNone(await self.sut.is_muted())

    @async_test
    async def test_set_volume(self):
        self.assertIsNone(await self.sut.set_volume(11))

    @async_test
    async def test_increase_volume(self):
        self.assertIsNone(await self.sut.increase_volume())

    @async_test
    async def test_decrease_volume(self):
        self.assertIsNone(await self.sut.decrease_volume())

    @async_test
    async def test_set_mute(self):
        self.assertIsNone(await self.sut.set_mute(True))
