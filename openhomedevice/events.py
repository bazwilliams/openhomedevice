"""Translation of device events into this library's own vocabulary.

Each key is named for the Device method returning the same value, which a
test asserts over EVENT_KEYS. Variables this library does not map are
dropped. The names below are stable across Product:1-4 and Volume:1-4.
"""

from xml.etree.ElementTree import ParseError

import openhomedevice.didl_lite as didl_lite
import openhomedevice.source_list as source_list

from openhomedevice.services import (
    INFO_SERVICE_ID,
    PRODUCT_SERVICE_ID,
    TRANSPORT_SERVICE_ID,
    VOLUME_SERVICE_ID,
)

# Variables that map straight onto a key. The rest are handled in translate.
_SIMPLE_VARIABLES = {
    PRODUCT_SERVICE_ID: {
        "Standby": "is_in_standby",
        "ProductRoom": "room",
        "ProductName": "name",
    },
    VOLUME_SERVICE_ID: {
        "Volume": "volume",
        "Mute": "is_muted",
    },
    TRANSPORT_SERVICE_ID: {
        "TransportState": "transport_state",
        "CanPause": "can_pause",
        "CanSkipNext": "can_skip_next",
        "CanSkipPrevious": "can_skip_previous",
    },
}

# Produced in translate() rather than by the table above.
_DERIVED_KEYS = frozenset({"source", "sources", "track_info"})

# Reported by the Device rather than translated from a variable.
_LIFECYCLE_KEYS = frozenset({"is_subscribed"})

_TRANSLATED_KEYS = (
    frozenset(key for mapping in _SIMPLE_VARIABLES.values() for key in mapping.values())
    | _DERIVED_KEYS
)

# Every key an event can carry.
EVENT_KEYS = _TRANSLATED_KEYS | _LIFECYCLE_KEYS


class EventTranslator:
    """Turns state variable changes into the keys this library reports.

    Stateful because a source is an index plus a list, and the device sends
    them in separate events. Both are remembered so either one arriving
    resolves a source without asking the device for the other.
    """

    def __init__(self):
        self._source_list = []
        self._source_index = None

    def translate(self, service_id, state_variables):
        changes = {}
        simple = _SIMPLE_VARIABLES.get(service_id, {})
        source_moved = False

        for state_variable in state_variables:
            name = state_variable.name
            value = state_variable.value

            if name in simple:
                changes[simple[name]] = value
            elif service_id == PRODUCT_SERVICE_ID and name == "SourceIndex":
                # Remembered, not reported: source() answers with name and type.
                self._source_index = value
                source_moved = True
            elif service_id == PRODUCT_SERVICE_ID and name == "SourceXml":
                sources = self._parse_sources(value)
                if sources is not None:
                    self._source_list = sources
                    changes["sources"] = source_list.visible(sources)
                    source_moved = True
            elif service_id == INFO_SERVICE_ID and name == "Metadata":
                changes["track_info"] = didl_lite.parse(value)

        if source_moved:
            source = self._current_source()
            if source is not None:
                changes["source"] = source

        return changes

    @staticmethod
    def _parse_sources(source_xml):
        try:
            return source_list.parse(source_xml)
        except (ParseError, TypeError, AttributeError):
            return None

    def _current_source(self):
        for source in self._source_list:
            if source["index"] == self._source_index:
                return {"type": source["type"], "name": source["name"]}
        return None
