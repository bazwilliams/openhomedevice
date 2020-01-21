def soapRequest(location, service, fnName, fnParams):
    import requests

    bodyString = '<?xml version="1.0"?>'
    bodyString += '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
    bodyString += (
        '  <s:Body s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    )
    bodyString += "    <u:" + fnName + ' xmlns:u="' + service + '">'
    bodyString += "      " + fnParams
    bodyString += "    </u:" + fnName + ">"
    bodyString += "  </s:Body>"
    bodyString += "</s:Envelope>"

    headers = {
        "Content-Type": "text/xml",
        "Accept": "text/xml",
        "SOAPAction": '"' + service + "#" + fnName + '"',
    }

    res = requests.post(location, data=bodyString, headers=headers)
    res.encoding = "utf-8"

    return res.text.encode("utf-8")
