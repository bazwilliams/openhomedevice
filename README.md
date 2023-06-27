# openhomedevice

Library to provide an API to an existing openhome device. The device needs to have been discovered first by something like netdisco (https://github.com/home-assistant/netdisco).

The underlying UPnP client library used is https://github.com/StevenLooman/async_upnp_client

* Tested against [Linn Products Ltd](https://www.linn.co.uk/uk/) devices running Davaar 80 (thought expected to work on earlier variants)
* Tested against [OpenHome Player](http://openhome.org/) devices

## Installation

`pip install openhomedevice`

## API

### Constructor

```python
device = Device(location)
await device.init()
```

### Methods

#### Control

```python
    await set_standby(standbyRequested) #bool
    await play() #starts playback
    await play_media(track_details) #start playing `track_details`
    await stop() #stops playback
    await pause() #pauses playback
    await skip(offset) #positive or negative integer
    await set_volume(volume_level) #positive number
    await increase_volume() #increase volume by 1
    await decrease_volume() #decrease volume by 1
    await set_mute(muteRequested) #bool
    await set_source(index) #positive integer (use Sources() for indices)
    await invoke_pin(index) #positive integer (use Pins() for indices)
```

#### Firmware

```python
    await check_latest_firmware() #check for the latest firmware
    await update_firmware() #update the device firmware
    await software_status() #returns a dictionary with information about the current software
```

#### Informational

```python
    uuid() #Unique identifier
    manufacturer() #Manufacturer
    model_name() #Model Name
    friendly_name() #Friendly Name
    await name() #Name of device
    await room() #Name of room
    await is_in_standby() #returns true if in standby
    await transport_state() #returns one of Stopped, Playing, Paused or Buffering.
    volume_enabled #property true if the volume service is available
    await volume_level() #returns the volume setting or None if disabled
    await is_muted() #returns true if muted or None if disabled
    await source() #returns the currently connected source as a dictionary
    await sources() #returns an array of source dictionaries with indices
    await track_info() #returns a track dictionary
    await pins() #returns an array of pin dictionaries with indices
    pins_enabled #property true if the pins service is available
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

##### Pins Response

```python
[
  {'index': 1, 'title': 'Playstation 4', 'artworkUri': 'external:///source?type=Hdmi&systemName=HDMI3'}
  {'index': 4, 'title': 'Classic FM', 'artworkUri': 'http://cdn-profiles.tunein.com/s8439/images/logoq.png?t=1'}
  {'index': 6, 'title': 'Chillout Playlist', 'artworkUri': 'http://media/artwork/chillout-playlist.png'}
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

##### SoftwareStatus response

When an update is available:

```python
{
   "status":"update_available",
   "current_software":{
      "version":"4.99.491",
      "topic":"main",
      "channel":"release"
   },
   "update_info":{
      "legal":{
         "licenseurl":"http://products.linn.co.uk/VersionInfo/licenseV2.txt",
         "privacyurl":"https://www.linn.co.uk/privacy",
         "privacyuri":"https://products.linn.co.uk/VersionInfo/PrivacyV1.json",
         "privacyversion":1
      },
      "releasenotesuri":"http://docs.linn.co.uk/wiki/index.php/ReleaseNotes",
      "updates":[
         {
            "channel":"release",
            "date":"07 Jun 2023 12:29:48",
            "description":"Release build version 4.100.502 (07 Jun 2023 12:29:48)",
            "exaktlink":"3",
            "manifest":"https://cloud.linn.co.uk/update/components/836/4.100.502/manifest.json",
            "topic":"main",
            "variant":"836",
            "version":"4.100.502"
         }
      ],
      "exaktUpdates":[]
   }
}
```

When the system is on the latest firmware:

```python
{
   "status":"on_latest",
   "current_software":{
      "version":"4.100.502",
      "topic":"main",
      "channel":"release"
   }
}
```

##### Upgrading Firmware

Use this to check if an update is required and then instruct the device to apply it

```python
    await openhomeDevice.check_latest_firmware()
    await openhomeDevice.update_firmware()
```

##### Playing A Track

Use this to play a short audio track, a podcast Uri or radio station Uri. The audio will be played using the radio source of the device. The `trackDetails` object should be the same as the one described in the `TrackInfo` section above.

```python
    track_details = {}
    track_details["uri"] = "http://opml.radiotime.com/Tune.ashx?id=s122119"
    track_details["title"] = 'Linn Radio (Eclectic Music)'
    track_details["albumArtwork"] = 'http://cdn-radiotime-logos.tunein.com/s122119q.png'

    openhomeDevice.PlayMedia(track_details)
```

## Example

```python
python3 demo.py
```

## Running Tests

```bash
PYTHONPATH=. pytest ./tests/*
```

## Uploading Package

Following guide from https://packaging.python.org/tutorials/packaging-projects/

Update version in `setup.py`

```sh
python3 setup.py sdist
twine upload dist/*
```
