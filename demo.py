import asyncio
from openhomedevice.device import Device


async def main():
    locations = [
        # "http://192.168.1.32:53101/OsxPlayer-barrys-imac.local/Upnp/device.xml",
        "http://192.168.1.36:55178/4c494e4e-0026-0f21-f15c-01373197013f/Upnp/device.xml",
        "http://192.168.1.173:55178/4c494e4e-0026-0f21-e768-01357060013f/Upnp/device.xml",
    ]

    devices = []

    for location in locations:
        device = Device(location)
        await device.init()
        devices.append(device)

        # await device.setup_subscriptions()
        print("----")
        print("NAME     : %s" % await device.name())
        print("ROOM     : %s" % await device.room())
        print("UUID     : %s" % device.uuid())
        print("MANUFACT : %s" % device.manufacturer())
        print("MODEL    : %s" % device.model_name())
        print("FRIENDLY : %s" % device.friendly_name())
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
        print("SOFTWARE : %s" % await device.software_status())
        print("SENDS    : %s" % device.songcast_sender_enabled)
        print("SND STAT : %s" % await device.songcast_sender_status())
        print("SND AUDIO: %s" % await device.songcast_sender_audio())
        print("SENDER   : %s" % await device.songcast_sender())
        print("RECEIVES : %s" % device.songcast_receiver_enabled)
        print("FOLLOWING: %s" % await device.songcast_receiver_sender())
        print("RCV STATE: %s" % await device.songcast_receiver_transport_state())

        # await device.check_latest_firmware()
        # await device.update_firmware()

        await device.set_standby(False)
        await device.set_volume(30)
        await device.increase_volume()
        await device.decrease_volume()
        await device.set_mute(True)
        await device.set_mute(False)
        await device.play_media(
            {
                "uri": "http://opml.radiotime.com/Tune.ashx?id=s50646"
                "&formats=mp3,aac,ogg,hls&partnerId=ah2rjr68"
                "&username=linnproducts&c=ebrowse"
            }
        )
        await asyncio.sleep(4)
        print("TRACK    : %s" % await device.track_info())
        print("STATE    : %s" % await device.transport_state())
        await device.pause()
        await device.play()
        await device.invoke_pin(1)
        await asyncio.sleep(4)
        print("TRACK    : %s" % await device.track_info())
        print("STATE    : %s" % await device.transport_state())
        await device.skip(2)
        await asyncio.sleep(0.5)
        print("TRACK    : %s" % await device.track_info())
        print("STATE    : %s" % await device.transport_state())
        await device.stop()
        await device.set_source(0)
        await device.set_source(1)
        print("SOURCE   : %s" % await device.source())

        await device.set_standby(True)
        print("STANDBY  : %s" % await device.is_in_standby())

    print("----")

    # Songcast: make the last device follow the first one.
    sender = await devices[0].songcast_sender()
    receiver = devices[-1]

    print("SENDER   : %s" % sender)

    await receiver.songcast_receiver_join(sender)
    await asyncio.sleep(5)
    print("SOURCE   : %s" % await receiver.source())
    print("FOLLOWING: %s" % await receiver.songcast_receiver_sender())
    print("RCV STATE: %s" % await receiver.songcast_receiver_transport_state())

    await receiver.songcast_receiver_leave()
    await receiver.set_standby(True)
    print("FOLLOWING: %s" % await receiver.songcast_receiver_sender())

    print("----")


asyncio.run(main())
