import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from lili.core import Store
from lili.media import MediaService

class JobPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir="work/tests");self.addCleanup(self.tmp.cleanup)
        self.media=MediaService(Store(self.tmp.name));self.addCleanup(lambda:self.media.pool.shutdown(wait=True))
        self.media.jobs={"synthetic":{"status":"queued"}}
    def test_transient_replacement_denial_retries_without_losing_jobs(self):
        original=Path.replace;calls=[]
        def replace(source,target):
            calls.append(target)
            if len(calls)<3:raise PermissionError("synthetic sharing conflict")
            return original(source,target)
        with patch.object(Path,"replace",replace),patch("lili.media.time.sleep") as sleep:
            self.media._save_jobs()
        self.assertEqual(len(calls),3);self.assertEqual(sleep.call_count,2)
        self.assertEqual(json.loads(self.media.jobs_file.read_text(encoding="utf-8")),self.media.jobs)
    def test_persistent_denial_is_bounded_and_preserves_previous_file(self):
        self.media.jobs_file.write_text('{"previous":true}',encoding="utf-8")
        with patch.object(Path,"replace",side_effect=PermissionError("synthetic denial")) as replace,patch("lili.media.time.sleep") as sleep:
            with self.assertRaises(PermissionError):self.media._save_jobs()
        self.assertEqual(replace.call_count,5);self.assertEqual(sleep.call_count,4)
        self.assertEqual(json.loads(self.media.jobs_file.read_text(encoding="utf-8")),{"previous":True})
