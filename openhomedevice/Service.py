import re
import socket
import xml.etree.ElementTree as etree


class Service:
    """Info for a particular service - namely the stuff contained in the XML description files."""

    def __init__(self, aParentDevice, aServElem, aServNs):
        self.iParentDevice = aParentDevice

        self.iType = aServElem.find("{%s}serviceType" % (aServNs)).text
        self.iId = aServElem.find("{%s}serviceId" % (aServNs)).text
        self.iScpdUrl = aServElem.find("{%s}SCPDURL" % (aServNs)).text
        self.iControlUrl = aServElem.find("{%s}controlURL" % (aServNs)).text
        try:
            self.iEventSubUrl = aServElem.find("{%s}eventSubURL" % (aServNs)).text
        except:
            self.iEventSubUrl = None

        self.iActionList = []
        self.iStateVarList = []

        # Make sure the relative URLs have a '/' at the front
        if self.iScpdUrl[0:7] != "http://":
            if self.iScpdUrl[0] != "/":
                self.iScpdUrl = self.iParentDevice.UrlBase() + "/" + self.iScpdUrl
            else:
                self.iScpdUrl = self.iParentDevice.UrlBase() + self.iScpdUrl

        if self.iControlUrl[0:7] != "http://":
            if self.iControlUrl[0] != "/":
                self.iControlUrl = self.iParentDevice.UrlBase() + "/" + self.iControlUrl
            else:
                self.iControlUrl = self.iParentDevice.UrlBase() + self.iControlUrl

        if self.iEventSubUrl and self.iEventSubUrl[0:7] != "http://":
            if self.iEventSubUrl[0] != "/":
                self.iEventSubUrl = (
                    self.iParentDevice.UrlBase() + "/" + self.iEventSubUrl
                )
            else:
                self.iEventSubUrl = self.iParentDevice.UrlBase() + self.iEventSubUrl

    def __str__(self):
        servStr = "\t" + "SERVICE:\r\n"
        servStr += "\t" + "TYPE       : " + self.iType + "\r\n"
        servStr += "\t" + "ID         : " + self.iId + "\r\n"
        servStr += "\t" + "SCPD URL   : " + self.ScpdUrl() + "\r\n"
        servStr += "\t" + "CONTROL URL: " + self.ControlUrl() + "\r\n"
        if self.iEventSubUrl:
            servStr += "\t" + "EVENT URL  : " + self.EventSubUrl() + "\r\n"
        return servStr

    def Type(self):
        return self.iType

    def Id(self):
        return self.iId

    def ScpdUrl(self):
        return self.iScpdUrl

    def ControlUrl(self):
        return self.iControlUrl

    def EventSubUrl(self):
        return self.iEventSubUrl

    def StateVarList(self):
        return self.iStateVarList

    def ActionList(self):
        return self.iActionList

    def ParseXmlDesc(self, aXmlDesc):
        "Parse the service description XML file." ""

        scpd = etree.fromstring(aXmlDesc)
        ns = scpd.tag[1:].split("}")[0]

        # State Variables
        stateVars = scpd.find("{%s}serviceStateTable" % (ns))
        if stateVars is not None:
            for stateVar in stateVars.getchildren():
                name = stateVar.find("{%s}name" % (ns)).text
                type = stateVar.find("{%s}dataType" % (ns)).text
                sendEvs = stateVar.attrib["sendEvents"]
                try:
                    default = stateVar.find("{%s}defaultValue" % (ns)).text
                except:
                    default = None

                sv = StateVariable(self, name, type)
                if default:
                    sv.SetDefaultValue(default)

                if sendEvs == "yes":
                    sv.SetEvented(1)
                else:
                    sv.SetEvented(0)

                allowedVals = stateVar.find("{%s}allowedValueList" % (ns))
                if allowedVals is not None:
                    for allowedVal in allowedVals.getchildren():
                        sv.AddAllowedValue(allowedVal.text)

                allowedValRange = stateVar.find("{%s}allowedValueRange" % (ns))
                if allowedValRange is not None:
                    min = allowedValRange.find("{%s}minimum" % (ns)).text
                    max = allowedValRange.find("{%s}maximum" % (ns)).text
                    try:
                        step = allowedValRange.find("{%s}step" % (ns)).text
                    except:
                        step = "1"
                    sv.SetAllowedValueRange(min, max, step)

                self.iStateVarList.append(sv)

        # Actions
        actions = scpd.find("{%s}actionList" % (ns))
        if actions is not None:
            for act in actions.getchildren():
                name = act.find("{%s}name" % (ns)).text
                action = Action(self, name)

                arguments = act.find("{%s}argumentList" % (ns))
                if arguments is not None:
                    for argument in arguments.getchildren():
                        name = argument.find("{%s}name" % (ns)).text
                        dir = argument.find("{%s}direction" % (ns)).text
                        arg = Argument(action, name, dir)

                        rsv = argument.find("{%s}relatedStateVariable" % (ns)).text
                        for sv in self.iStateVarList:
                            if rsv == sv.Name():
                                arg.SetRelatedStateVar(sv)
                                break

                self.iActionList.append(action)


class Action:
    """An action belonging to a service."""

    def __init__(self, aParent, aName):
        self.iParent = aParent
        self.iName = aName
        self.iArgList = []

    def AddArg(self, aArg):
        self.iArgList.append(aArg)

    def Name(self):
        return self.iName

    def ArgList(self):
        return self.iArgList


class Argument:
    """An argument of an action."""

    def __init__(self, aParent, aName, aDir):
        self.iParent = aParent
        self.iName = aName
        self.iDir = aDir
        self.iRsv = None
        self.iParent.AddArg(self)

    def Name(self):
        return self.iName

    def Direction(self):
        return self.iDir

    def RelatedStateVar(self):
        return self.iRsv

    def Type(self):
        if self.iRsv:
            return self.iRsv.Type()
        else:
            return None

    def SetRelatedStateVar(self, aRsv):
        self.iRsv = aRsv


class StateVariable:
    """A service state variable."""

    def __init__(self, aParent, aName, aType):
        self.iParent = aParent
        self.iName = aName
        self.iType = aType
        self.iDefaultValue = None
        self.iAllowedValueList = None
        self.iAllowedRangeMin = None
        self.iAllowedRangeMax = None
        self.iAllowedRangeStep = None
        self.iIsEvented = 0

    def SetEvented(self, aIsEvented):
        self.iIsEvented = aIsEvented

    def SetDefaultValue(self, aDefVal):
        self.iDefaultValue = aDefVal

    def AddAllowedValue(self, aVal):
        if self.iAllowedValueList == None:
            self.iAllowedValueList = []
        self.iAllowedValueList.append(aVal)

    def SetAllowedValueRange(self, aMin, aMax, aStep):
        self.iAllowedRangeMin = aMin
        self.iAllowedRangeMax = aMax
        self.iAllowedRangeStep = aStep

    def IsEvented(self):
        return self.iIsEvented

    def Name(self):
        return self.iName

    def Type(self):
        return self.iType

    def DefaultValue(self):
        return self.iDefaultValue

    def AllowedValueList(self):
        return self.iAllowedValueList

    def AllowedValueRange(self):
        return (self.iAllowedRangeMin, self.iAllowedRangeMax, self.iAllowedRangeStep)
