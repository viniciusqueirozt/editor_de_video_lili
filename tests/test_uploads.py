import io
import tempfile
import unittest
from pathlib import Path

from lili.core import EditorError, Store
from lili.uploads import Uploads


class Registrar:
    def register(self,pid,path,name,upload_id):
        return {'media_id':upload_id,'bytes':path.read_bytes(),'name':name}


class UploadTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('work/tests').resolve();scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        store=Store(self.temp.name)
        self.pid=store.create('Envio')['id']
        self.uploads=Uploads(store,Registrar())

    def test_blocks_retry_and_completion_preserve_exact_bytes(self):
        uid=self.uploads.start(self.pid,{'name':'teste.mp4','size':6})['upload_id']
        self.uploads.append(self.pid,uid,0,3,io.BytesIO(b'abc'))
        self.uploads.append(self.pid,uid,0,3,io.BytesIO(b'abc'))
        with self.assertRaises(EditorError):self.uploads.complete(self.pid,uid)
        with self.assertRaises(EditorError):self.uploads.append(self.pid,uid,2,3,io.BytesIO(b'XYZ'))
        with self.assertRaises(EditorError):self.uploads.append(self.pid,uid,3,3,io.BytesIO(b'd'))
        self.uploads.append(self.pid,uid,3,3,io.BytesIO(b'def'))
        self.assertEqual(self.uploads.complete(self.pid,uid)['bytes'],b'abcdef')
        with self.assertRaises(EditorError):self.uploads.complete(self.pid,uid)

    def test_another_project_cannot_append_or_finish(self):
        uid=self.uploads.start(self.pid,{'name':'teste.mov','size':6})['upload_id']
        with self.assertRaises(EditorError):self.uploads.append('0'*32,uid,0,3,io.BytesIO(b'abc'))
        with self.assertRaises(EditorError):self.uploads.complete('0'*32,uid)
