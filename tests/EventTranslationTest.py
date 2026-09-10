import unittest

from openhomedevice.device import Device
from openhomedevice.events import (
    _LIFECYCLE_KEYS,
    EVENT_KEYS,
    EventTranslator,
)
from openhomedevice.services import (
    INFO_SERVICE_ID,
    PRODUCT_SERVICE_ID,
    TRANSPORT_SERVICE_ID,
    VOLUME_SERVICE_ID,
)

SOURCE_XML = (
    "<SourceList>"
    "<Source><Name>Playlist</Name><Type>Playlist</Type><Visible>true</Visible></Source>"
    "<Source><Name>Radio</Name><Type>Radio</Type><Visible>true</Visible></Source>"
    "<Source><Name>Songcast</Name><Type>Receiver</Type><Visible>false</Visible></Source>"
    "<Source><Name>Airplay</Name><Type>Net Aux</Type><Visible>true</Visible></Source>"
    "</SourceList>"
)

TRACK_METADATA = (
    '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" '
    'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">'
    '<item id="" parentID="" restricted="True">'
    "<dc:title>Cirrus Minor</dc:title>"
    "<upnp:artist>Pink Floyd</upnp:artist>"
    "<upnp:albumArtURI>http://example.com/art.jpg</upnp:albumArtURI>"
    "</item>"
    "</DIDL-Lite>"
)


class FakeStateVariable:
    """Stands in for an async_upnp_client UpnpStateVariable.

    Only the name and the already-converted value matter to the translator;
    the conversion from the wire format is the client library's job.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value


def changes(service_id, **variables):
    """Translate one event made up of the named state variables."""
    return EventTranslator().translate(
        service_id,
        [FakeStateVariable(name, value) for name, value in variables.items()],
    )


class VolumeEventTests(unittest.TestCase):
    def test_volume_is_reported_as_volume(self):
        self.assertEqual(changes(VOLUME_SERVICE_ID, Volume=42), {"volume": 42})

    def test_mute_is_reported_as_is_muted(self):
        """The key matches is_muted(), not the device's variable name Mute."""
        self.assertEqual(changes(VOLUME_SERVICE_ID, Mute=True), {"is_muted": True})

    def test_volume_and_mute_arrive_together(self):
        self.assertEqual(
            changes(VOLUME_SERVICE_ID, Volume=10, Mute=False),
            {"volume": 10, "is_muted": False},
        )

    def test_other_volume_variables_are_dropped(self):
        """The service events a dozen variables this library does not expose."""
        self.assertEqual(changes(VOLUME_SERVICE_ID, Balance=0, FadeMax=3), {})


class TransportEventTests(unittest.TestCase):
    def test_transport_state_is_reported(self):
        self.assertEqual(
            changes(TRANSPORT_SERVICE_ID, TransportState="Playing"),
            {"transport_state": "Playing"},
        )


class TransportCapabilityTests(unittest.TestCase):
    """What the device says it can do with whatever is playing right now."""

    def test_each_capability_is_reported_under_its_method_name(self):
        self.assertEqual(
            changes(
                TRANSPORT_SERVICE_ID,
                CanPause=True,
                CanSkipNext=True,
                CanSkipPrevious=False,
            ),
            {
                "can_pause": True,
                "can_skip_next": True,
                "can_skip_previous": False,
            },
        )

    def test_capabilities_with_no_action_behind_them_are_dropped(self):
        """Seeking, repeating and shuffling are evented but cannot be done."""
        self.assertEqual(
            changes(
                TRANSPORT_SERVICE_ID, CanSeek=True, CanRepeat=True, CanShuffle=True
            ),
            {},
        )

    def test_a_line_input_reports_no_capability_at_all(self):
        """A turntable on an analog input: taken from a real Akurate DSM."""
        self.assertEqual(
            changes(
                TRANSPORT_SERVICE_ID,
                TransportState="Playing",
                CanPause=False,
                CanSkipNext=False,
                CanSkipPrevious=False,
            ),
            {
                "transport_state": "Playing",
                "can_pause": False,
                "can_skip_next": False,
                "can_skip_previous": False,
            },
        )

    def test_one_capability_can_change_on_its_own(self):
        """Starting playback flips CanPause without touching the rest."""
        self.assertEqual(
            changes(TRANSPORT_SERVICE_ID, CanPause=True), {"can_pause": True}
        )


