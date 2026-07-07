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


class DeviceWithNoHardwareConfigTests(unittest.TestCase):
    """Devices without the AURALiC HardwareConfig service degrade gracefully."""

    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/novolumedevice.xml")
        ) as file:
            mocked.get(LOCATION, body=file.read())
            for service in (
                "av.openhome.org-Config-2",
                "av.openhome.org-ConfigApp-1",
                "av.openhome.org-Credentials-1",
                "av.openhome.org-Debug-1",
                "av.openhome.org-Exakt-4",
                "av.openhome.org-Info-1",
                "av.openhome.org-Pins-1",
                "av.openhome.org-Playlist-1",
                "av.openhome.org-Product-3",
                "av.openhome.org-Radio-1",
                "av.openhome.org-Receiver-1",
                "av.openhome.org-Sender-2",
                "av.openhome.org-Time-1",
                "av.openhome.org-Transport-1",
                "av.openhome.org-Volume-4",
                "linn.co.uk-Cloud-1",
                "linn.co.uk-Configuration-1",
                "linn.co.uk-Diagnostics-1",
                "linn.co.uk-Exakt2-1",
                "linn.co.uk-ExaktInputs-1",
                "linn.co.uk-LipSync-1",
                "linn.co.uk-Privacy-1",
                "linn.co.uk-Update-2",
                "linn.co.uk-Volkano-1",
            ):
                mocked.get(
                    f"http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp/{service}/service.xml",
                    body='<scpd xmlns="urn:schemas-upnp-org:service-1-0"><serviceStateTable/></scpd>',
                )
            self.sut = Device(LOCATION)
            await self.sut.init()

    def test_hardware_config_service_is_absent(self):
        self.assertIsNone(self.sut.hardware_config_service)

    @async_test
    async def test_is_halted_returns_none(self):
        self.assertIsNone(await self.sut.is_halted())

    @async_test
    async def test_set_halt_is_a_noop(self):
        await self.sut.set_halt(True)  # must not raise
