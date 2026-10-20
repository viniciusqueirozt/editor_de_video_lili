import copy
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from lili.ai import AIEditor
from lili.core import EditorError, Store, uid
from lili.media import MediaService


class AIEditorTests(unittest.TestCase):
    def setUp(self):
        scratch = Path("work/tests").resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.p = self.store.create("IA", "Uma chegada.\n\nA despedida.")
        self.asset = {"id": uid(), "name": "teste.mp4", "filename": "teste.mp4", "kind": "video", "duration": 5,
                      "status": "ready", "has_audio": True}
        self.store.add_media(self.p["id"], self.asset)
        self.p = self.store.get(self.p["id"])
        self.media = MediaService(self.store)
        self.addCleanup(lambda: self.media.pool.shutdown(wait=True))
        self.media.sheet = lambda *_: Path("example-sheet.jpg")
        self.plan = {"summary": "Montagem visual", "warnings": ["Revisar os cortes"], "clips": [
            {"media_id": self.asset["id"], "start": .3, "end": 2, "label": "Chegada", "title": "", "volume": 1,
             "block_id": "bloco-1", "existing_clip_id": None}]}
        self.ai = AIEditor(self.store, self.media, lambda *_: copy.deepcopy(self.plan))

    def wait_job(self, job):
        for _ in range(150):
            current = self.media.job(job["id"])
            if current["status"] in ("done", "error"):
                return current
            time.sleep(.02)
        self.fail("Edição com IA não terminou")

    def test_generated_timeline_is_editable_and_undoable(self):
        result = self.wait_job(self.ai.start(self.p["id"], self.p["revision"]))
        self.assertEqual(result["status"], "done", result)
        p = self.store.get(self.p["id"])
        self.assertEqual(len(p["timeline"]), 1)
        self.assertEqual(p["last_change"]["actor"], "IA · Codex")
        clip = p["timeline"][0]
        p = self.store.apply(p["id"], "clip_update", {"clip_id": clip["id"], "end": 2.5}, p["revision"])
        self.assertEqual(p["timeline"][0]["end"], 2.5)
        p = self.store.apply(p["id"], "undo", {}, p["revision"])
        p = self.store.apply(p["id"], "undo", {}, p["revision"])
        self.assertEqual(p["timeline"], [])

    def test_invalid_plan_does_not_change_project(self):
        for mutation in ({"clips": []}, {"warnings": [None]}, {"summary": "x" * 4001}):
            plan = {**self.plan, **mutation}
            self.ai.runner = lambda *_, plan=plan: plan
            result = self.wait_job(self.ai.start(self.p["id"], self.p["revision"]))
            self.assertEqual(result["status"], "error")
            self.assertEqual(self.store.get(self.p["id"])["revision"], self.p["revision"])
        self.plan["clips"][0]["end"] = 30
        self.ai.runner = lambda *_: self.plan
        self.assertEqual(self.wait_job(self.ai.start(self.p["id"], self.p["revision"]))["status"], "error")

    def test_manual_edit_during_analysis_is_not_overwritten(self):
        def runner(*_):
            self.store.apply(self.p["id"], "script_update", {"script": "Roteiro novo"}, self.p["revision"])
            return self.plan
        self.ai.runner = runner
        job = self.wait_job(self.ai.start(self.p["id"], self.p["revision"]))
        self.assertEqual(job["status"], "error")
        self.assertEqual(self.store.get(self.p["id"])["script"], "Roteiro novo")
        self.assertEqual(self.store.get(self.p["id"])["timeline"], [])

    def test_protected_scene_must_be_preserved_and_narration_is_kept(self):
        self.p = self.store.apply(self.p["id"], "clip_add", {"media_id": self.asset["id"], "start": 0, "end": 1, "locked": True}, self.p["revision"])
        self.p = self.store.apply(self.p["id"], "narration_set", {"media_id": self.asset["id"]}, self.p["revision"])
        self.assertEqual(self.wait_job(self.ai.start(self.p["id"], self.p["revision"]))["status"], "error")
        protected = self.p["timeline"][0]
        self.plan["clips"].insert(0, {**{k: v for k, v in protected.items() if k not in ("id", "locked")}, "existing_clip_id": protected["id"]})
        self.assertEqual(self.wait_job(self.ai.start(self.p["id"], self.p["revision"]))["status"], "done")
        p = self.store.get(self.p["id"])
        self.assertEqual(p["timeline"][0], protected)
        self.assertEqual(p["narration"], self.p["narration"])

    def test_prerequisites_and_duplicate_run(self):
        gate = threading.Event()
        self.ai.runner = lambda *_: (gate.wait(3), self.plan)[1]
        job = self.ai.start(self.p["id"], self.p["revision"])
        try:
            with self.assertRaises(EditorError):
                self.ai.start(self.p["id"], self.p["revision"])
        finally:
            gate.set()
        self.wait_job(job)
        self.p = self.store.get(self.p["id"])
        self.store.update_media(self.p["id"], self.asset["id"], {"status": "processing"})
        self.p = self.store.get(self.p["id"])
        with self.assertRaises(EditorError):
            self.ai.start(self.p["id"], self.p["revision"])
        with self.assertRaises(EditorError):
            self.ai.start(self.p["id"], True)

    def test_cli_is_bounded_and_does_not_execute_model_shell_commands(self):
        def fake_run(command, **kwargs):
            self.assertIn("--ephemeral", command)
            self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
            self.assertIn("--ignore-user-config", command)
            self.assertIn("shell_tool", command)
            self.assertIn("--image", command)
            self.assertEqual(kwargs["timeout"], 1200)
            Path(command[command.index("--output-last-message") + 1]).write_text('{"clips":[]}', encoding="utf-8")
            return type("Result", (), {"returncode": 0})()
        with patch("lili.ai.shutil.which", return_value="codex.exe"), patch("lili.ai.subprocess.run", side_effect=fake_run):
            self.assertEqual(AIEditor.run_codex(self.p, "", [Path("sheet.jpg")]), {"clips": []})


if __name__ == "__main__":
    unittest.main()
