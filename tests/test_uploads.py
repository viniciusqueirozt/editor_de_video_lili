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


    def test_retry_consumes_and_compares_bytes_without_changing_progress(self):
        uid=self.uploads.start(self.pid,{'name':'teste.mp4','size':6})['upload_id']
        self.uploads.append(self.pid,uid,0,3,io.BytesIO(b'abc'))
        repeated=io.BytesIO(b'abc')
        self.assertEqual(self.uploads.append(self.pid,uid,'0',3,repeated),{'received':3})
        self.assertEqual(repeated.tell(),3)
        for content,status in ((b'XYZ',409),(b'ab',400)):
            with self.subTest(content=content),self.assertRaises(EditorError) as error:
                self.uploads.append(self.pid,uid,0,3,io.BytesIO(content))
            self.assertEqual(error.exception.status,status)
            self.assertEqual(self.uploads.pending[uid]['received'],3)
            self.assertEqual(self.uploads.pending[uid]['path'].read_bytes(),b'abc')
        self.uploads.append(self.pid,uid,3,3,io.BytesIO(b'def'))
        self.assertEqual(self.uploads.complete(self.pid,uid)['bytes'],b'abcdef')

    def test_offset_and_length_must_be_whole_bytes(self):
        uid=self.uploads.start(self.pid,{'name':'teste.mp4','size':6})['upload_id']
        for offset in ('0.00001','0.5','1e0','-1','nan','9999999999999',True,0.0,None):
            with self.subTest(offset=offset),self.assertRaises(EditorError):
                self.uploads.append(self.pid,uid,offset,3,io.BytesIO(b'abc'))
        for length in (True,1.5,'3',None,0,-1):
            with self.subTest(length=length),self.assertRaises(EditorError):
                self.uploads.append(self.pid,uid,0,length,io.BytesIO(b'abc'))
        self.assertEqual(self.uploads.pending[uid]['received'],0)
        self.assertEqual(self.uploads.pending[uid]['path'].read_bytes(),b'')
        self.uploads.append(self.pid,uid,'0',3,io.BytesIO(b'abc'))
        self.assertEqual(self.uploads.pending[uid]['received'],3)


    def test_declared_file_size_rejects_rounding_and_invalid_types(self):
        for size in (6.00001,6.0,True,None,'6',0,-1,2*1024**3+1,float('nan')):
            with self.subTest(size=size),self.assertRaises(EditorError):
                self.uploads.start(self.pid,{'name':'teste.mp4','size':size})
        self.assertEqual(self.uploads.pending,{})
