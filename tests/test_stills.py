import tempfile
import unittest
from pathlib import Path
from PIL import Image
from lili.core import EditorError
from lili.stills import prepare_still


class StillTests(unittest.TestCase):
    def setUp(self):
        root = Path('work/tests');root.mkdir(parents=True,exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_normalizes_orientation_alpha_and_preserves_source(self):
        source=self.root/'foto.png';output=self.root/'normalized.png'
        Image.new('RGBA',(80,40),(255,0,0,128)).save(source)
        original=source.read_bytes()
        result=prepare_still(source,output)
        self.assertTrue(result['is_still']);self.assertEqual(result['duration'],30)
        with Image.open(output) as image:
            self.assertEqual(image.mode,'RGB');self.assertEqual(image.getpixel((0,0)),(128,0,0))
        self.assertEqual(source.read_bytes(),original)
        exif=Image.Exif();exif[274]=6
        source=self.root/'rotated.jpg';Image.new('RGB',(80,40),'blue').save(source,exif=exif)
        result=prepare_still(source,output)
        self.assertEqual((result['width'],result['height']),(40,80))

    def test_rejects_corrupt_animated_and_oversized_before_decoding(self):
        source=self.root/'bad.png';source.write_bytes(b'not an image')
        with self.assertRaises(EditorError):prepare_still(source,self.root/'out.png')
        frames=[Image.new('RGB',(10,10),color) for color in ('red','blue')]
        frames[0].save(source,save_all=True,append_images=frames[1:],duration=100,loop=0)
        with self.assertRaises(EditorError):prepare_still(source,self.root/'out.png')
        from unittest.mock import patch
        with patch('lili.stills.Image.open') as opened:
            image=opened.return_value.__enter__.return_value
            image.format='PNG';image.is_animated=False;image.width=10000;image.height=6000;image.size=(10000,6000)
            with self.assertRaises(EditorError):prepare_still(source,self.root/'out.png')
            image.convert.assert_not_called()
