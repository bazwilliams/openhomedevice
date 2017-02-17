# openhomedevice

Library to provide an API to an existing openhome device. The device needs to have been discovered first by something like netdisco (https://github.com/home-assistant/netdisco).

## Installation

`pip install openhomedevice`

## API

### Constuctor

```python
Device(location)
```

### Methods

#### Control

```python

    SetStandby(standbyRequested) #bool
    Play() #starts playback
    Stop() #stops playback
    Pause() #pauses playback
    Skip(offset) #positive or negative integer
    SetVolumeLevel(volumeLevel) #positive number
    IncreaseVolume() #increase volume by 1
    DecreaseVolume() #decrease volume by 1
    SetMute(muteRequested) #bool
    SetSource(index) #positive integer (use Sources() for indices)
```

#### Informational

```python
    Uuid() #Unique identifier
    Name() #Name of device
    Room() #Name of room
    IsInStandby() #returns true if in standby
    TransportState() #returns one of Stopped, Playing, Paused or Buffering.
    VolumeLevel() #returns the volume setting
    IsMuted() #returns true if muted
    Source() #returns the currently connected source as a dictionary
    Sources() #returns an array of source dictionaries with indices
    TrackInfo() #returns a track dictionary
```

##### Source Response

```python
{
    'type': 'Playlist',
    'name': 'Playlist'
}
```

##### Sources Response

```python
[
    { 'index': 0, 'type': 'Playlist', 'name': 'Playlist' }, 
    { 'index': 1, 'type': 'Radio', 'name': 'Radio' }, 
    { 'index': 3, 'type': 'Receiver', 'name': 'Songcast' }, 
    { 'index': 6, 'type': 'Analog', 'name': 'Front Aux' }
]
```

##### TrackInfo Response

```python
{
    'album': 'DROGAS Light',
    'artist': 'Lupe Fiasco',
    'albumArt': 'https://resources.tidal.com/images/c8333ef0/ae18/4464/9a69/b99401b82ed7/320x320.jpg',
    'title': 'Dopamine Lit (Intro)'
}
```

## Example

```python
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
        print("NAME     : %s" % openhomeDevice.Name())
        print("ROOM     : %s" % openhomeDevice.Room())
        print("UUID     : %s" % openhomeDevice.Uuid())
        print("SOURCE   : %s" % openhomeDevice.Source())
        print("STANDBY  : %s" % openhomeDevice.IsInStandby())
        print("STATE    : %s" % openhomeDevice.TransportState())
        print("TRACK    : %s" % openhomeDevice.TrackInfo())
        print("VOLUME   : %s" % openhomeDevice.VolumeLevel())
        print("MUTED    : %s" % openhomeDevice.IsMuted())
        print("SOURCES  : %s" % openhomeDevice.Sources())
    print("----")
```
