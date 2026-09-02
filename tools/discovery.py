"""Find Openhome devices on the local network.

A development helper, deliberately kept out of the installed package: there is
no __init__.py here, so setuptools does not pick it up.

Run it to print a locations list ready to paste into demo.py:

    python tools/discovery.py
"""

import asyncio
import sys
import os

from async_upnp_client.search import SSDP_ST_ALL, async_search

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openhomedevice.device import Device  # noqa: E402

OPENHOME_PRODUCT = "urn:av-openhome-org:service:Product:1"
OPENHOME_SENDER = "urn:av-openhome-org:service:Sender:1"
OPENHOME_RECEIVER = "urn:av-openhome-org:service:Receiver:1"


async def discover_locations(timeout=5, search_target=OPENHOME_PRODUCT):
    """Search the local network for Openhome devices.

    Returns a list of device description urls, de-duplicated by UDN because a
    device answers a search once per interface. Searching for the ':1' service
    version also matches devices implementing later versions.
    """
    locations = {}

    async def on_response(headers):
        location = headers.get("LOCATION")
        usn = headers.get("USN")
        if not location or not usn:
            return

        # Some devices answer every M-SEARCH regardless of what was asked for.
        # A device that does implement the service echoes back the searched
        # target, including when it implements a later version of it.
        if search_target != SSDP_ST_ALL and headers.get("ST") != search_target:
            return

        locations.setdefault(usn.split("::")[0], location)

    await async_search(
        async_callback=on_response, timeout=timeout, search_target=search_target
    )

    return list(locations.values())


async def discover(timeout=5, search_target=OPENHOME_PRODUCT):
    """Search the local network and return initialised Devices.

    Devices that answer the search but cannot be reached over http, such as one
    on a link-local address, are skipped rather than failing the whole search.
    """
    devices = []
    for location in await discover_locations(timeout, search_target):
        device = Device(location)
        try:
            await device.init()
        except Exception:
            continue
        devices.append(device)
    return devices


async def main():
    devices = await discover()
    print("    locations = [")
    for device in sorted(devices, key=lambda d: d.friendly_name()):
        print('        "%s",  # %s' % (device.location, await device.room()))
    print("    ]")


if __name__ == "__main__":
    asyncio.run(main())
