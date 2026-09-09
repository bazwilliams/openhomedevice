"""What the device says it can do with whatever is playing.

Deciding which transport controls to offer by matching the source type
against a list of known types gets it wrong in both directions, and needs
extending for every streaming service ever invented. The Transport service
answers the same question properly, and differently: the capability belongs
to the transport mode and to the stream, not to the source.

The values below were read off a live Akurate DSM.
"""

import asyncio
import unittest

from openhomedevice.device import Device


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
        self.was_called_times += 1
        return self.response


class FakeService:
    def __init__(self, actions):
        self.actions = actions

    def action(self, name):
        return self.actions[name]


def device_reporting(mode_info, stream_info):
    """A device whose Transport service answers with the given capability."""
    device = Device("http://mydevice:12345/desc.xml")
    device.transport_service = FakeService(
        {"ModeInfo": FakeAction(mode_info), "StreamInfo": FakeAction(stream_info)}
    )
    return device


def mode(skip_next=False, skip_previous=False):
    return {"CanSkipNext": skip_next, "CanSkipPrevious": skip_previous}


def stream(pause=False):
    return {"StreamId": 0, "CanPause": pause}


class LineInputTests(unittest.TestCase):
    """A turntable on a balanced analog input can do none of it."""

    @async_test
    async def test_nothing_is_possible(self):
        device = device_reporting(mode(), stream())
        self.assertFalse(await device.can_pause())
        self.assertFalse(await device.can_skip_next())
        self.assertFalse(await device.can_skip_previous())


class RadioTests(unittest.TestCase):
    @async_test
    async def test_a_station_cannot_be_paused_or_skipped(self):
        """With no presets stored there is nothing to skip through."""
        device = device_reporting(mode(), stream())
        self.assertFalse(await device.can_pause())
        self.assertFalse(await device.can_skip_next())
        self.assertFalse(await device.can_skip_previous())


class PlaylistTests(unittest.TestCase):
    @async_test
    async def test_a_playing_track_allows_everything(self):
        device = device_reporting(
            mode(skip_next=True, skip_previous=True), stream(pause=True)
        )
        self.assertTrue(await device.can_pause())
        self.assertTrue(await device.can_skip_next())
        self.assertTrue(await device.can_skip_previous())

    @async_test
    async def test_an_unpausable_stream_in_a_playlist_allows_skipping_only(self):
        """Same source and mode, but the stream itself cannot be paused."""
        device = device_reporting(
            mode(skip_next=True, skip_previous=True), stream(pause=False)
        )
        self.assertFalse(await device.can_pause())
        self.assertTrue(await device.can_skip_next())
        self.assertTrue(await device.can_skip_previous())


class WhichActionAnswersTests(unittest.TestCase):
    @async_test
    async def test_pausing_comes_from_the_stream(self):
        m, s = FakeAction(mode()), FakeAction(stream())
        device = Device("http://mydevice:12345/desc.xml")
        device.transport_service = FakeService({"ModeInfo": m, "StreamInfo": s})

        await device.can_pause()

        self.assertEqual((s.was_called_times, m.was_called_times), (1, 0))

    @async_test
    async def test_skipping_comes_from_the_mode(self):
        m, s = FakeAction(mode()), FakeAction(stream())
        device = Device("http://mydevice:12345/desc.xml")
        device.transport_service = FakeService({"ModeInfo": m, "StreamInfo": s})

        await device.can_skip_next()
        await device.can_skip_previous()

        self.assertEqual((s.was_called_times, m.was_called_times), (0, 2))


class WithoutTransportServiceTests(unittest.TestCase):
    """None rather than False: the device cannot say, which is not the same
    as saying no. A caller falls back to guessing from the source type, as
    everything had to before the Transport service existed."""

    @async_test
    async def test_every_capability_is_unknown(self):
        device = Device("http://mydevice:12345/desc.xml")
        device.transport_service = None
        self.assertIsNone(await device.can_pause())
        self.assertIsNone(await device.can_skip_next())
        self.assertIsNone(await device.can_skip_previous())