class ProductEventTests(unittest.TestCase):
    def test_standby_is_reported(self):
        self.assertEqual(
            changes(PRODUCT_SERVICE_ID, Standby=True), {"is_in_standby": True}
        )

    def test_room_and_name_are_reported(self):
        self.assertEqual(
            changes(PRODUCT_SERVICE_ID, ProductRoom="Kitchen", ProductName="Sneaky"),
            {"room": "Kitchen", "name": "Sneaky"},
        )

    def test_source_xml_becomes_the_visible_sources(self):
        """Same shape as sources(): hidden sources gone, indices untouched."""
        self.assertEqual(
            changes(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML)["sources"],
            [
                {"index": 0, "name": "Playlist", "type": "Playlist"},
                {"index": 1, "name": "Radio", "type": "Radio"},
                {"index": 3, "name": "Airplay", "type": "Net Aux"},
            ],
        )

    def test_source_index_alone_reports_nothing(self):
        """No list to resolve against, and a bare index is not ours to report."""
        self.assertEqual(changes(PRODUCT_SERVICE_ID, SourceIndex=1), {})

    def test_the_index_is_never_reported_on_its_own(self):
        """Events mirror the methods, and no method returns a bare index."""
        result = changes(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML, SourceIndex=1)
        self.assertEqual(set(result), {"sources", "source"})

    def test_source_is_resolved_when_both_halves_arrive(self):
        result = changes(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML, SourceIndex=1)
        self.assertEqual(result["source"], {"type": "Radio", "name": "Radio"})

    def test_a_hidden_source_still_resolves(self):
        """Songcast is hidden from sources() but is still selectable."""
        result = changes(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML, SourceIndex=2)
        self.assertEqual(result["source"], {"type": "Receiver", "name": "Songcast"})

    def test_malformed_source_xml_does_not_lose_the_rest_of_the_event(self):
        result = changes(PRODUCT_SERVICE_ID, SourceXml="<not xml", Standby=False)
        self.assertEqual(result, {"is_in_standby": False})


class SourceAcrossEventsTests(unittest.TestCase):
    """The source list and the selected index rarely change in the same event."""

    def setUp(self):
        self.translator = EventTranslator()

    def translate(self, service_id, **variables):
        return self.translator.translate(
            service_id,
            [FakeStateVariable(name, value) for name, value in variables.items()],
        )

    def test_an_index_change_uses_the_list_from_an_earlier_event(self):
        self.translate(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML, SourceIndex=0)
        result = self.translate(PRODUCT_SERVICE_ID, SourceIndex=3)
        self.assertEqual(result["source"], {"type": "Net Aux", "name": "Airplay"})

    def test_a_new_list_renames_the_source_at_the_current_index(self):
        """Renaming a source in the app sends a new list, not a new index."""
        self.translate(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML, SourceIndex=1)
        renamed = SOURCE_XML.replace("<Name>Radio</Name>", "<Name>Stations</Name>")
        result = self.translate(PRODUCT_SERVICE_ID, SourceXml=renamed)
        self.assertEqual(result["source"], {"type": "Radio", "name": "Stations"})

    def test_source_is_left_out_when_neither_half_changed(self):
        """An unrelated change should not re-report a source that stood still."""
        self.translate(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML, SourceIndex=1)
        result = self.translate(PRODUCT_SERVICE_ID, Standby=True)
        self.assertEqual(result, {"is_in_standby": True})

    def test_an_index_outside_the_list_reports_no_source(self):
        self.translate(PRODUCT_SERVICE_ID, SourceXml=SOURCE_XML)
        result = self.translate(PRODUCT_SERVICE_ID, SourceIndex=99)
        self.assertEqual(result, {})


class InfoEventTests(unittest.TestCase):
    def test_metadata_is_parsed_into_track_info(self):
        """The same dict track_info() would have returned."""
        track_info = changes(INFO_SERVICE_ID, Metadata=TRACK_METADATA)["track_info"]
        self.assertEqual(track_info["title"], "Cirrus Minor")
        self.assertEqual(track_info["artist"], ["Pink Floyd"])
        self.assertEqual(track_info["albumArtwork"], "http://example.com/art.jpg")

    def test_unparseable_metadata_gives_an_empty_track(self):
        self.assertEqual(
            changes(INFO_SERVICE_ID, Metadata="<not xml")["track_info"], {}
        )


class UnknownServiceTests(unittest.TestCase):
    def test_a_service_that_is_not_subscribed_to_is_ignored(self):
        """Guards against a shared notify server delivering somebody else's event."""
        self.assertEqual(
            changes("urn:av-openhome-org:serviceId:Radio", TransportState="Playing"), {}
        )


class EventVocabularyTests(unittest.TestCase):
    """Events mirror the methods, and nothing is allowed to drift from that."""

    def test_every_event_key_names_a_device_method(self):
        for key in sorted(EVENT_KEYS):
            with self.subTest(key=key):
                self.assertTrue(
                    hasattr(Device, key),
                    f"event key {key!r} has no Device.{key} behind it",
                )

    def test_every_key_a_translation_produces_is_declared(self):
        """EVENT_KEYS is the whole vocabulary, not a list someone forgot."""
        produced = set()
        produced |= set(changes(VOLUME_SERVICE_ID, Volume=1, Mute=True))
        produced |= set(
            changes(
                TRANSPORT_SERVICE_ID,
                TransportState="Playing",
                CanPause=True,
                CanSkipNext=True,
                CanSkipPrevious=True,
            )
        )
        produced |= set(changes(INFO_SERVICE_ID, Metadata=TRACK_METADATA))
        produced |= set(
            changes(
                PRODUCT_SERVICE_ID,
                Standby=True,
                ProductRoom="Kitchen",
                ProductName="Sneaky",
                SourceXml=SOURCE_XML,
                SourceIndex=1,
            )
        )
        self.assertEqual(produced, set(EVENT_KEYS) - set(_LIFECYCLE_KEYS))

    def test_the_subscription_state_key_is_a_device_property(self):
        """Losing a subscription is reported with a key, not an empty dict."""
        self.assertEqual(_LIFECYCLE_KEYS, {"is_subscribed"})
        self.assertIsInstance(Device.is_subscribed, property)
