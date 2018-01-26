# openhomedevice

Library to provide an API to an existing openhome device. The device needs to have been discovered first by something like netdisco (https://github.com/home-assistant/netdisco).

## Installation

`pip install openhomedevice`

## API

### Constructor

```python
Device(location)
```

### Methods

#### Control

```python
    SetStandby(standbyRequested) #bool
    Play() #starts playback
    PlayMedia(track_details) #start playing `track_details`
    Stop() #stops playback
    Pause() #pauses playback
    Skip(offset) #positive or negative integer
    SetVolumeLevel(volumeLevel) #positive number
    IncreaseVolume() #increase volume by 1
    DecreaseVolume() #decrease volume by 1
    SetMute(muteRequested) #bool
    SetSource(index) #positive integer (use Sources() for indices)
```

#### Configuration

```python
    GetConfigurationKeys() # returns an array of configurable keys
    SetConfiguration(key, value) #set a configuration key to a specific value
    GetConfiguration(key) #returns the value of the configuration key 
```

#### Informational

```python
    Uuid() #Unique identifier
    Name() #Name of device
    Room() #Name of room
    IsInStandby() #returns true if in standby
    TransportState() #returns one of Stopped, Playing, Paused or Buffering.
    VolumeEnabled() #returns true if the volume service is available
    VolumeLevel() #returns the volume setting or None if disabled
    IsMuted() #returns true if muted or None if disabled
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
  "mimeType": "http-get:*:audio/x-flac:DLNA.ORG_OP=01;DLNA.ORG_FLAGS=01700000000000000000000000000000",
  "rating": None,
  "performer": [
    "Fahmi Alqhai, Performer - Johann Sebastian Bach, Composer"
  ],
  "bitDepth": 16,
  "channels": 2,
  "disc": None,
  "composer": [],
  "year": 2017,
  "duration": 460,
  "author": [],
  "albumArtist": [],
  "type": "object.item.audioItem.musicTrack",
  "narrator": [],
  "description": None,
  "conductor": [],
  "albumArtwork": "http://static.qobuz.com/images/covers/58/20/8424562332058_600.jpg",
  "track": 2,
  "tracks": None,
  "artwork": None,
  "genre": [
    "Klassiek"
  ],
  "publisher": "Glossa",
  "albumGenre": [
    "Klassiek"
  ],
  "artist": [
    "Fahmi Alqhai"
  ],
  "bitRate": None,
  "albumTitle": "The Bach Album",
  "uri": "http://192.168.0.110:58050/stream/audio/b362f0f7a1ff33b176bcf2adde75af96.flac",
  "discs": None,
  "published": None,
  "title": "Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba) : Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba): II. Fuga",
  "sampleRate": 44100
}
```

##### Playing A Track

Use this to play a short audio track, a podcast Uri or radio station Uri. The audio will be played using the radio source of the device. The `trackDetails` object should be the same as the one described in the `TrackInfo` section above. 

```python
    trackDetails = {}
    trackDetails["uri"] = "http://opml.radiotime.com/Tune.ashx?id=s122119"
    trackDetails["title"] = 'Linn Radio (Eclectic Music)'
    trackDetails["albumArtwork"] = 'http://cdn-radiotime-logos.tunein.com/s122119q.png'

    openhomeDevice.PlayMedia(trackDetails)
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
