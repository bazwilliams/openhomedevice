import requests
import re

import xml.etree.ElementTree as etree

class TrackInfoParser(object):

    def __init__(self, trackInfo):
        trackInfoXml = etree.fromstring(trackInfo)
        print trackInfo
        self.metadata = trackInfoXml[0][0].find("Metadata").text

    def TrackInfo(self):

        if self.metadata is None:
            return {}

        metadataXml = etree.fromstring(self.metadata)
        itemElement = metadataXml.find("DIDL-Lite:item", { 'DIDL-Lite': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/' })

        trackDetails = {}

        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:class", "type", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "dc:title", "title", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "DIDL-Lite:res", "uri", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artist", "artist", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artist[@role='Composer']", "composer", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artist[@role='Narrator']", "narrator", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artist[@role='Performer']", "performer", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artist[@role='Conductor']", "conductor", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artist[@role='AlbumArtist']", "albumArtist", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:genre", "genre", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:genre", "albumGenre", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:album", "albumTitle", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:albumArtURI", "albumArtwork", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:artworkURI", "artwork", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "dc:date", "year", True, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:originalDiscNumber", "disc", True, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:originalDiscCount", "discs", True, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:originalTrackNumber", "track", True, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:originalTrackCount", "tracks", True, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "dc:author", "author", False, True)
        self.TrackDetailBuilder(trackDetails, itemElement, "dc:publisher", "publisher", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "dc:published", "published", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "dc:description", "description", False, False)
        self.TrackDetailBuilder(trackDetails, itemElement, "upnp:rating", "rating", False, False)
        self.TrackDetailAttributeBuilder(trackDetails, itemElement, "DIDL-Lite:res", "nrAudioChannels", "channels", True)
        self.TrackDetailAttributeBuilder(trackDetails, itemElement, "DIDL-Lite:res", "bitsPerSample", "bitDepth", True)
        self.TrackDetailAttributeBuilder(trackDetails, itemElement, "DIDL-Lite:res", "sampleFrequency", "sampleRate", True)
        self.TrackDetailAttributeBuilder(trackDetails, itemElement, "DIDL-Lite:res", "bitrate", "bitRate", True)
        self.TrackDetailAttributeBuilder(trackDetails, itemElement, "DIDL-Lite:res", "duration", "duration", True)
        self.TrackDetailAttributeBuilder(trackDetails, itemElement, "DIDL-Lite:res", "protocolInfo", "mimeType", False)
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

    def TrackDetailAttributeBuilder(self, trackDetails, itemElement, itemKey, itemAttribute, targetKey, isNumber):
        intFinder = re.compile('\d+')

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
                if isNumber:
                    numbers = intFinder.findall(attribute)
                    if (len(numbers) > 0):
                        parsedValue = numbers[0]
                else:
                    parsedValue = attribute

        trackDetails[targetKey] = parsedValue

    def TrackDetailBuilder(self, trackDetails, itemElement, itemKey, targetKey, isNumber, isArray):
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
            trackDetails[targetKey] = []
            if parsedValue != None:
                trackDetails[targetKey].append(parsedValue)
        else:
            trackDetails[targetKey] = parsedValue
