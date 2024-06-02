import re

import xml.etree.ElementTree as etree


def generate_string(track_details):
    title = track_details.get("title", "") or ""
    uri = track_details.get("uri", "") or ""
    albumArtwork = track_details.get("albumArtwork", "") or ""

    return (
        '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" '
        'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">'
        '<item id="" parentID="" restricted="True">'
        "<dc:title>{0}</dc:title>"
        '<res protocolInfo="*:*:*:*">{1}</res>'
        "<upnp:albumArtURI>{2}</upnp:albumArtURI>"
        "<upnp:class>object.item.audioItem</upnp:class>"
        "</item>"
        "</DIDL-Lite>".format(title, uri, albumArtwork)
    )


def parse(metadata):
    track_details = {}

    if metadata is None:
        return track_details

    try:
        et = etree.fromstring(metadata).find(
            "DIDL-Lite:item",
            {"DIDL-Lite": "urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"},
        )
    except:
        return track_details

    if et is None:
        return track_details

    track_details["type"] = find_element_value(et, "upnp:class", False)
    track_details["title"] = find_element_value(et, "dc:title", False)
    track_details["uri"] = find_element_value(et, "DIDL-Lite:res", False)
    track_details["artist"] = find_element_value(et, "upnp:artist", True)
    track_details["composer"] = find_element_value(
        et, "upnp:artist[@role='Composer']", True
    )
    track_details["narrator"] = find_element_value(
        et, "upnp:artist[@role='Narrator']", True
    )
    track_details["performer"] = find_element_value(
        et, "upnp:artist[@role='Performer']", True
    )
    track_details["conductor"] = find_element_value(
        et, "upnp:artist[@role='Conductor']", True
    )
    track_details["albumArtist"] = find_element_value(
        et, "upnp:artist[@role='AlbumArtist']", True
    )
    track_details["genre"] = find_element_value(et, "upnp:genre", True)
    track_details["albumGenre"] = find_element_value(et, "upnp:genre", True)
    track_details["albumTitle"] = find_element_value(et, "upnp:album", False)
    track_details["albumArtwork"] = find_element_value(et, "upnp:albumArtURI", False)
    track_details["artwork"] = find_element_value(et, "upnp:artworkURI", False)
    track_details["year"] = parse_int(find_element_value(et, "dc:date", False))
    track_details["disc"] = parse_int(
        find_element_value(et, "upnp:originalDiscNumber", False)
    )
    track_details["discs"] = parse_int(
        find_element_value(et, "upnp:originalDiscCount", False)
    )
    track_details["track"] = parse_int(
        find_element_value(et, "upnp:originalTrackNumber", False)
    )
    track_details["tracks"] = parse_int(
        find_element_value(et, "upnp:originalTrackCount", False)
    )
    track_details["author"] = find_element_value(et, "dc:author", True)
    track_details["publisher"] = find_element_value(et, "dc:publisher", False)
    track_details["published"] = find_element_value(et, "dc:published", False)
    track_details["description"] = find_element_value(et, "dc:description", False)
    track_details["rating"] = find_element_value(et, "upnp:rating", False)
    track_details["channels"] = parse_int(
        find_element_attribute_value(et, "DIDL-Lite:res", "nrAudioChannels")
    )
    track_details["bitDepth"] = parse_int(
        find_element_attribute_value(et, "DIDL-Lite:res", "bitsPerSample")
    )
    track_details["sampleRate"] = parse_int(
        find_element_attribute_value(et, "DIDL-Lite:res", "sampleFrequency")
    )
    track_details["bitRate"] = parse_int(
        find_element_attribute_value(et, "DIDL-Lite:res", "bitrate")
    )
    track_details["duration"] = parse_duration(
        find_element_attribute_value(et, "DIDL-Lite:res", "duration")
    )
    track_details["mimeType"] = find_element_attribute_value(
        et, "DIDL-Lite:res", "protocolInfo"
    )
    #    "provider": "{provider}" // oh:provider
    #    "work": "{work}" // oh:work
    #    "movement": "{movement}" // oh:movement
    #    "show": "{show}" // oh:show
    #    "episode": {episode} // oh:episodeNumber
    #    "episodes": {episodes} // oh:episodeCount
    #    "website": "{website}" // oh:website
    #    "location": "{location}" // oh:location // ISO 6709
    #    "details": "{details}" // oh:details
    #    "extensions": "{extensions}" // oh:extensions // stringified json

    return track_details


def parse_duration(value):
    if value == None:
        return None

    intFinder = re.compile(r"\d+")
    numbers = intFinder.findall(value.split(".")[0])

    if len(numbers) == 3:
        return int(numbers[2]) + (int(numbers[1]) * 60) + (int(numbers[0]) * 360)
    if len(numbers) == 2:
        return int(numbers[1]) + (int(numbers[0]) * 60)
    if len(numbers) == 1:
        return int(numbers[0])

    return None


def parse_int(value):
    if value == None:
        return None

    intFinder = re.compile(r"\d+")
    numbers = intFinder.findall(value)
    if len(numbers) > 0:
        return int(numbers[0])

    return None


def find_element_attribute_value(et, itemKey, itemAttribute):
    namespaces = {
        "DIDL-Lite": "urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/",
        "upnp": "urn:schemas-upnp-org:metadata-1-0/upnp/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    value = et.find(itemKey, namespaces)
    parsedValue = None

    if value != None:
        attribute = value.attrib.get(itemAttribute, None)
        if attribute != None:
            parsedValue = attribute

    return parsedValue


def find_element_value(et, itemKey, isArray):
    namespaces = {
        "DIDL-Lite": "urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/",
        "upnp": "urn:schemas-upnp-org:metadata-1-0/upnp/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    items = et.findall(itemKey, namespaces)

    parsedValue = None

    if len(items) > 0:
        parsedValue = items[0].text

    if isArray:
        values = set()
        array = []
        if len(items) > 0:
            for i in items:
                value = i.text
                if value and value not in values:
                    values.add(i.text)
                    array.append(i.text)
        return list(array)
    else:
        return parsedValue
