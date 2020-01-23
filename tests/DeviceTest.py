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

    with open(os.path.join(os.path.dirname(__file__), "data/description.xml")) as file:
        return MockResponse(file.read(), 200)


soap_request_calls = []


def mocked_soap_request(*args, **kwargs):
    global soap_request_calls
    soap_request_calls.append(args)
    if args[2] == "Product":
        with open(
            os.path.join(os.path.dirname(__file__), "data/productSoapResponse.xml")
        ) as file:
            return file.read()
    if args[2] == "Standby":
        with open(
            os.path.join(
                os.path.dirname(__file__), "data/productStandbySoapResponse.xml"
            )
        ) as file:
            return file.read()
    if args[1] == "urn:av-openhome-org:service:Pins:1" and args[2] == "GetDeviceMax":
        with open(
            os.path.join(
                os.path.dirname(__file__), "data/pinsDeviceMaxSoapResponse.xml"
            )
        ) as file:
            return file.read()
    if args[1] == "urn:av-openhome-org:service:Pins:1" and args[2] == "GetIdArray":
        with open(
            os.path.join(
                os.path.dirname(__file__), "data/pinsGetIdArraySoapResponse.xml"
            )
        ) as file:
            return file.read()
    if args[1] == "urn:av-openhome-org:service:Pins:1" and args[2] == "ReadList":
        with open(
            os.path.join(os.path.dirname(__file__), "data/pinsReadListSoapResponse.xml")
        ) as file:
            return file.read()
    print(args)


class DidlLiteTests(unittest.TestCase):

    LOCATION = "http://mydevice:12345/desc.xml"

    @patch("requests.get", side_effect=mocked_requests_get)
    @patch("openhomedevice.Soap.soapRequest", side_effect=mocked_soap_request)
    def setUp(self, patched_soap_request, patched_get):
        from openhomedevice.Device import Device

        global soap_request_calls

        self.sut = Device(self.LOCATION)
        soap_request_calls = []
        return super().setUp()

    def test_device_parses_uuid(self):
        self.assertEqual(self.sut.Uuid(), "4c494e4e-1234-ab12-abcd-01234567819f")

    def test_device_advertises_transport_service(self):
        self.assertTrue(self.sut.HasTransportService())

    def test_device_name(self):
        self.assertEqual(self.sut.Name(), b"My Friendly Name")

    def test_room_name(self):
        self.assertEqual(self.sut.Room(), b"Bathroom")

    def test_set_standby_off(self):
        self.sut.SetStandby(False)
        self.assertEqual(soap_request_calls[0][3], "<Value>0</Value>")

    def test_set_standby_on(self):
        self.sut.SetStandby(True)
        self.assertEqual(soap_request_calls[0][3], "<Value>1</Value>")

    def test_is_in_standby(self):
        self.assertEqual(self.sut.IsInStandby(), True)

    def test_play_media_with_nothing(self):
        self.sut.PlayMedia(None)
        self.assertEqual(len(soap_request_calls), 0)

    def test_play_media_with_details(self):
        from openhomedevice.DidlLite import didlLiteString

        track_details = {}
        track_details["uri"] = "https://host/uri.flac"
        track_details["title"] = "TITLE"
        track_details["albumArtwork"] = "https://host/uri.jpg"

        expectedValue = "<Uri>{0}</Uri><Metadata>{1}</Metadata>".format(
            "https://host/uri.flac", didlLiteString(track_details)
        )
        self.sut.PlayMedia(track_details)
        self.assertEqual(soap_request_calls[0][3], expectedValue)

    def test_play_media_with_invalid_uri(self):
        from openhomedevice.DidlLite import didlLiteString

        track_details = {}
        track_details["title"] = "TITLE"
        track_details["albumArtwork"] = "https://host/uri.jpg"

        expectedValue = "<Uri></Uri><Metadata>{0}</Metadata>".format(
            didlLiteString(track_details)
        )
        self.sut.PlayMedia(track_details)
        self.assertEqual(soap_request_calls[0][3], expectedValue)

    def test_number_of_pins(self):
        self.assertListEqual(
            self.sut.Pins(),
            [
                {"index": 1, "title": "Sky", 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI2'},
                {"index": 2, "title": "Playstation 4", 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI1'},
                {"index": 4, "title": "Fire Stick", 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI3'},
                {"index": 6, "title": "LP12", 'artworkUri': 'external:///source?type=Analog&systemName=Balanced'},
            ],
        )

    def test_invoke_pin(self):
        self.sut.InvokePin(42)
        self.assertEqual(soap_request_calls[0][1], "urn:av-openhome-org:service:Pins:1")
        self.assertEqual(soap_request_calls[0][2], "InvokeIndex")
        self.assertEqual(soap_request_calls[0][3], "<Index>41</Index>")
