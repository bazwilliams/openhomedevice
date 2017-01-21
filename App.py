from openhomedevice.Device import Device

if __name__ == '__main__':
    locations = [
        "http://192.168.1.122:55178/4c494e4e-0026-0f21-fd5a-01387403013f/Upnp/device.xml",
        "http://192.168.1.124:55178/4c494e4e-0026-0f21-f15c-01373197013f/Upnp/device.xml",
        "http://192.168.1.157:55178/4c494e4e-0026-0f21-d74b-01333078013f/Upnp/device.xml",
        "http://192.168.1.228:55178/4c494e4e-0026-0f21-bf92-01303737013f/Upnp/device.xml"
    ]

    for location in locations:
        openhomeDevice = Device(location)
        print("----")
        print("NAME     : %s" % openhomeDevice.FriendlyName())
        print("UUID     : %s" % openhomeDevice.Uuid())
        print("SOURCE   : %s" % openhomeDevice.Source())
        print("STANDBY  : %s" % openhomeDevice.IsInStandby())
        print("STATE    : %s" % openhomeDevice.TransportState())
        print("TRACK    : %s" % openhomeDevice.TrackInfo())
        print("VOLUME   : %s" % openhomeDevice.VolumeLevel())
        print("MUTED    : %s" % openhomeDevice.IsMuted())
    print("----")
