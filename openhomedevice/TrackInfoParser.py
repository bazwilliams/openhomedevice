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

        trackDetails["type"] = self.TrackDetailBuilder(itemElement, "upnp:class", False, False)
        trackDetails["title"] = self.TrackDetailBuilder(itemElement, "dc:title", False, False)
        trackDetails["uri"] = self.TrackDetailBuilder(itemElement, "DIDL-Lite:res", False, False)
        trackDetails["artist"] = self.TrackDetailBuilder(itemElement, "upnp:artist", False, True)
        trackDetails["composer"] = self.TrackDetailBuilder(itemElement, "upnp:artist[@role='Composer']", False, True)
        trackDetails["narrator"] = self.TrackDetailBuilder(itemElement, "upnp:artist[@role='Narrator']", False, True)
        trackDetails["performer"] = self.TrackDetailBuilder(itemElement, "upnp:artist[@role='Performer']", False, True)
        trackDetails["conductor"] = self.TrackDetailBuilder(itemElement, "upnp:artist[@role='Conductor']", False, True)
        trackDetails["albumArtist"] = self.TrackDetailBuilder(itemElement, "upnp:artist[@role='AlbumArtist']", False, True)
        trackDetails["genre"] = self.TrackDetailBuilder(itemElement, "upnp:genre", False, True)
        trackDetails["albumGenre"] = self.TrackDetailBuilder(itemElement, "upnp:genre", False, True)
        trackDetails["albumTitle"] = self.TrackDetailBuilder(itemElement, "upnp:album", False, False)
        trackDetails["albumArtwork"] = self.TrackDetailBuilder(itemElement, "upnp:albumArtURI", False, False)
        trackDetails["artwork"] = self.TrackDetailBuilder(itemElement, "upnp:artworkURI", False, False)
        trackDetails["year"] = self.TrackDetailBuilder(itemElement, "dc:date", True, False)
        trackDetails["disc"] = self.TrackDetailBuilder(itemElement, "upnp:originalDiscNumber", True, False)
        trackDetails["discs"] = self.TrackDetailBuilder(itemElement, "upnp:originalDiscCount", True, False)
        trackDetails["track"] = self.TrackDetailBuilder(itemElement, "upnp:originalTrackNumber", True, False)
        trackDetails["tracks"] = self.TrackDetailBuilder(itemElement, "upnp:originalTrackCount", True, False)
        trackDetails["author"] = self.TrackDetailBuilder(itemElement, "dc:author", False, True)
        trackDetails["publisher"] = self.TrackDetailBuilder(itemElement, "dc:publisher", False, False)
        trackDetails["published"] = self.TrackDetailBuilder(itemElement, "dc:published", False, False)
        trackDetails["description"] = self.TrackDetailBuilder(itemElement, "dc:description", False, False)
        trackDetails["rating"] = self.TrackDetailBuilder(itemElement, "upnp:rating", False, False)
        trackDetails["channels"] = self.ParseInt(self.TrackDetailAttributeBuilder(itemElement, "DIDL-Lite:res", "nrAudioChannels"))
        trackDetails["bitDepth"] = self.ParseInt(self.TrackDetailAttributeBuilder(itemElement, "DIDL-Lite:res", "bitsPerSample"))
        trackDetails["sampleRate"] = self.ParseInt(self.TrackDetailAttributeBuilder(itemElement, "DIDL-Lite:res", "sampleFrequency"))
        trackDetails["bitRate"] = self.ParseInt(self.TrackDetailAttributeBuilder(itemElement, "DIDL-Lite:res", "bitrate"))
        trackDetails["duration"] = self.ParseInt(self.TrackDetailAttributeBuilder(itemElement, "DIDL-Lite:res", "duration"))
        trackDetails["mimeType"] = self.TrackDetailAttributeBuilder(itemElement, "DIDL-Lite:res", "protocolInfo")
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

    def ParseInt(self, value):
        intFinder = re.compile('\d+')

        if value != None:
            numbers = intFinder.findall(value)
            if (len(numbers) > 0):
                parsedValue = numbers[0]


    def TrackDetailAttributeBuilder(self, itemElement, itemKey, itemAttribute):
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

    def TrackDetailBuilder(self, itemElement, itemKey, isNumber, isArray):
        intFinder = re.compile('\d+')

        namespaces = {
                'DIDL-Lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/',
		'upnp': 'urn:schemas-upnp-org:metadata-1-0/upnp/',
                'dc': 'http://purl.org/dc/elements/1.1/'
	}

        value = itemElement.find(itemKey, namespaces)
        parsedValue = None

        if value != None:
            if isNumber:
                numbers = intFinder.findall(value.text)
                if (len(numbers) > 0):
                    parsedValue = numbers[0]
            else:
                parsedValue = value.text

        if isArray:
            values = []
            if parsedValue != None:
                values.append(parsedValue)
            return values
        else:
            return parsedValue
