import unittest
from lili.captions import caption_lines

class CaptionTests(unittest.TestCase):
    def test_lines_words_blank_lines_and_unicode_match_preview(self):
        self.assertEqual(caption_lines("Linha 1\n\nLinha 3"),["Linha 1","","Linha 3"])
        self.assertEqual(caption_lines("Oi " + "x"*55,"large"),["Oi","x"*22,"x"*22,"x"*11])
        self.assertEqual(caption_lines("🐈"*25,"large"),["🐈"*22,"🐈"*3])
        self.assertEqual(caption_lines(" oi   Cora "),["oi Cora"])
