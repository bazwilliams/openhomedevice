import asyncio
from openhomedevice.device import Device
import time

async def main():
    locations = [
        "http://192.168.1.12:55178/4c494e4e-0026-0f21-f15c-01373197013f/Upnp/device.xml"
    ]

    for location in locations:
        device = Device(location)
        await device.init()
        
        print("----")
        print("NAME     : %s" % await device.name())
        print("ROOM     : %s" % await device.room())
        print("UUID     : %s" % device.uuid())
        print("SOURCE   : %s" % await device.source())
        print("STANDBY  : %s" % await device.is_in_standby())
        print("STATE    : %s" % await device.transport_state())
        print("TRACK    : %s" % await device.track_info())
        print("HAS VOL  : %s" % device.volume_enabled)
        print("VOLUME   : %s" % await device.volume())
        print("MUTED    : %s" % await device.is_muted())
        print("SOURCES  : %s" % await device.sources())
        print("HAS PINS : %s" % device.pins_enabled)
        print("PINS     : %s" % await device.pins())


        await device.set_standby(False)
        await device.set_volume(30)
        await device.increase_volume()
        await device.decrease_volume()
        await device.set_mute(True)
        await device.set_mute(False)
        await device.play_media({ "uri": "http://www.radiofeeds.co.uk/wgvirginradioaac.m3u"})
        time.sleep(4)
        print("TRACK    : %s" % await device.track_info())
        print("STATE    : %s" % await device.transport_state())
        await device.pause()
        await device.play()
        await device.invoke_pin(1)
        time.sleep(4)
        print("TRACK    : %s" % await device.track_info())
        print("STATE    : %s" % await device.transport_state())
        await device.skip(2)
        time.sleep(0.5)
        print("TRACK    : %s" % await device.track_info())
        print("STATE    : %s" % await device.transport_state())
        await device.stop()
        await device.set_source(0)
        await device.set_source(1)
        print("SOURCE   : %s" % await device.source())

        await device.set_standby(True)
        print("STANDBY  : %s" % await device.is_in_standby())

    print("----")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
