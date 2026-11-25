import asyncio
import unittest

from async_upnp_client.exceptions import (
    UpnpConnectionError,
    UpnpConnectionTimeoutError,
)

from openhomedevice.device import RETRY_ATTEMPTS, Device
from openhomedevice.exceptions import OpenhomeConnectionError, OpenhomeTimeoutError

LOCATION = "http://mydevice:12345/desc.xml"
TIMEOUT = UpnpConnectionTimeoutError("no answer")


def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()

    return wrapper


class ScriptedAction:
    """Raises each scripted error in turn, then answers with result."""

    def __init__(self, errors=(), result=None):
        self.errors = list(errors)
        self.result = result
        self.calls = []

    async def async_call(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            raise self.errors.pop(0)
        return self.result


class ScriptedService:
    def __init__(self, **actions):
        self.actions = actions

    def action(self, name):
        return self.actions[name]


class RetryTests(unittest.TestCase):
    """A read the device never answers is retried; a command is not.

    Some Linn devices occasionally ignore a request, and async_upnp_client
    0.49 stopped retrying timeouts, which left players flapping unavailable.
    """

    def device(self, **services):
        device = Device(LOCATION)
        device.transport_service = None
        for name, service in services.items():
            setattr(device, name, service)
        return device

    @async_test
    async def test_read_is_retried_after_a_timeout(self):
        standby = ScriptedAction([TIMEOUT] * (RETRY_ATTEMPTS - 1), {"Value": True})
        sut = self.device(product_service=ScriptedService(Standby=standby))

        self.assertTrue(await sut.is_in_standby())
        self.assertEqual(len(standby.calls), RETRY_ATTEMPTS)

    @async_test
    async def test_read_gives_up_after_the_last_attempt(self):
        product = ScriptedAction([TIMEOUT] * 10)
        sut = self.device(product_service=ScriptedService(Product=product))

        with self.assertRaises(OpenhomeTimeoutError):
            await sut.name()
        self.assertEqual(len(product.calls), RETRY_ATTEMPTS)

    @async_test
    async def test_read_is_not_retried_after_other_errors(self):
        """The requester already retries a dropped connection."""
        product = ScriptedAction([UpnpConnectionError("refused")] * 10)
        sut = self.device(product_service=ScriptedService(Product=product))

        with self.assertRaises(OpenhomeConnectionError):
            await sut.name()
        self.assertEqual(len(product.calls), 1)

    @async_test
    async def test_command_is_not_retried_after_a_timeout(self):
        """Re-sending a command the device may still be processing repeats it."""
        set_standby = ScriptedAction([TIMEOUT] * 10)
        sut = self.device(product_service=ScriptedService(SetStandby=set_standby))

        with self.assertRaises(OpenhomeTimeoutError):
            await sut.set_standby(True)
        self.assertEqual(len(set_standby.calls), 1)

    @async_test
    async def test_command_sends_once_after_its_read_is_retried(self):
        """play() reads the source first; only that read is retried."""
        source_index = ScriptedAction([TIMEOUT], {"Value": 0})
        source = ScriptedAction(result={"Type": "Playlist", "Name": "Playlist"})
        play = ScriptedAction(result={})
        sut = self.device(
            product_service=ScriptedService(SourceIndex=source_index, Source=source),
            playlist_service=ScriptedService(Play=play),
        )

        await sut.play()
        self.assertEqual(len(source_index.calls), 2)
        self.assertEqual(len(play.calls), 1)

    @async_test
    async def test_nested_reads_do_not_multiply_attempts(self):
        """transport_state() calls source(), whose own retries must not multiply."""
        source_index = ScriptedAction([TIMEOUT] * 10)
        sut = self.device(product_service=ScriptedService(SourceIndex=source_index))

        with self.assertRaises(OpenhomeTimeoutError):
            await sut.transport_state()
        self.assertEqual(len(source_index.calls), RETRY_ATTEMPTS)
