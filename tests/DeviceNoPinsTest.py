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

    with open(
        os.path.join(os.path.dirname(__file__), "data/nopinsdevice.xml")
    ) as file:
        return MockResponse(file.read(), 200)


class DeviceWithNoPinsTests(unittest.TestCase):

    LOCATION = "http://mydevice:12345/desc.xml"

    @patch("requests.get", side_effect=mocked_requests_get)
    def setUp(self, patched_get):
        from openhomedevice.Device import Device

        self.sut = Device(self.LOCATION)
        soap_request_calls = []
        return super().setUp()

    def test_number_of_pins(self):
        self.assertListEqual(
            self.sut.Pins(), list()
        )

    def test_invoke_pin(self):
        self.sut.InvokePin(42)
