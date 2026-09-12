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

Pass an existing `aiohttp.ClientSession` to reuse it and its connection pool.
Without one, every request opens and closes a session of its own, which is
wasteful when polling a device:

```python
device = Device(location, session=session)
await device.init()
```

The session is never closed by this library. Whoever created it owns it.

Pass an `event_handler` to receive events through a notify server you already
run, rather than letting the device start one of its own. See
[Sharing a notify server](#sharing-a-notify-server).

### Errors

Every method that talks to the device raises one of these, so callers do not
need to know that `async_upnp_client` is underneath:

```python
from openhomedevice.exceptions import (
    OpenhomeError,             # base class for all of the below
    OpenhomeConnectionError,   # device could not be reached
    OpenhomeTimeoutError,      # device did not answer in time
    OpenhomeDeviceError,       # device answered, but refused or replied unusably
)
```

`OpenhomeTimeoutError` is a subclass of `OpenhomeConnectionError`, so catching
the latter covers a device that is off or unreachable for any reason.
`OpenhomeDeviceError` means the device is reachable but something else is
wrong: a SOAP fault, an HTTP error status, or a response that could not be
parsed. The original exception is kept as `__cause__`.

```python
try:
    await device.init()
except OpenhomeConnectionError:
    ...  # device is off or off the network
except OpenhomeDeviceError:
    ...  # device answered with something unusable
```

### Events

Rather than polling, a device can be asked to push its changes. `subscribe`
takes a callback and returns the lease the device granted:

```python
def on_event(changes):
    print(changes)  # {"volume": 42, "is_muted": False}

lease = await device.subscribe(on_event)
...
await device.unsubscribe()
```

The callback may be a plain function or a coroutine function. It is given a
dictionary holding only what changed, using the same keys and the same types
the matching method would have returned:

| Key | Service | Same as |
| --- | --- | --- |
| `is_in_standby` | Product | `is_in_standby()` |
| `source` | Product | `source()` |
| `sources` | Product | `sources()` |
| `room` | Product | `room()` |
| `name` | Product | `name()` |
| `volume` | Volume | `volume()` |
| `is_muted` | Volume | `is_muted()` |
| `transport_state` | Transport | `transport_state()` |
| `can_pause` | Transport | `can_pause()` |
| `can_skip_next` | Transport | `can_skip_next()` |
| `can_skip_previous` | Transport | `can_skip_previous()` |
| `track_info` | Info | `track_info()` |

The first callback after subscribing carries the device's whole state, because
that is what a device sends when a subscription begins. After that only the
values that actually changed are present, so check for a key rather than
assuming it is there.

A callback that raises is logged and otherwise ignored: the notify server
behind a subscription may be shared with other devices, and one broken
callback must not stop the rest of them receiving anything.

#### Keeping a subscription

A subscription lasts as long as the lease `subscribe` returned, and nothing
here renews it for you. Call `renew` before the lease runs out, on whatever
schedule suits you, and renew against what it returns rather than what you
asked for: a device caps the lease at its own maximum.

```python
lease = await device.subscribe(on_event)
while True:
    await asyncio.sleep(lease.total_seconds() - 60)
    try:
        lease = await device.renew()
    except OpenhomeError:
        lease = await device.subscribe(on_event)
```

Renewing is also the only way to discover that a device has stopped
honouring a subscription. A device that restarted, or that gave up on an
event it could not deliver, is not obliged to say so and does not: it
answers every other request exactly as before, and simply never sends
another event. `renew` raises `OpenhomeDeviceError` when that has happened,
having released everything first, so `is_subscribed` is already `False` and
`subscribe` is what picks the device back up.

Renewing is all or nothing: one subscription that cannot be renewed ends
them all, because holding half a subscription is worse than holding none.
Some values would go stale while others kept arriving, with no way to tell
which were which.

#### Devices that cannot be subscribed to

Subscribing needs the Product, Transport and Info services. Check
`events_enabled` before subscribing; `subscribe()` raises
`OpenhomeDeviceError` on a device that has not got them:

```python
if device.events_enabled:
    await device.subscribe(on_event)
else:
    ...  # poll instead
```

Older firmware and some third party renderers have no Transport service and
report transport state through Radio or Playlist instead. Which of the two is
authoritative depends on the source selected, so neither can be subscribed to,
and transport state is the one value a caller is least able to do without.
Rather than offer a subscription that leaves it behind, none is offered: a
caller polling `transport_state()` on a timer may as well poll the rest and
skip the listener entirely.

A device with no Volume service is still served. Volume control can be
switched off, leaving the device at unity gain with no service to advertise,
so there is no volume for a caller to miss.

#### Sharing a notify server

Events arrive over HTTP, so a subscription needs something listening. By
default the device starts a listener of its own on subscribe and stops it
again on unsubscribe. When several devices are involved it is better to run
one listener and hand it to each of them:

```python
from async_upnp_client.aiohttp import AiohttpNotifyServer, AiohttpRequester
from async_upnp_client.utils import async_get_local_ip

_, local_ip = await async_get_local_ip(location)
server = AiohttpNotifyServer(requester=AiohttpRequester(), source=(local_ip, 0))
await server.async_start_server()

device = Device(location, event_handler=server.event_handler)
```

As with the session, a notify server you supply is never stopped by this
library. Whoever created it owns it.

#### When events do not arrive

A subscription only works if the device can reach the listener, which puts
two requirements on the host running this library.

The callback address must be on the device's own subnet. A device refuses
one that is not, and `subscribe()` raises `OpenhomeDeviceError` carrying
HTTP 412. Hosts behind NAT, such as some container and virtual machine
setups, advertise an address the device cannot route to and are refused for
this reason.

The device must also be able to open a connection back to the listener.
Nothing reports a problem here: the subscription is accepted, `subscribe()`
returns, `is_subscribed` is `True`, and no events ever arrive. A firewall
that permits outbound but blocks inbound connections produces exactly this,
so it is worth ruling out first when a subscription looks healthy but is
silent.

### Methods

#### Control

```python
    await subscribe(callback) #push changes to callback instead of polling
    await unsubscribe() #stop receiving changes
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
    await can_pause() #true if what is playing can be paused, None if unknown
    await can_skip_next() #true if the next track can be skipped to
    await can_skip_previous() #true if the previous track can be skipped to
<<<<<<< HEAD
=======
    is_subscribed #property true while subscribed to the device's events
    events_enabled #property true if this device can be subscribed to
>>>>>>> 9f27828 (Subscribe to device events instead of polling)
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

Update `version` in `setup.py`, then tag the release and publish to PyPI:

```sh
rm -rf dist
python3 -m build
python3 -m twine check dist/*
git tag <version> && git push origin <version>
python3 -m twine upload dist/*
```

`dist` is cleared first because it keeps the artifacts of previous releases,
and `twine upload dist/*` would then try to upload a version that is already
on PyPI.

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
