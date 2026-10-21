import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lili.core import EditorError, Store, uid


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        root = Path("work/tests").resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.p = self.store.create("Recuperação", "Roteiro")
        self.folder = self.store.folder(self.p["id"])
        self.main = self.folder / "project.json"
        self.backup = self.folder / "project.json.bak"

    def test_latest_complete_mirror_preserves_imports_and_locked_timeline(self):
        asset = {"id": uid(), "name": "teste.mp4", "status": "ready", "kind": "video", "duration": 5, "has_audio": True}
        self.store.add_media(self.p["id"], asset)
        self.p = self.store.get(self.p["id"])
        self.p = self.store.apply(self.p["id"], "clip_add", {"media_id": asset["id"], "start": 1, "end": 3, "locked": True}, self.p["revision"])
        self.p = self.store.apply(self.p["id"], "narration_set", {"media_id": asset["id"]}, self.p["revision"])
        latest = self.p.copy()
        for invalid in ('{"id":', '[]', '{"id":"wrong"}', b"\xff\xfe"):
            with self.subTest(invalid=invalid):
                self.main.write_bytes(invalid if isinstance(invalid, bytes) else invalid.encode())
                recovered = Store(self.temp.name).get(self.p["id"])
                for key in ("revision", "media", "timeline", "narration", "undo_available"):
                    self.assertEqual(recovered[key], latest[key])
                self.assertIn("recovery_notice", recovered)
        recovered = self.store.apply(self.p["id"], "script_update", {"script": "Revisado"}, latest["revision"])
        self.assertNotIn("recovery_notice", recovered)
        self.assertEqual(json.loads(self.main.read_text(encoding="utf-8")), json.loads(self.backup.read_text(encoding="utf-8")))
        self.assertEqual(recovered["timeline"], latest["timeline"])

    def test_missing_primary_is_listed_and_uses_backup(self):
        self.main.unlink()
        self.assertEqual(self.store.list()[0]["id"], self.p["id"])
        self.assertIn("recovery_notice", self.store.get(self.p["id"]))
        self.assertFalse(self.main.exists(), "Reading alone must not overwrite files")

    def test_invalid_backup_is_never_used_for_another_project(self):
        self.main.write_text("{", encoding="utf-8")
        other = json.loads(self.backup.read_text(encoding="utf-8"))
        other["id"] = uid()
        self.backup.write_text(json.dumps(other), encoding="utf-8")
        with self.assertRaises(EditorError) as error:
            self.store.get(self.p["id"])
        self.assertEqual(error.exception.status, 422)
        self.assertEqual(self.main.read_text(encoding="utf-8"), "{")

    def test_legacy_project_without_backup_remains_readable(self):
        self.backup.unlink()
        self.assertNotIn("recovery_notice", self.store.get(self.p["id"]))
        self.main.write_text("{", encoding="utf-8")
        with self.assertRaises(EditorError) as error:
            self.store.get(self.p["id"])
        self.assertEqual(error.exception.status, 422)
        with self.assertRaises(EditorError) as missing:
            self.store.get(uid())
        self.assertEqual(missing.exception.status, 404)

    def test_failure_between_main_and_backup_keeps_previous_recovery_point(self):
        previous = self.backup.read_bytes()
        original_replace = Path.replace
        def fail_backup(path, target):
            if path.name == "project.json.bak.tmp":
                raise OSError("simulated backup replacement failure")
            return original_replace(path, target)
        with patch("lili.core.Path.replace", fail_backup):
            with self.assertRaises(OSError):
                self.store.apply(self.p["id"], "script_update", {"script": "New primary"}, self.p["revision"])
        self.assertEqual(self.store.get(self.p["id"])["script"], "New primary")
        self.assertEqual(self.backup.read_bytes(), previous)
        self.main.write_text("{", encoding="utf-8")
        recovered = self.store.get(self.p["id"])
        self.assertEqual(recovered["script"], "Roteiro")
        self.assertIn("recovery_notice", recovered)

    def test_interrupted_replacement_preserves_both_valid_files(self):
        original = self.main.read_bytes()
        with patch("lili.core.Path.replace", side_effect=OSError("simulated interrupted save")):
            with self.assertRaises(OSError):
                self.store.apply(self.p["id"], "script_update", {"script": "Never committed"}, self.p["revision"])
        self.assertEqual(self.main.read_bytes(), original)
        self.assertEqual(self.backup.read_bytes(), original)
        self.assertEqual(list(self.folder.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
