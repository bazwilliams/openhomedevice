import unittest
from unittest.mock import patch
import os

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, payload, status_code):
            self.payload = payload
            self.status_code = status_code

        @property
        def text(self):
            return self.payload

    with open(os.path.join(os.path.dirname(__file__), 'data/novolumedevice.xml')) as file:
        return MockResponse(file.read(), 200)

class DeviceWithNoVolumeTests(unittest.TestCase):

    LOCATION = "http://mydevice:12345/desc.xml"

    @patch('requests.get', side_effect=mocked_requests_get)
    def setUp(self, patched_get):
        from openhomedevice.Device import Device
        self.sut = Device(self.LOCATION)
        soap_request_calls = []
        return super().setUp()

    def test_volume_enabled(self):
        self.assertFalse(self.sut.VolumeEnabled())

    def test_volume_level(self):
        self.assertIsNone(self.sut.VolumeLevel())

    def test_volume_muted(self):
        self.assertIsNone(self.sut.IsMuted())

    def test_set_volume(self):
        self.assertIsNone(self.sut.SetVolumeLevel(11))

    def test_increase_volume(self):
        self.assertIsNone(self.sut.IncreaseVolume())

    def test_decrease_volume(self):
        self.assertIsNone(self.sut.DecreaseVolume())

    def test_set_mute(self):
        self.assertIsNone(self.sut.SetMute(True))
