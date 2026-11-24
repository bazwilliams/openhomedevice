import asyncio
import unittest

from async_upnp_client.exceptions import (
    UpnpConnectionError,
    UpnpConnectionTimeoutError,
)

from openhomedevice.device import QUERY_ATTEMPTS, QUERY_TIMEOUT, Device
from openhomedevice.exceptions import OpenhomeConnectionError, OpenhomeTimeoutError

LOCATION = "http://mydevice:12345/desc.xml"


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

    def __init__(self, errors, result=None):
        self.errors = list(errors)
        self.result = result
        self.calls = []

    async def async_call(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            raise self.errors.pop(0)
        return self.result


class ScriptedService:
    def __init__(self, action):
        self._action = action

    def action(self, name):
        return self._action


class QueryRetryTests(unittest.TestCase):
    """A query the device never answers is re-sent; a command is not.

    Some Linn devices occasionally ignore a request, and async_upnp_client
    0.49 stopped retrying timeouts, which left players flapping unavailable.
    """

    def device_with_product_action(self, action):
        device = Device(LOCATION)
        device.product_service = ScriptedService(action)
        return device

    @async_test
    async def test_query_is_retried_after_a_timeout(self):
        action = ScriptedAction(
            [UpnpConnectionTimeoutError("no answer")] * (QUERY_ATTEMPTS - 1),
            result={"Value": True},
        )
        sut = self.device_with_product_action(action)

        self.assertTrue(await sut.is_in_standby())
        self.assertEqual(len(action.calls), QUERY_ATTEMPTS)

    @async_test
    async def test_query_uses_the_short_timeout(self):
        action = ScriptedAction([], result={"Name": "Klimax"})
        sut = self.device_with_product_action(action)

        await sut.name()
        self.assertEqual(action.calls, [{"request_timeout": QUERY_TIMEOUT}])

    @async_test
    async def test_query_arguments_are_kept_on_every_attempt(self):
        action = ScriptedAction(
            [UpnpConnectionTimeoutError("no answer")],
            result={"Value": 1, "Type": "Playlist", "Name": "Playlist"},
        )
        sut = self.device_with_product_action(action)

        await sut.source()
        self.assertEqual(
            action.calls[1:],
            [
                {"request_timeout": QUERY_TIMEOUT},
                {"request_timeout": QUERY_TIMEOUT, "Index": 1},
            ],
        )

    @async_test
    async def test_query_gives_up_after_the_last_attempt(self):
        action = ScriptedAction([UpnpConnectionTimeoutError("no answer")] * 10)
        sut = self.device_with_product_action(action)

        with self.assertRaises(OpenhomeTimeoutError):
            await sut.name()
        self.assertEqual(len(action.calls), QUERY_ATTEMPTS)

    @async_test
    async def test_query_is_not_retried_after_other_errors(self):
        """The requester already retries a dropped connection."""
        action = ScriptedAction([UpnpConnectionError("refused")] * 10)
        sut = self.device_with_product_action(action)

        with self.assertRaises(OpenhomeConnectionError):
            await sut.name()
        self.assertEqual(len(action.calls), 1)

    @async_test
    async def test_command_is_not_retried_after_a_timeout(self):
        """Re-sending a command the device may still be processing repeats it."""
        action = ScriptedAction([UpnpConnectionTimeoutError("no answer")] * 10)
        sut = self.device_with_product_action(action)

        with self.assertRaises(OpenhomeTimeoutError):
            await sut.set_standby(True)
        self.assertEqual(action.calls, [{"Value": True}])
