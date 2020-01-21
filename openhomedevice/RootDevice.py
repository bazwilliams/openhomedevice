import re
from openhomedevice import Service
import xml.etree.ElementTree as etree
from threading import Thread


class RootDevice:
    def __init__(self, aDevDescXml, aLocation):
        self.iLocation = aLocation
        self.iUrlBase = None
        self.iDevice = None

        root = etree.fromstring(aDevDescXml)
        ns = root.tag[1:].split("}")[0]

        # URLBase
        urlBase = root.find("{%s}URLBase" % (ns))
        if urlBase is not None:
            self.iUrlBase = urlBase.text
        else:
            m = re.match("http://([^/]*)(.*$)", aLocation)
            self.iUrlBase = "http://" + m.group(1)
        # Strip off any trailing '/'
        m = re.match("(.*?)(/*$)", self.iUrlBase)
        if m:
            self.iUrlBase = m.group(1)

        # create the root device
        device = root.find("{%s}device" % (ns))
        self.iDevice = Device(device, ns, self)

    def Location(self):
        return self.iLocation

    def SetLocation(self, aLocation):
        self.iLocation = aLocation

    def UrlBase(self):
        return self.iUrlBase

    def Device(self):
        return self.iDevice


class Device:
    """A class representing a UPnP device."""

    def __init__(self, aDevElem, aDevNs, aRootDevice):
        self.iRootDevice = aRootDevice
        self.iServiceList = []
        self.iDeviceList = []

        # deviceType
        try:
            self.iType = aDevElem.find("{%s}deviceType" % (aDevNs)).text
        except:
            self.iType = ""

        # UDN
        try:
            self.iUuid = aDevElem.find("{%s}UDN" % (aDevNs)).text
            if self.iUuid[0:5] == "uuid:":
                self.iUuid = self.iUuid[5:]
        except:
            self.iUuid = ""

        # friendlyName
        try:
            self.iFriendlyName = aDevElem.find("{%s}friendlyName" % (aDevNs)).text
        except:
            self.iFriendlyName = ""

        # serviceList
        serviceList = aDevElem.find("{%s}serviceList" % (aDevNs))
        if serviceList is not None:
            for service in serviceList:
                newServ = Service.Service(self, service, aDevNs)
                self.iServiceList.append(newServ)

        # deviceList
        deviceList = aDevElem.find("{%s}deviceList" % (aDevNs))
        if deviceList:
            for device in deviceList:
                newDev = Device(device, aDevNs, aRootDevice)
                self.iDeviceList.append(newDev)

        # presentationUrl
        try:
            self.iPresentationUrl = aDevElem.find("{%s}presentationURL" % (aDevNs)).text
        except:
            self.iPresentationUrl = ""

    def __str__(self):
        devStr = "DEVICE:\r\n"
        devStr += "UUID        : " + self.Uuid() + "\r\n"
        devStr += "DEV DESC URL: " + self.Location() + "\r\n"
        devStr += "URL BASE    : " + self.UrlBase() + "\r\n"
        for serv in self.iServiceList:
            devStr += str(serv)
        devStr += "\r\n"
        return devStr

    def Uuid(self):
        return self.iUuid

    def Location(self):
        return self.iRootDevice.Location()

    def UrlBase(self):
        return self.iRootDevice.UrlBase()

    def Type(self):
        return self.iType

    def FriendlyName(self):
        return self.iFriendlyName

    def PresentationUrl(self):
        return self.iPresentationUrl

    def SetLocation(self, aLocation):
        self.iRootDevice.SetLocation(aLocation)

    def Service(self, aServId):
        for serv in self.iServiceList:
            if aServId == serv.Id():
                return serv
        return None

    def ServiceList(self):
        return self.iServiceList

    def DeviceList(self):
        return self.iDeviceList

    def FindDevice(self, aUuid):
        if aUuid == self.iUuid:
            return self
        for dev in self.iDeviceList:
            found = dev.FindDevice(aUuid)
            if found != None:
                return found
        return None
