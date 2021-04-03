import unittest

from openhomedevice.didl_lite import generate_string


class DidlLiteTests(unittest.TestCase):
    def setUp(self):
        self.sut = generate_string

    def test_empty_track_details(self):
        track_details = {}
        result = self.sut(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details_title_is_none(self):
        track_details = {}
        track_details["title"] = None
        result = self.sut(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details_uri_is_none(self):
        track_details = {}
        track_details["uri"] = None
        result = self.sut(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details_albumArtwork_is_none(self):
        track_details = {}
        track_details["albumArtwork"] = None
        result = self.sut(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details(self):
        track_details = {}
        track_details["albumArtwork"] = "ALBUMARTWORK"
        track_details["title"] = "TITLE"
        track_details["uri"] = "URI"
        result = self.sut(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title>TITLE</dc:title><res protocolInfo="*:*:*:*">URI</res><upnp:albumArtURI>ALBUMARTWORK</upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )
