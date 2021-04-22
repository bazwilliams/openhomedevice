import unittest

from openhomedevice.didl_lite import generate_string, parse, parse_duration, parse_int


class DidlLiteTests(unittest.TestCase):
    def test_int_parsing(self):
        self.assertEqual(parse_duration("42"), 42)
        self.assertEqual(parse_duration("42.5"), 42)
        self.assertIsNone(parse_int("forty"))
        self.assertIsNone(parse_int(None))

    def test_duration_parsing(self):
        self.assertEqual(parse_duration("0:07:40.000"), 460)
        self.assertEqual(parse_duration("1:00.000"), 60)
        self.assertEqual(parse_duration("42.000"), 42)
        self.assertEqual(parse_duration("2:0.5"), 120)
        self.assertIsNone(parse_duration("forty"))
        self.assertIsNone(parse_duration(None))

    def test_parse_empty_didlite(self):
        result = parse(None)
        self.assertEqual(result, {})

    def test_parse_corrupt_didlite(self):
        result = parse(
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></itemX></DIDL-Lite>'
        )
        self.assertEqual(result, {})

    def test_parse_didlite_missing_item(self):
        result = parse(
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"></DIDL-Lite>'
        )
        self.assertEqual(result, {})

    def test_empty_track_details(self):
        track_details = {}
        result = generate_string(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details_title_is_none(self):
        track_details = {}
        track_details["title"] = None
        result = generate_string(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details_uri_is_none(self):
        track_details = {}
        track_details["uri"] = None
        result = generate_string(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details_albumArtwork_is_none(self):
        track_details = {}
        track_details["albumArtwork"] = None
        result = generate_string(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title></dc:title><res protocolInfo="*:*:*:*"></res><upnp:albumArtURI></upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )

    def test_track_details(self):
        track_details = {}
        track_details["albumArtwork"] = "ALBUMARTWORK"
        track_details["title"] = "TITLE"
        track_details["uri"] = "URI"
        result = generate_string(track_details)
        self.assertEqual(
            result,
            '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title>TITLE</dc:title><res protocolInfo="*:*:*:*">URI</res><upnp:albumArtURI>ALBUMARTWORK</upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>',
        )
