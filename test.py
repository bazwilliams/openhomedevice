import asyncio
from openhomedevice.Device import Device

async def main():
    locations = [
        "http://192.168.1.12:55178/4c494e4e-0026-0f21-f15c-01373197013f/Upnp/device.xml"
    ]

    for location in locations:
        openhomeDevice = Device(location)
        await openhomeDevice.init()
        
        print("----")
        print("NAME     : %s" % await openhomeDevice.name())
        print("ROOM     : %s" % await openhomeDevice.room())
        print("UUID     : %s" % await openhomeDevice.uuid())
        print("SOURCE   : %s" % await openhomeDevice.source())
        print("STANDBY  : %s" % await openhomeDevice.is_in_standby())
        print("STATE    : %s" % await openhomeDevice.transport_state())
        print("TRACK    : %s" % await openhomeDevice.track_info())
        print("HAS VOL  : %s" % await openhomeDevice.volume_enabled())
        print("VOLUME   : %s" % await openhomeDevice.volume_level())
        print("MUTED    : %s" % await openhomeDevice.is_muted())
        print("SOURCES  : %s" % await openhomeDevice.sources())
        print("PINS     : %s" % await openhomeDevice.pins())
    print("----")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
