def didlLiteString(track_details):
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
