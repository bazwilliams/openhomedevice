from openhomedevice.didl_lite import parse
import unittest


class TrackInfoParserTests(unittest.TestCase):
    def setUp(self):
        self.sut = parse

    def test_one(self):
        element_string = '<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" xmlns:sec="http://www.sec.co.kr/" xmlns:pv="http://www.pv.com/pvns/"><item id="qobuz/albums/8424562332058/37122539" parentID="qobuz/albums/8424562332058" restricted="1"><upnp:class>object.item.audioItem.musicTrack</upnp:class><dc:title>Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba) : Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba): II. Fuga</dc:title><dc:creator>Fahmi Alqhai</dc:creator><upnp:artist>Fahmi Alqhai</upnp:artist><upnp:artist role="Performer">Fahmi Alqhai, Performer - Johann Sebastian Bach, Composer</upnp:artist><dc:publisher>Glossa</dc:publisher> <upnp:albumArtURI>http://static.qobuz.com/images/covers/58/20/8424562332058_600.jpg</upnp:albumArtURI><upnp:albumArtURI dlna:profileID="JPEG_TN">http://static.qobuz.com/images/covers/58/20/8424562332058_230.jpg</upnp:albumArtURI><upnp:genre>Klassiek</upnp:genre><dc:date>2017-01-06</dc:date><dc:description><a href="http://static.qobuz.com/goodies/44/000096244.pdf">Digital booklet</a></dc:description><upnp:album>The Bach Album</upnp:album><upnp:originalTrackNumber>2</upnp:originalTrackNumber><ownerUdn>000974e2-681e-1a36-ffff-ffffa38afd93</ownerUdn><res protocolInfo="http-get:*:audio/x-flac:DLNA.ORG_OP=01;DLNA.ORG_FLAGS=01700000000000000000000000000000" bitsPerSample="16" sampleFrequency="44100" nrAudioChannels="2" duration="0:07:40.000">http://192.168.0.110:58050/stream/audio/b362f0f7a1ff33b176bcf2adde75af96.flac</res></item></DIDL-Lite>'
        result = self.sut(element_string)
        self.assertEqual(result.get("type"), "object.item.audioItem.musicTrack")
        self.assertEqual(
            result.get("title"),
            "Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba) : Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba): II. Fuga",
        )
        self.assertEqual(
            result.get("uri"),
            "http://192.168.0.110:58050/stream/audio/b362f0f7a1ff33b176bcf2adde75af96.flac",
        )
        self.assertSetEqual(
            set(result.get("artist")),
            set(
                [
                    "Fahmi Alqhai, Performer - Johann Sebastian Bach, Composer",
                    "Fahmi Alqhai",
                ]
            ),
        )
        self.assertSetEqual(set(result.get("conductor")), set())
        self.assertSetEqual(set(result.get("albumArtist")), set())
        self.assertSetEqual(set(result.get("genre")), set(["Klassiek"]))
        self.assertSetEqual(set(result.get("albumGenre")), set(["Klassiek"]))
        self.assertEqual(result.get("albumTitle"), "The Bach Album")
        self.assertEqual(
            result.get("albumArtwork"),
            "http://static.qobuz.com/images/covers/58/20/8424562332058_600.jpg",
        )
        self.assertEqual(result.get("artwork"), None)
        self.assertEqual(result.get("year"), 2017)
        self.assertEqual(result.get("disc"), None)
        self.assertEqual(result.get("discs"), None)
        self.assertEqual(result.get("track"), 2)
        self.assertEqual(result.get("tracks"), None)
        self.assertSetEqual(set(result.get("author")), set())
        self.assertEqual(result.get("publisher"), "Glossa")
        self.assertEqual(result.get("published"), None)
        self.assertEqual(result.get("description"), None)
        self.assertEqual(result.get("rating"), None)
        self.assertEqual(result.get("channels"), 2)
        self.assertEqual(result.get("bitDepth"), 16)
        self.assertEqual(result.get("sampleRate"), 44100)
        self.assertEqual(result.get("bitRate"), None)
        self.assertEqual(result.get("duration"), 460)
        self.assertEqual(
            result.get("mimeType"),
            "http-get:*:audio/x-flac:DLNA.ORG_OP=01;DLNA.ORG_FLAGS=01700000000000000000000000000000",
        )

    def test_two(self):
        element_string = '<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="" parentID="" restricted="True"><dc:title>BBC Radio 6 Music (AAA)</dc:title><res protocolInfo="*:*:*:*" bitrate="40000">http://opml.radiotime.com/Tune.ashx?id=s44491&amp;formats=mp3,wma,aac,ogg,hls&amp;partnerId=ah2rjr68&amp;username=bazwilliams&amp;c=ebrowse</res><upnp:albumArtURI>http://cdn-radiotime-logos.tunein.com/s44491q.png</upnp:albumArtURI><upnp:class>object.item.audioItem</upnp:class></item></DIDL-Lite>'
        result = self.sut(element_string)
        self.assertEqual(result.get("type"), "object.item.audioItem")
        self.assertEqual(result.get("title"), "BBC Radio 6 Music (AAA)")
        self.assertEqual(
            result.get("uri"),
            "http://opml.radiotime.com/Tune.ashx?id=s44491&formats=mp3,wma,aac,ogg,hls&partnerId=ah2rjr68&username=bazwilliams&c=ebrowse",
        )
        self.assertSetEqual(set(result.get("artist")), set())
        self.assertSetEqual(set(result.get("conductor")), set())
        self.assertSetEqual(set(result.get("albumArtist")), set())
        self.assertSetEqual(set(result.get("genre")), set())
        self.assertSetEqual(set(result.get("albumGenre")), set())
        self.assertEqual(result.get("albumTitle"), None)
        self.assertEqual(
            result.get("albumArtwork"),
            "http://cdn-radiotime-logos.tunein.com/s44491q.png",
        )
        self.assertEqual(result.get("artwork"), None)
        self.assertEqual(result.get("year"), None)
        self.assertEqual(result.get("disc"), None)
        self.assertEqual(result.get("discs"), None)
        self.assertEqual(result.get("track"), None)
        self.assertEqual(result.get("tracks"), None)
        self.assertSetEqual(set(result.get("author")), set())
        self.assertEqual(result.get("publisher"), None)
        self.assertEqual(result.get("published"), None)
        self.assertEqual(result.get("description"), None)
        self.assertEqual(result.get("rating"), None)
        self.assertEqual(result.get("channels"), None)
        self.assertEqual(result.get("bitDepth"), None)
        self.assertEqual(result.get("sampleRate"), None)
        self.assertEqual(result.get("bitRate"), 40000)
        self.assertEqual(result.get("duration"), None)
        self.assertEqual(result.get("mimeType"), "*:*:*:*")

    def test_three(self):
        element_string = '<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"><item id="d5112915403826242371-co533" parentID="co533" restricted="0"><dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">The Mystic Trumpeter, Op. 18 - Colin Matthews &amp; Imogen Holst</dc:title><upnp:class xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">object.item.audioItem.musicTrack</upnp:class><upnp:albumArtURI xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3/$!picture-633-144623.jpg</upnp:albumArtURI><upnp:album xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Holst: The Planets, The Mystic Trumpeter</upnp:album><upnp:artist xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Royal Scottish National Orchestra; David Lloyd-Jones</upnp:artist><upnp:artist role="AlbumArtist" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Royal Scottish National Orchestra; David Lloyd-Jones</upnp:artist><dc:date xmlns:dc="http://purl.org/dc/elements/1.1/">2001-01-01</dc:date><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Classical</upnp:genre><upnp:genre xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/">Orchestral</upnp:genre><res sampleFrequency="44100" bitrate="24000">http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3</res></item></DIDL-Lite>'
        result = self.sut(element_string)
        self.assertEqual(result.get("type"), "object.item.audioItem.musicTrack")
        self.assertEqual(
            result.get("title"),
            "The Mystic Trumpeter, Op. 18 - Colin Matthews & Imogen Holst",
        )
        self.assertEqual(
            result.get("uri"),
            "http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3",
        )
        self.assertSetEqual(
            set(result.get("artist")),
            set(["Royal Scottish National Orchestra; David Lloyd-Jones"]),
        )
        self.assertSetEqual(set(result.get("conductor")), set())
        self.assertSetEqual(
            set(result.get("albumArtist")),
            set(["Royal Scottish National Orchestra; David Lloyd-Jones"]),
        )
        self.assertSetEqual(set(result.get("genre")), set(["Orchestral", "Classical"]))
        self.assertSetEqual(
            set(result.get("albumGenre")), set(["Orchestral", "Classical"])
        )
        self.assertEqual(
            result.get("albumTitle"), "Holst: The Planets, The Mystic Trumpeter"
        )
        self.assertEqual(
            result.get("albumArtwork"),
            "http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3/$!picture-633-144623.jpg",
        )
        self.assertEqual(result.get("artwork"), None)
        self.assertEqual(result.get("year"), 2001)
        self.assertEqual(result.get("disc"), None)
        self.assertEqual(result.get("discs"), None)
        self.assertEqual(result.get("track"), None)
        self.assertEqual(result.get("tracks"), None)
        self.assertSetEqual(set(result.get("author")), set())
        self.assertEqual(result.get("publisher"), None)
        self.assertEqual(result.get("published"), None)
        self.assertEqual(result.get("description"), None)
        self.assertEqual(result.get("rating"), None)
        self.assertEqual(result.get("channels"), None)
        self.assertEqual(result.get("bitDepth"), None)
        self.assertEqual(result.get("sampleRate"), 44100)
        self.assertEqual(result.get("bitRate"), 24000)
        self.assertEqual(result.get("duration"), None)
        self.assertEqual(result.get("mimeType"), None)
