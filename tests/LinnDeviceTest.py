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

class FakeProductAction:
    async def async_call(self):
        return {
            "Name": b"My Friendly Name",
            "Room": b"Bathroom"
        }

class FakeSetStandbyAction:
    async def async_call(self, Value):
        self.Value = Value
        return {}

class FakeStandbyAction:
    async def async_call(self):
        return {
            "Value": True
        }

product_actions = {
    'Product': FakeProductAction(),
    'SetStandby': FakeSetStandbyAction(),
    'Standby': FakeStandbyAction()
}
class FakeProductService:
    def action(self, action_called):
        return product_actions[action_called]

# def mocked_soap_request(*args, **kwargs):
#     global soap_request_calls
#     soap_request_calls.append(args)
#     if args[2] == "Product":
#         with open(
#             os.path.join(os.path.dirname(__file__), "data/productSoapResponse.xml")
#         ) as file:
#             return file.read()
#     if args[2] == "Standby":
#         with open(
#             os.path.join(
#                 os.path.dirname(__file__), "data/productStandbySoapResponse.xml"
#             )
#         ) as file:
#             return file.read()
#     if args[1] == "urn:av-openhome-org:service:Pins:1" and args[2] == "GetDeviceMax":
#         with open(
#             os.path.join(
#                 os.path.dirname(__file__), "data/pinsDeviceMaxSoapResponse.xml"
#             )
#         ) as file:
#             return file.read()
#     if args[1] == "urn:av-openhome-org:service:Pins:1" and args[2] == "GetIdArray":
#         with open(
#             os.path.join(
#                 os.path.dirname(__file__), "data/pinsGetIdArraySoapResponse.xml"
#             )
#         ) as file:
#             return file.read()
#     if args[1] == "urn:av-openhome-org:service:Pins:1" and args[2] == "ReadList":
#         with open(
#             os.path.join(os.path.dirname(__file__), "data/pinsReadListSoapResponse.xml")
#         ) as file:
#             return file.read()
#     print(args)


class LinnDeviceTests(unittest.TestCase):

    @async_test
    @aioresponses()
    async def setUp(self, mocked):
        LOCATION = "http://mydevice:12345/desc.xml"
        with open(
            os.path.join(os.path.dirname(__file__), "data/linndescription.xml")
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

    def test_device_parses_uuid(self):
        self.assertEqual(self.sut.uuid(), "uuid:4c494e4e-1234-ab12-abcd-01234567819f")

    @async_test
    async def test_device_name(self):
        self.sut.product_service = FakeProductService()
        self.assertEqual(await self.sut.name(), b"My Friendly Name")

    @async_test
    async def test_device_name(self):
        self.sut.product_service = FakeProductService()
        self.assertEqual(await self.sut.room(), b"Bathroom") 

    @async_test
    async def test_set_standby_off(self):
        self.sut.product_service = FakeProductService()
        await self.sut.set_standby(False)
        self.assertFalse(product_actions['SetStandby'].Value)

    @async_test
    async def test_set_standby_on(self):
        self.sut.product_service = FakeProductService()
        await self.sut.set_standby(True)
        self.assertTrue(product_actions['SetStandby'].Value)

    @async_test
    async def test_is_in_standby(self):
        self.sut.product_service = FakeProductService()
        self.assertEqual(await self.sut.is_in_standby(), True)

    # def test_play_media_with_nothing(self):
    #     self.sut.PlayMedia(None)
    #     self.assertEqual(len(soap_request_calls), 0)

    # def test_play_media_with_details(self):
    #     from openhomedevice.DidlLite import didlLiteString

    #     track_details = {}
    #     track_details["uri"] = "https://host/uri.flac"
    #     track_details["title"] = "TITLE"
    #     track_details["albumArtwork"] = "https://host/uri.jpg"

    #     expectedValue = "<Uri>{0}</Uri><Metadata>{1}</Metadata>".format(
    #         "https://host/uri.flac", didlLiteString(track_details)
    #     )
    #     self.sut.PlayMedia(track_details)
    #     self.assertEqual(soap_request_calls[0][3], expectedValue)

    # def test_play_media_with_invalid_uri(self):
    #     from openhomedevice.DidlLite import didlLiteString

    #     track_details = {}
    #     track_details["title"] = "TITLE"
    #     track_details["albumArtwork"] = "https://host/uri.jpg"

    #     expectedValue = "<Uri></Uri><Metadata>{0}</Metadata>".format(
    #         didlLiteString(track_details)
    #     )
    #     self.sut.PlayMedia(track_details)
    #     self.assertEqual(soap_request_calls[0][3], expectedValue)

    # def test_number_of_pins(self):
    #     self.assertListEqual(
    #         self.sut.Pins(),
    #         [
    #             {"index": 1, "title": "Sky", 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI2'},
    #             {"index": 2, "title": "Playstation 4", 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI1'},
    #             {"index": 4, "title": "Fire Stick", 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI3'},
    #             {"index": 6, "title": "LP12", 'artworkUri': 'external:///source?type=Analog&systemName=Balanced'},
    #         ],
    #     )

    # def test_invoke_pin(self):
    #     self.sut.InvokePin(42)
    #     self.assertEqual(soap_request_calls[0][1], "urn:av-openhome-org:service:Pins:1")
    #     self.assertEqual(soap_request_calls[0][2], "InvokeIndex")
    #     self.assertEqual(soap_request_calls[0][3], "<Index>41</Index>")
