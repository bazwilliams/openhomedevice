import asyncio
import unittest
import xml.etree.ElementTree as etree

from aiohttp import ClientConnectionError
from aioresponses import aioresponses
from async_upnp_client.exceptions import (
    UpnpActionError,
    UpnpCommunicationError,
    UpnpConnectionError,
    UpnpConnectionTimeoutError,
    UpnpResponseError,
    UpnpXmlParseError,
)

from openhomedevice.device import Device
from openhomedevice.exceptions import (
    OpenhomeConnectionError,
    OpenhomeDeviceError,
    OpenhomeError,
    OpenhomeTimeoutError,
)

LOCATION = "http://mydevice:12345/desc.xml"


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


def real_parse_error():
    """UpnpXmlParseError copies attributes off a genuine ParseError."""
    try:
        etree.fromstring("not xml")
    except etree.ParseError as err:
        return err


class RaisingAction:
    def __init__(self, error):
        self.error = error

    async def async_call(self, **kwargs):
        raise self.error


class RaisingService:
    """Stands in for a service whose every action fails."""

    def __init__(self, error):
        self.error = error

    def action(self, name):
        return RaisingAction(self.error)


class ErrorTranslationTests(unittest.TestCase):
    """Errors from async_upnp_client must not reach callers unchanged."""

    def device_that_raises(self, error):
        device = Device(LOCATION)
        device.product_service = RaisingService(error)
        return device

    @async_test
    async def test_connection_error_is_translated(self):
        sut = self.device_that_raises(UpnpConnectionError("unreachable"))
        with self.assertRaises(OpenhomeConnectionError):
            await sut.name()

    @async_test
    async def test_timeout_is_translated(self):
        sut = self.device_that_raises(UpnpConnectionTimeoutError("too slow"))
        with self.assertRaises(OpenhomeTimeoutError):
            await sut.room()

    @async_test
    async def test_timeout_is_also_a_connection_error(self):
        """So callers that do not care why it was unreachable catch one type."""
        sut = self.device_that_raises(UpnpConnectionTimeoutError("too slow"))
        with self.assertRaises(OpenhomeConnectionError):
            await sut.room()

    @async_test
    async def test_communication_error_is_translated(self):
        sut = self.device_that_raises(UpnpCommunicationError("broken pipe"))
        with self.assertRaises(OpenhomeConnectionError):
            await sut.is_in_standby()

    @async_test
    async def test_http_error_status_is_a_device_error(self):
        """The device answered, it just did not like the request."""
        sut = self.device_that_raises(UpnpResponseError(status=500))
        with self.assertRaises(OpenhomeDeviceError):
            await sut.name()

    @async_test
    async def test_soap_fault_is_a_device_error(self):
        sut = self.device_that_raises(UpnpActionError("no such action"))
        with self.assertRaises(OpenhomeDeviceError):
            await sut.set_standby(True)

    @async_test
    async def test_unparseable_response_is_a_device_error(self):
        sut = self.device_that_raises(UpnpXmlParseError(real_parse_error()))
        with self.assertRaises(OpenhomeDeviceError):
            await sut.source()

    @async_test
    async def test_every_error_shares_one_base_class(self):
        for error in (
            UpnpConnectionError("a"),
            UpnpConnectionTimeoutError("b"),
            UpnpResponseError(status=500),
            UpnpActionError("c"),
        ):
            sut = self.device_that_raises(error)
            with self.assertRaises(OpenhomeError):
                await sut.name()

    @async_test
    async def test_original_error_is_kept_as_the_cause(self):
        original = UpnpConnectionError("unreachable")
        sut = self.device_that_raises(original)
        with self.assertRaises(OpenhomeConnectionError) as caught:
            await sut.name()
        self.assertIs(caught.exception.__cause__, original)

    @async_test
    @aioresponses()
    async def test_init_translates_an_unreachable_device(self, mocked):
        """The path Home Assistant hits when setting up an offline device."""
        mocked.get(LOCATION, exception=ClientConnectionError("no route to host"))
        sut = Device(LOCATION)
        with self.assertRaises(OpenhomeConnectionError):
            await sut.init()

    @async_test
    @aioresponses()
    async def test_init_translates_an_http_error(self, mocked):
        mocked.get(LOCATION, status=500)
        sut = Device(LOCATION)
        with self.assertRaises(OpenhomeDeviceError):
            await sut.init()

    @async_test
    @aioresponses()
    async def test_init_translates_an_unparseable_description(self, mocked):
        mocked.get(LOCATION, body="this is not xml")
        sut = Device(LOCATION)
        with self.assertRaises(OpenhomeDeviceError):
            await sut.init()
