import unittest
from lili.profiles import render_profile,FORMATS
from lili.core import EditorError
class ExportProfileTests(unittest.TestCase):
    def test_all_ratios_and_quality_levels_preserve_even_dimensions(self):
        for width,height in FORMATS.values():
            for quality in ("preview","balanced","full","high"):
                profile=render_profile({"width":width,"height":height},quality)
                self.assertAlmostEqual(profile["width"]/profile["height"],width/height,places=3)
                self.assertEqual(profile["width"]%2,0);self.assertEqual(profile["height"]%2,0)
        self.assertEqual(render_profile({"width":1080,"height":1920},"balanced")["height"],1280)
    def test_invalid_profile_or_dimensions_fail(self):
        for settings,quality in (({"width":True,"height":1920},"full"),({"width":1079,"height":1920},"full"),({"width":1080,"height":1920},{})):
            with self.assertRaises(EditorError):render_profile(settings,quality)
