# openhomedevice

[![Tests](https://github.com/bazwilliams/openhomedevice/actions/workflows/tests.yml/badge.svg)](https://github.com/bazwilliams/openhomedevice/actions/workflows/tests.yml)

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

#### Songcast

```python
    await songcast_receiver_join(sender) #follow a sender from songcast_sender()
    await songcast_receiver_leave() #stop following and clear the sender
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
    await volume() #returns the volume setting or None if disabled
    await is_muted() #returns true if muted or None if disabled
    await source() #returns the currently connected source as a dictionary
    await sources() #returns an array of source dictionaries with indices
    await track_info() #returns a track dictionary
    await pins() #returns an array of pin dictionaries with indices
    pins_enabled #property true if the pins service is available
    songcast_sender_enabled #property true if the sender service is available
    songcast_receiver_enabled #property true if the receiver service is available
    await songcast_sender_status() #Enabled, Disabled or Blocked, or None if unavailable
    await songcast_sender_audio() #true if this device is broadcasting audio
    await songcast_sender() #this device as a sender, or None if it cannot send
    await songcast_receiver_sender() #the sender being followed, or None
    await songcast_receiver_transport_state() #Stopped, Waiting, Playing or Buffering
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

##### Songcast Sender Response

Returned by `songcast_sender()`, and by `songcast_receiver_sender()` for the
sender a device is currently following. `None` when the device cannot send, or
when it is not following anyone.

```python
{
    'uri': 'ohz://239.255.255.250:51972/4c494e4e-0026-0f21-1234-01234567013f',
    'metadata': '<DIDL-Lite ...><item id="0" restricted="True">...</item></DIDL-Lite>'
}
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
    await openhome_device.check_latest_firmware()
    await openhome_device.update_firmware()
```

##### Playing A Track

Use this to play a short audio track, a podcast Uri or radio station Uri. The audio will be played using the radio source of the device. The `trackDetails` object should be the same as the one described in the `TrackInfo` section above.

```python
    track_details = {}
    track_details["uri"] = "http://opml.radiotime.com/Tune.ashx?id=s122119"
    track_details["title"] = 'Linn Radio (Eclectic Music)'
    track_details["albumArtwork"] = 'http://cdn-radiotime-logos.tunein.com/s122119q.png'

    await openhome_device.play_media(track_details)
```

##### Grouping Rooms With Songcast

One device broadcasts its audio as a Songcast sender, and others follow it as
receivers, so several rooms play the same thing in sync.

`songcast_receiver_join` sets the sender and starts the receiver playing. Linn
firmware selects the Songcast source itself in response, so there is no need to
call `set_source` first. `songcast_receiver_leave` stops the receiver and clears
the sender, rather than leaving a stale one configured.

```python
    sender = await kitchen.songcast_sender()

    if sender is not None:
        await living_room.songcast_receiver_join(sender)

    # ... later
    await living_room.songcast_receiver_leave()
```

A receiver reports `Waiting` from `songcast_receiver_transport_state()` when it
is following a sender that is not currently broadcasting any audio. Use
`songcast_sender_audio()` on the sender to tell that apart from a sender that is
genuinely playing.

Not every device can send: `songcast_sender()` returns `None` when the sender
service is missing or reports no metadata, and `songcast_sender_status()`
distinguishes `Enabled` from `Disabled` and `Blocked`.

## Example

```python
python3 demo.py
```

The addresses in `demo.py` are hardcoded. To find the devices on your network:

```sh
python3 tools/discovery.py
```

## Running Tests

Install the package and the test dependencies, then run the suite:

```bash
python3 -m pip install . -r requirements-test.txt
PYTHONPATH=. pytest ./tests/*
```

The same suite runs on GitHub Actions against Python 3.10 to 3.14 for every
push and pull request, so a proposed change shows a pass or fail on the pull
request itself. The workflow is `.github/workflows/tests.yml`.

`requirements-test.txt` holds `aiohttp<3.14`: `aioresponses`, which the tests
use to mock the device, constructs an aiohttp `ClientResponse` by hand and
aiohttp 3.14 added a required argument to that constructor. Without the pin
every mocked request fails. The pin can go once `aioresponses` catches up.

## Releasing

Following guide from https://packaging.python.org/tutorials/packaging-projects/

Update `version` and `download_url` in `setup.py`, then tag the release so the
`download_url` tarball resolves, and publish to PyPI:

```sh
python3 -m build
python3 -m twine check dist/*
git tag <version> && git push origin <version>
python3 -m twine upload dist/*
```

Then publish a GitHub release for that tag:

```sh
gh release create <version> --generate-notes
```

`--generate-notes` writes the release notes from the pull requests and commits
merged since the previous release, so contributions that arrived as PRs are
listed and credited without anything being written by hand. Review the
generated notes afterwards and add a line about anything a consumer of the
library has to act on, such as a changed method signature.

Pushing the tag is not enough on its own: a tag does not appear on the releases
page, and a release created later will only generate notes back to the previous
release, not for work the tag has already gone out with. Create the release at
the same time as the tag. If a tag was already pushed without one, the release
can still be created against it, and the notes filled in by hand where the
generated set is incomplete.

Release notes matter beyond this repository. Home Assistant reviews a
dependency bump by reading what changed between the old and new versions, so a
version with no release is extra work for whoever is handling the bump.

The description shown on PyPI is baked into each release from this file, so a
README change only appears there once a new version is published.
