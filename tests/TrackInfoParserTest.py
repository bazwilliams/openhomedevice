from openhomedevice.TrackInfoParser import TrackInfoParser
import unittest


class TrackInfoParserTests(unittest.TestCase):
    def setUp(self):
        self.Sut = TrackInfoParser

    def test_corrupt_metadata(self):
        element_string = b'<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:TrackResponse xmlns:u="urn:av-openhome-org:service:Info:1"><Uri>http://192.168.11.92:8200/MediaItems/38297.flac</Uri><Metadata>&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot; xmlns:dlna=&quot;urn:schemas-dlna-org:metadata-1-0/&quot;&gt;&lt;item id=&quot;1$F$2232$97&quot; parentID=&quot;1$F$2232&quot; restricted=&quot;1&quot; refID=&quot;64$2$1$1F4$6$1&quot;&gt;&lt;dc:title&gt;Baby Be Mine&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.audioItem.musicTrack&lt;/upnp:class&gt;&lt;dc:creator&gt;Michael Jackson&lt;/dc:creator&gt;&lt;dc:date&gt;2001-01-01&lt;/dc:date&gt;&lt;upnp:artist&gt;Michael Jackson&lt;/upnp:artist&gt;&lt;upnp:album&gt;Thriller&lt;/upnp:album&gt;&lt;upnp:genre&gt;R&amp;B&lt;/upnp:genre&gt;&lt;upnp:originalTrackNumber&gt;97&lt;/upnp:originalTrackNumber&gt;&lt;res size=&quot;32116092&quot; duration=&quot;0:04:20.160&quot; bitrate=&quot;987579&quot; sampleFrequency=&quot;44100&quot; nrAudioChannels=&quot;2&quot; protocolInfo=&quot;http-get:*:audio/x-flac:*&quot;&gt;http://192.168.11.92:8200/MediaItems/38297.flac&lt;/res&gt;&lt;upnp:albumArtURI dlna:profileID=&quot;JPEG_TN&quot;&gt;http://192.168.11.92:8200/AlbumArt/14347-38297.jpg&lt;/upnp:albumArtURI&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;</Metadata></u:TrackResponse></s:Body></s:Envelope>'
        result = self.Sut(element_string).TrackInfo()
        self.assertEqual(result, {})

    def test_one(self):
        element_string = b'<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"> <s:Body><u:TrackResponse xmlns:u="urn:av-openhome-org:service:Info:1"><Uri>http://192.168.0.110:58050/stream/audio/b362f0f7a1ff33b176bcf2adde75af96.flac</Uri><Metadata>&lt;DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/" xmlns:sec="http://www.sec.co.kr/" xmlns:pv="http://www.pv.com/pvns/"&gt;&lt;item id="qobuz/albums/8424562332058/37122539" parentID="qobuz/albums/8424562332058" restricted="1"&gt;&lt;upnp:class&gt;object.item.audioItem.musicTrack&lt;/upnp:class&gt;&lt;dc:title&gt;Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba) : Violin Sonata No. 2 in A Minor, BWV 1003 (Arr. for Viola da gamba): II. Fuga&lt;/dc:title&gt;&lt;dc:creator&gt;Fahmi Alqhai&lt;/dc:creator&gt;&lt;upnp:artist&gt;Fahmi Alqhai&lt;/upnp:artist&gt;&lt;upnp:artist role="Performer"&gt;Fahmi Alqhai, Performer - Johann Sebastian Bach, Composer&lt;/upnp:artist&gt;&lt;dc:publisher&gt;Glossa&lt;/dc:publisher&gt; &lt;upnp:albumArtURI&gt;http://static.qobuz.com/images/covers/58/20/8424562332058_600.jpg&lt;/upnp:albumArtURI&gt;&lt;upnp:albumArtURI dlna:profileID="JPEG_TN"&gt;http://static.qobuz.com/images/covers/58/20/8424562332058_230.jpg&lt;/upnp:albumArtURI&gt;&lt;upnp:genre&gt;Klassiek&lt;/upnp:genre&gt;&lt;dc:date&gt;2017-01-06&lt;/dc:date&gt;&lt;dc:description&gt;&lt;a href="http://static.qobuz.com/goodies/44/000096244.pdf"&gt;Digital booklet&lt;/a&gt;&lt;/dc:description&gt;&lt;upnp:album&gt;The Bach Album&lt;/upnp:album&gt;&lt;upnp:originalTrackNumber&gt;2&lt;/upnp:originalTrackNumber&gt;&lt;ownerUdn&gt;000974e2-681e-1a36-ffff-ffffa38afd93&lt;/ownerUdn&gt;&lt;res protocolInfo="http-get:*:audio/x-flac:DLNA.ORG_OP=01;DLNA.ORG_FLAGS=01700000000000000000000000000000" bitsPerSample="16" sampleFrequency="44100" nrAudioChannels="2" duration="0:07:40.000"&gt;http://192.168.0.110:58050/stream/audio/b362f0f7a1ff33b176bcf2adde75af96.flac&lt;/res&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;</Metadata></u:TrackResponse></s:Body></s:Envelope>'
        result = self.Sut(element_string).TrackInfo()
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
        element_string = b'<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:TrackResponse xmlns:u="urn:av-openhome-org:service:Info:1"><Uri>http://opml.radiotime.com/Tune.ashx?id=s44491&amp;formats=mp3,wma,aac,ogg,hls&amp;partnerId=ah2rjr68&amp;username=bazwilliams&amp;c=ebrowse</Uri><Metadata>&lt;DIDL-Lite xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot; xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;&quot; parentID=&quot;&quot; restricted=&quot;True&quot;&gt;&lt;dc:title&gt;BBC Radio 6 Music (AAA)&lt;/dc:title&gt;&lt;res protocolInfo=&quot;*:*:*:*&quot; bitrate=&quot;40000&quot;&gt;http://opml.radiotime.com/Tune.ashx?id=s44491&amp;amp;formats=mp3,wma,aac,ogg,hls&amp;amp;partnerId=ah2rjr68&amp;amp;username=bazwilliams&amp;amp;c=ebrowse&lt;/res&gt;&lt;upnp:albumArtURI&gt;http://cdn-radiotime-logos.tunein.com/s44491q.png&lt;/upnp:albumArtURI&gt;&lt;upnp:class&gt;object.item.audioItem&lt;/upnp:class&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;</Metadata></u:TrackResponse></s:Body></s:Envelope>'
        result = self.Sut(element_string).TrackInfo()
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
        element_string = b'<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:TrackResponse xmlns:u="urn:av-openhome-org:service:Info:1"><Uri>http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3</Uri><Metadata>&lt;DIDL-Lite xmlns=&quot;urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/&quot;&gt;&lt;item id=&quot;d5112915403826242371-co533&quot; parentID=&quot;co533&quot; restricted=&quot;0&quot;&gt;&lt;dc:title xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot;&gt;The Mystic Trumpeter, Op. 18 - Colin Matthews &amp;amp; Imogen Holst&lt;/dc:title&gt;&lt;upnp:class xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;object.item.audioItem.musicTrack&lt;/upnp:class&gt;&lt;upnp:albumArtURI xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3/$!picture-633-144623.jpg&lt;/upnp:albumArtURI&gt;&lt;upnp:album xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;Holst: The Planets, The Mystic Trumpeter&lt;/upnp:album&gt;&lt;upnp:artist xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;Royal Scottish National Orchestra; David Lloyd-Jones&lt;/upnp:artist&gt;&lt;upnp:artist role=&quot;AlbumArtist&quot; xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;Royal Scottish National Orchestra; David Lloyd-Jones&lt;/upnp:artist&gt;&lt;dc:date xmlns:dc=&quot;http://purl.org/dc/elements/1.1/&quot;&gt;2001-01-01&lt;/dc:date&gt;&lt;upnp:genre xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;Classical&lt;/upnp:genre&gt;&lt;upnp:genre xmlns:upnp=&quot;urn:schemas-upnp-org:metadata-1-0/upnp/&quot;&gt;Orchestral&lt;/upnp:genre&gt;&lt;res sampleFrequency=&quot;44100&quot; bitrate=&quot;24000&quot;&gt;http://192.168.1.126:9790/minimserver/*/music/Albums/RSNO*20-*20Holst*20-*20The*20Planets,*20The*20Mystic*20Trumpeter/09*20The*20Mystic*20Trumpeter,*20Op.*2018*20-*20Colin*20Matthews*20*26*20Imogen*20Holst.mp3&lt;/res&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;</Metadata></u:TrackResponse></s:Body></s:Envelope>'
        result = self.Sut(element_string).TrackInfo()
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
