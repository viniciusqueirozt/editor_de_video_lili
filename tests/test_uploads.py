import io
import threading
from concurrent.futures import ThreadPoolExecutor
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lili.core import EditorError, Store
from lili.uploads import DISK_HEADROOM, Uploads


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


    def test_disk_budget_counts_remaining_bytes_across_projects(self):
        other = self.uploads.store.create('Outro projeto')['id']
        with patch('lili.uploads.shutil.disk_usage', return_value=SimpleNamespace(free=DISK_HEADROOM+10)) as disk:
            uid=self.uploads.start(self.pid,{'name':'teste.mp4','size':6})['upload_id']
            with self.assertRaises(EditorError) as error:
                self.uploads.start(other,{'name':'outro.mp4','size':5})
            self.assertEqual(error.exception.status,507)
            self.assertEqual(len(self.uploads.pending),1)
            self.assertEqual(list((self.uploads.store.folder(other)/'media').iterdir()),[])
            self.uploads.append(self.pid,uid,0,3,io.BytesIO(b'abc'))
            # Disk now contains 3 bytes, and only 3 remain reserved for that file.
            disk.return_value=SimpleNamespace(free=DISK_HEADROOM+7)
            self.uploads.start(other,{'name':'outro.mp4','size':4})
            self.assertEqual(len(self.uploads.pending),2)

    def test_disk_filling_mid_upload_preserves_progress_and_allows_retry(self):
        uid=self.uploads.start(self.pid,{'name':'teste.mp4','size':6})['upload_id']
        self.uploads.append(self.pid,uid,0,3,io.BytesIO(b'abc'))
        with patch('lili.uploads.shutil.disk_usage',return_value=SimpleNamespace(free=DISK_HEADROOM+2)):
            # A retry writes no bytes and remains available even with low disk.
            self.assertEqual(self.uploads.append(self.pid,uid,0,3,io.BytesIO(b'abc')),{'received':3})
            stream=io.BytesIO(b'def')
            with self.assertRaises(EditorError) as error:
                self.uploads.append(self.pid,uid,3,3,stream)
            self.assertEqual(error.exception.status,507)
            self.assertEqual(stream.tell(),0)
            self.assertEqual(self.uploads.pending[uid]['received'],3)
            self.assertEqual(self.uploads.pending[uid]['path'].read_bytes(),b'abc')
        self.uploads.append(self.pid,uid,3,3,io.BytesIO(b'def'))
        self.assertEqual(self.uploads.complete(self.pid,uid)['bytes'],b'abcdef')

    def test_unavailable_disk_check_fails_without_creating_upload(self):
        with patch('lili.uploads.shutil.disk_usage',side_effect=OSError('private path')):
            with self.assertRaises(EditorError) as error:
                self.uploads.start(self.pid,{'name':'teste.mp4','size':6})
        self.assertEqual(error.exception.status,503)
        self.assertNotIn('private path',str(error.exception))
        self.assertEqual(self.uploads.pending,{})

    def test_cancel_releases_partial_file_capacity_and_protects_completed_media(self):
        upload_id = self.uploads.start(self.pid, {"name": "teste.mp4", "size": 6})["upload_id"]
        self.uploads.append(self.pid, upload_id, 0, 3, io.BytesIO(b"abc"))
        path = self.uploads.pending[upload_id]["path"]
        with self.assertRaises(EditorError):
            self.uploads.cancel("0" * 32, upload_id)
        self.assertTrue(path.exists())
        with patch("lili.uploads.shutil.disk_usage", return_value=SimpleNamespace(free=DISK_HEADROOM + 6)):
            self.assertEqual(self.uploads.cancel(self.pid, upload_id), {"cancelled": True, "removed_bytes": 3})
            self.assertFalse(path.exists())
            other = self.uploads.start(self.pid, {"name": "outro.mp4", "size": 6})["upload_id"]
        for action in (lambda: self.uploads.cancel(self.pid, upload_id),
                       lambda: self.uploads.append(self.pid, upload_id, 3, 3, io.BytesIO(b"def")),
                       lambda: self.uploads.complete(self.pid, upload_id)):
            with self.assertRaises(EditorError): action()
        self.uploads.append(self.pid, other, 0, 6, io.BytesIO(b"abcdef"))
        self.uploads.complete(self.pid, other)
        final = self.uploads.store.folder(self.pid) / "media" / (other + ".mp4")
        with self.assertRaises(EditorError): self.uploads.cancel(self.pid, other)
        self.assertEqual(final.read_bytes(), b"abcdef")

    def test_cancel_failure_keeps_pending_and_refuses_unexpected_paths(self):
        upload_id = self.uploads.start(self.pid, {"name": "teste.mov", "size": 6})["upload_id"]
        item = self.uploads.pending[upload_id]
        path = item["path"]
        with patch.object(Path, "unlink", side_effect=PermissionError("private path")):
            with self.assertRaises(EditorError) as error: self.uploads.cancel(self.pid, upload_id)
        self.assertEqual(error.exception.status, 503)
        self.assertIn(upload_id, self.uploads.pending)
        self.assertTrue(path.exists())
        item["path"] = path.with_suffix(".mov")
        with self.assertRaises(EditorError): self.uploads.cancel(self.pid, upload_id)
        self.assertTrue(path.exists())
        item["path"] = path
        path.unlink()
        self.assertEqual(self.uploads.cancel(self.pid, upload_id), {"cancelled": True, "removed_bytes": 0})

    def test_cancel_waits_for_current_block_before_removing_temporary(self):
        upload_id = self.uploads.start(self.pid, {"name": "teste.mp4", "size": 6})["upload_id"]
        entered, release, cancelling = threading.Event(), threading.Event(), threading.Event()
        class BlockingStream(io.BytesIO):
            def read(self, size):
                entered.set()
                if not release.wait(3): raise RuntimeError("test timeout")
                return super().read(size)
        def cancel():
            cancelling.set()
            return self.uploads.cancel(self.pid, upload_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            append = pool.submit(self.uploads.append, self.pid, upload_id, 0, 3, BlockingStream(b"abc"))
            try:
                self.assertTrue(entered.wait(3))
                cancelled = pool.submit(cancel)
                self.assertTrue(cancelling.wait(3))
            finally:
                release.set()
            self.assertEqual(append.result(timeout=3), {"received": 3})
            self.assertEqual(cancelled.result(timeout=3), {"cancelled": True, "removed_bytes": 3})
        self.assertNotIn(upload_id, self.uploads.pending)
