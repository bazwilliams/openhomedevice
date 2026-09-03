import asyncio
import os
import unittest
from unittest import mock

from aiohttp import ClientSession
from aioresponses import aioresponses
from async_upnp_client.aiohttp import AiohttpRequester, AiohttpSessionRequester

from openhomedevice.device import Device

LOCATION = "http://mydevice:12345/desc.xml"
SERVICE_XML = '<scpd xmlns="urn:schemas-upnp-org:service-1-0"><serviceStateTable/></scpd>'
BASE = "http://mydevice:12345/4c494e4e-1234-ab12-abcd-01234567819f/Upnp"


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


def mock_device(mocked):
    with open(os.path.join(os.path.dirname(__file__), "data/v1description.xml")) as file:
        mocked.get(LOCATION, body=file.read())
    for service in (
        "av.openhome.org-Product-1",
        "av.openhome.org-Volume-1",
        "av.openhome.org-Info-1",
        "av.openhome.org-Playlist-1",
    ):
        mocked.get(f"{BASE}/{service}/service.xml", body=SERVICE_XML)


class SessionTests(unittest.TestCase):
    """A caller with its own aiohttp session should be able to supply it.

    Home Assistant shares one session across every integration, and without
    this each request opens and closes a session of its own.
    """

    @async_test
    @aioresponses()
    async def test_supplied_session_is_used(self, mocked):
        mock_device(mocked)
        session = ClientSession()
        try:
            with mock.patch(
                "openhomedevice.device.AiohttpSessionRequester",
                wraps=AiohttpSessionRequester,
            ) as requester:
                sut = Device(LOCATION, session=session)
                await sut.init()
            requester.assert_called_once_with(session)
        finally:
            await session.close()

    @async_test
    @aioresponses()
    async def test_session_is_reachable_on_the_device(self, mocked):
        mock_device(mocked)
        session = ClientSession()
        try:
            sut = Device(LOCATION, session=session)
            self.assertIs(sut.session, session)
        finally:
            await session.close()

    @async_test
    @aioresponses()
    async def test_without_a_session_the_default_requester_is_used(self, mocked):
        mock_device(mocked)
        with mock.patch(
            "openhomedevice.device.AiohttpSessionRequester"
        ) as session_requester, mock.patch(
            "openhomedevice.device.AiohttpRequester", wraps=AiohttpRequester
        ) as default_requester:
            sut = Device(LOCATION)
            await sut.init()
        session_requester.assert_not_called()
        default_requester.assert_called_once_with()

    @async_test
    @aioresponses()
    async def test_supplied_session_is_not_closed(self, mocked):
        """The caller owns the session, so the library must leave it open."""
        mock_device(mocked)
        session = ClientSession()
        try:
            sut = Device(LOCATION, session=session)
            await sut.init()
            self.assertFalse(session.closed)
        finally:
            await session.close()

    @async_test
    @aioresponses()
    async def test_device_still_works_without_a_session(self, mocked):
        """Existing callers pass a location only, and must keep working."""
        mock_device(mocked)
        sut = Device(LOCATION)
        await sut.init()
        self.assertIsNotNone(sut.product_service)
