import unittest

import openhomedevice.source_list as source_list


class VisibleDialectTests(unittest.TestCase):
    """Devices disagree on how to spell a boolean in SourceXml.

    Linn writes <Visible>true</Visible> and AURALiC writes <Visible>1</Visible>.
    Reading only the Linn spelling filtered out every source on an AURALiC and
    left both sources() and the sources event empty.
    """

    def sources_from(self, visible):
        xml = (
            "<SourceList>"
            f"<Source><Name>Playlist</Name><Type>Playlist</Type>"
            f"<Visible>{visible}</Visible></Source>"
            "</SourceList>"
        )
        return source_list.visible(source_list.parse(xml))

    def test_the_linn_spelling_is_visible(self):
        self.assertEqual(len(self.sources_from("true")), 1)

    def test_the_auralic_spelling_is_visible(self):
        self.assertEqual(len(self.sources_from("1")), 1)

    def test_both_spellings_of_hidden_are_hidden(self):
        for hidden in ("false", "0"):
            with self.subTest(visible=hidden):
                self.assertEqual(self.sources_from(hidden), [])

    def test_case_and_whitespace_do_not_matter(self):
        for spelling in ("True", " TRUE ", "\n1\n"):
            with self.subTest(visible=spelling):
                self.assertEqual(len(self.sources_from(spelling)), 1)

    def test_a_source_with_no_visible_element_is_hidden(self):
        """Rather than raising on the missing element, as it used to."""
        xml = (
            "<SourceList>"
            "<Source><Name>Playlist</Name><Type>Playlist</Type></Source>"
            "</SourceList>"
        )
        self.assertEqual(source_list.visible(source_list.parse(xml)), [])

    def test_hidden_sources_keep_their_index(self):
        """SourceIndex counts them, so filtering must not renumber."""
        xml = (
            "<SourceList>"
            "<Source><Name>A</Name><Type>Playlist</Type><Visible>1</Visible></Source>"
            "<Source><Name>B</Name><Type>UpnpAv</Type><Visible>0</Visible></Source>"
            "<Source><Name>C</Name><Type>Radio</Type><Visible>1</Visible></Source>"
            "</SourceList>"
        )
        self.assertEqual(
            [s["index"] for s in source_list.visible(source_list.parse(xml))], [0, 2]
        )
