import requests
import re

import xml.etree.ElementTree as etree

class TrackInfoParser(object):

    def __init__(self, trackInfo):
        trackInfoXml = etree.fromstring(trackInfo)
        self.metadata = trackInfoXml[0][0].find("Metadata").text

    def TrackInfo(self):

        if self.metadata is None:
            return {}

        metadataXml = etree.fromstring(self.metadata)
        itemElement = metadataXml.find("DIDL-Lite:item", { 'DIDL-Lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/' })

        trackDetails = {}

        trackDetails["type"] = self.FindElementValue(itemElement, "upnp:class", False)
        trackDetails["title"] = self.FindElementValue(itemElement, "dc:title", False)
        trackDetails["uri"] = self.FindElementValue(itemElement, "DIDL-Lite:res", False)
        trackDetails["artist"] = self.FindElementValue(itemElement, "upnp:artist", True)
        trackDetails["composer"] = self.FindElementValue(itemElement, "upnp:artist[@role='Composer']", True)
        trackDetails["narrator"] = self.FindElementValue(itemElement, "upnp:artist[@role='Narrator']", True)
        trackDetails["performer"] = self.FindElementValue(itemElement, "upnp:artist[@role='Performer']", True)
        trackDetails["conductor"] = self.FindElementValue(itemElement, "upnp:artist[@role='Conductor']", True)
        trackDetails["albumArtist"] = self.FindElementValue(itemElement, "upnp:artist[@role='AlbumArtist']", True)
        trackDetails["genre"] = self.FindElementValue(itemElement, "upnp:genre", True)
        trackDetails["albumGenre"] = self.FindElementValue(itemElement, "upnp:genre", True)
        trackDetails["albumTitle"] = self.FindElementValue(itemElement, "upnp:album", False)
        trackDetails["albumArtwork"] = self.FindElementValue(itemElement, "upnp:albumArtURI", False)
        trackDetails["artwork"] = self.FindElementValue(itemElement, "upnp:artworkURI", False)
        trackDetails["year"] = self.ParseInt(self.FindElementValue(itemElement, "dc:date", False))
        trackDetails["disc"] = self.ParseInt(self.FindElementValue(itemElement, "upnp:originalDiscNumber", False))
        trackDetails["discs"] = self.ParseInt(self.FindElementValue(itemElement, "upnp:originalDiscCount", False))
        trackDetails["track"] = self.ParseInt(self.FindElementValue(itemElement, "upnp:originalTrackNumber", False))
        trackDetails["tracks"] = self.ParseInt(self.FindElementValue(itemElement, "upnp:originalTrackCount", False))
        trackDetails["author"] = self.FindElementValue(itemElement, "dc:author", True)
        trackDetails["publisher"] = self.FindElementValue(itemElement, "dc:publisher", False)
        trackDetails["published"] = self.FindElementValue(itemElement, "dc:published", False)
        trackDetails["description"] = self.FindElementValue(itemElement, "dc:description", False)
        trackDetails["rating"] = self.FindElementValue(itemElement, "upnp:rating", False)
        trackDetails["channels"] = self.ParseInt(self.FindElementAttributeValue(itemElement, "DIDL-Lite:res", "nrAudioChannels"))
        trackDetails["bitDepth"] = self.ParseInt(self.FindElementAttributeValue(itemElement, "DIDL-Lite:res", "bitsPerSample"))
        trackDetails["sampleRate"] = self.ParseInt(self.FindElementAttributeValue(itemElement, "DIDL-Lite:res", "sampleFrequency"))
        trackDetails["bitRate"] = self.ParseInt(self.FindElementAttributeValue(itemElement, "DIDL-Lite:res", "bitrate"))
        trackDetails["duration"] = self.ParseDuration(self.FindElementAttributeValue(itemElement, "DIDL-Lite:res", "duration"))
        trackDetails["mimeType"] = self.FindElementAttributeValue(itemElement, "DIDL-Lite:res", "protocolInfo")
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

        return trackDetails

    def ParseDuration(self, value):
        if value == None:
            return None

        intFinder = re.compile('\d+')
        numbers = intFinder.findall(value.split('.')[0])

        if (len(numbers) == 3):
            return int(numbers[2]) + (int(numbers[1]) * 60) + (int(numbers[0]) * 360)
        if (len(numbers) == 2):
            return int(numbers[1]) + (int(numbers[0]) * 60)
        if (len(numbers) == 1):
            return int(numbers[0])

        return None

    def ParseInt(self, value):
        if value == None:
            return None

        intFinder = re.compile('\d+')
        numbers = intFinder.findall(value)
        if (len(numbers) > 0):
            return int(numbers[0])

        return None

    def FindElementAttributeValue(self, itemElement, itemKey, itemAttribute):
        namespaces = {
                'DIDL-Lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
		'upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/',
                'dc': 'http://purl.org/dc/elements/1.1/'
	}

        value = itemElement.find(itemKey, namespaces)
        parsedValue = None

        if value != None:
            attribute = value.attrib.get(itemAttribute, None)
            if attribute != None:
                parsedValue = attribute

        return parsedValue

    def FindElementValue(self, itemElement, itemKey, isArray):
        namespaces = {
                'DIDL-Lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
		'upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/',
                'dc': 'http://purl.org/dc/elements/1.1/'
	}

        items = itemElement.findall(itemKey, namespaces)

        parsedValue = None

        if len(items) > 0:
            parsedValue = items[0].text

        if isArray:
            values = set()
            if len(items) > 0:
                for i in items:
                    value = i.text
                    if value != None:
                        values.add(i.text)
            return list(values)
        else:
            return parsedValue
