import xml.etree.ElementTree as etree


def _is_visible(element):
    """Linn writes <Visible>true</Visible>, AURALiC writes <Visible>1</Visible>."""
    if element is None:
        return False
    return (element.text or "").strip().lower() in ("true", "1")


def parse(source_xml):
    """The index counts hidden sources, because SourceIndex does."""
    sources = []
    for index, source in enumerate(etree.fromstring(source_xml)):
        sources.append(
            {
                "index": index,
                "name": source.find("Name").text,
                "type": source.find("Type").text,
                "visible": _is_visible(source.find("Visible")),
            }
        )
    return sources


def visible(source_list):
    return [
        {"index": source["index"], "name": source["name"], "type": source["type"]}
        for source in source_list
        if source["visible"]
    ]
