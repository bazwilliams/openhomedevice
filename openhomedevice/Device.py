import requests

from Upnp.Device import RootDevice
from Upnp.Soap import soapRequest

import xml.etree.ElementTree as etree

class Device(object):

    def __init__(self, location):
        xmlDesc = requests.get(location).text.encode('utf-8')
        self.rootDevice = RootDevice(xmlDesc, location)

    def FriendlyName(self):
        return self.rootDevice.Device().FriendlyName()

    def StandbyState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        standbyState = soapRequest(service.ControlUrl(), service.Type(), "Standby", "")
        
        standbyStateXml = etree.fromstring(standbyState)
        return standbyStateXml[0].find("{urn:av-openhome-org:service:Product:2}StandbyResponse/Value").text.encode('utf-8') == "true"

    def RadioTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Radio")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{urn:av-openhome-org:service:Radio:1}TransportStateResponse/Value").text.encode('utf-8')

    def PlaylistTransportState(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Playlist")
        transportState = soapRequest(service.ControlUrl(), service.Type(), "TransportState", "")

        transportStateXml = etree.fromstring(transportState)
        return transportStateXml[0].find("{urn:av-openhome-org:service:Playlist:1}TransportStateResponse/Value").text.encode('utf-8')

    def TransportState(self):
        source = self.Source()
        if (source["type"] == "Radio"):
            return self.RadioTransportState()
        if (source["type"] == "Playlist"):
            return self.PlaylistTransportState()
        return ""

    def Source(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Product")
        source = soapRequest(service.ControlUrl(), service.Type(), "SourceIndex", "")

        sourceXml = etree.fromstring(source)
        sourceIndex = sourceXml[0].find("{urn:av-openhome-org:service:Product:2}SourceIndexResponse/Value").text.encode('utf-8')

        sourceInfo = soapRequest(service.ControlUrl(), service.Type(), "Source", ("<Index>%s</Index>" % sourceIndex))
        sourceInfoXml = etree.fromstring(sourceInfo)

        sourceName = sourceInfoXml[0].find("{urn:av-openhome-org:service:Product:2}SourceResponse/Name").text.encode('utf-8')
        sourceType = sourceInfoXml[0].find("{urn:av-openhome-org:service:Product:2}SourceResponse/Type").text.encode('utf-8')
        
        return {
            "type": sourceType,
            "name": sourceName
        }

    def TrackInfo(self):
        service = self.rootDevice.Device().Service("urn:av-openhome-org:serviceId:Info")
        trackInfo = soapRequest(service.ControlUrl(), service.Type(), "Track", "")
        
        trackInfoXml = etree.fromstring(trackInfo)
        metadata = trackInfoXml[0][0].find('Metadata').text.encode('utf-8')

        metadataXml = etree.fromstring(metadata)
        itemElement = metadataXml.find("{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}item")
        
        albumArt = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}albumArtURI")
        album = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}album")
        artist = itemElement.find("{urn:schemas-upnp-org:metadata-1-0/upnp/}artist")
        title = itemElement.find("{http://purl.org/dc/elements/1.1/}title")

        trackDetails = {}

        trackDetails['title'] =  title.text.encode('utf-8') if title != None else None    
        trackDetails['album'] =  album.text.encode('utf-8') if album != None else None
        trackDetails['albumArt'] =  albumArt.text.encode('utf-8') if albumArt != None else None
        trackDetails['artist'] =  artist.text.encode('utf-8') if artist != None else None

        return trackDetails

    def listStateVars(self, serviceId):
        service = self.rootDevice.Device.Service(serviceId)
        service.ParseXmlDesc(requests.get(service.ScpdUrl()).text)
        for stateVar in service.StateVarList():
            print stateVar.Name()

    def listActionVars(self, serviceId):
        service = self.rootDevice.Device.Service(serviceId)
        service.ParseXmlDesc(requests.get(service.ScpdUrl()).text)
        for action in service.ActionList():
            print action.Name()
