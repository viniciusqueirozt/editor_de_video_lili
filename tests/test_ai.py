import copy
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from lili.ai import AIEditor, QUICK_ACTIONS
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

    def test_generated_montage_separates_audio_and_visual_replacement_preserves_it(self):
        self.assertEqual(self.wait_job(self.ai.start(self.p["id"],self.p["revision"]))["status"],"done")
        p=self.store.get(self.p["id"]);self.assertTrue(p["timeline"][0]["audio_detached"])
        self.assertEqual(len(p["audio_clips"]),1);sound=copy.deepcopy(p["audio_clips"])
        self.plan["clips"][0].update(start=2,end=4)
        self.assertEqual(self.wait_job(self.ai.start(p["id"],p["revision"],"Troque somente as imagens"))["status"],"done")
        current=self.store.get(p["id"]);self.assertEqual(current["audio_clips"],sound)
        self.assertTrue(current["timeline"][0]["audio_detached"])

    def test_local_mute_changes_independent_audio_and_respects_audio_locks(self):
        for start,end in ((0,2),(2,4)):
            self.p=self.store.apply(self.p["id"],"clip_add",{"media_id":self.asset["id"],"start":start,"end":end,"separate_audio":True},self.p["revision"])
        locked=self.p["audio_clips"][0]["id"]
        self.p=self.store.apply(self.p["id"],"audio_clip_update",{"audio_id":locked,"locked":True},self.p["revision"])
        sounds=copy.deepcopy(self.p["audio_clips"])
        for clip in list(self.p["timeline"]):
            self.p=self.store.apply(self.p["id"],"clip_update",{"clip_id":clip["id"],"locked":True},self.p["revision"])
        action=next(a["instructions"] for a in QUICK_ACTIONS if a["kind"]=="mute")
        self.ai.runner=lambda *_:self.fail("Local mute must not call AI")
        job=self.wait_job(self.ai.start(self.p["id"],self.p["revision"],action));self.assertEqual(job["status"],"done",job)
        current=self.store.get(self.p["id"]);self.assertEqual(current["audio_clips"][0],sounds[0]);self.assertEqual(current["audio_clips"][1]["volume"],0)
        self.assertEqual(current["timeline"],self.p["timeline"])

    def test_mute_original_audio_preserves_imported_effects(self):
        self.p=self.store.apply(self.p["id"],"clip_add",{"media_id":self.asset["id"],"start":0,"end":4,"separate_audio":True},self.p["revision"])
        self.p=self.store.apply(self.p["id"],"audio_clip_add",{"media_id":self.asset["id"],"start":0,"end":1,"offset":1,"volume":.5},self.p["revision"])
        effect=copy.deepcopy(self.p["audio_clips"][1])
        action=next(a["instructions"] for a in QUICK_ACTIONS if a["kind"]=="mute")
        self.ai.runner=lambda *_:self.fail("Local command must not call AI")
        job=self.wait_job(self.ai.start(self.p["id"],self.p["revision"],action));self.assertEqual(job["status"],"done",job)
        p=self.store.get(self.p["id"]);self.assertEqual(p["audio_clips"][0]["volume"],0);self.assertEqual(p["audio_clips"][1],effect)
        p=self.store.apply(p["id"],"audio_clip_update",{"audio_id":p["audio_clips"][0]["id"],"locked":True},p["revision"])
        p=self.store.apply(p["id"],"clip_update",{"clip_id":p["timeline"][0]["id"],"locked":True},p["revision"])
        with self.assertRaises(EditorError):self.ai.start(p["id"],p["revision"],action)

    def test_conversation_refines_existing_edits_and_preserves_history(self):
        for start,end in ((0,2),(2,4)):
            self.p=self.store.apply(self.p["id"],"clip_add",{"media_id":self.asset["id"],"start":start,"end":end,"brightness":1.2,"speed":1.25},self.p["revision"])
        original=copy.deepcopy(self.p["timeline"])
        def runner(project,instructions,images):
            self.assertEqual(project["conversation"],[])
            return {"summary":"Dissoluções e áudio original silenciado","warnings":[],"clips":[{**{k:c[k] for k in ("media_id","start","end","label","title","block_id")},"volume":0,"existing_clip_id":c["id"]} for c in project["timeline"]],"transition_style":{"kind":"dissolve","duration":.5}}
        self.ai.runner=runner;job=self.wait_job(self.ai.start(self.p["id"],self.p["revision"],"Suavize as transições e retire o som original"))
        self.assertEqual(job["status"],"done",job);self.assertIn("Suavize",job["request"])
        p=self.store.get(self.p["id"]);self.assertEqual(len(p["transitions"]),1)
        for clip,old in zip(p["timeline"],original):
            self.assertEqual(clip["id"],old["id"]);self.assertEqual(clip["brightness"],1.2);self.assertEqual(clip["speed"],1.25);self.assertEqual(clip["volume"],0)
        def followup(project,instructions,images):
            self.assertEqual(project["conversation"][-1]["user"],job["request"])
            self.assertEqual(project["conversation"][-1]["assistant"],job["result"]["summary"])
            return {"summary":"Mantive a edição","warnings":[],"clips":[{**c,"existing_clip_id":c["id"]} for c in project["timeline"]],"transition_style":{"kind":"keep","duration":.5}}
        self.ai.runner=followup;second=self.wait_job(self.ai.start(p["id"],p["revision"],"Mantenha essa edição"));self.assertEqual(second["status"],"done",second)
        current=self.store.get(p["id"]);self.assertEqual(current["transitions"],p["transitions"])
        current=self.store.apply(p["id"],"undo",{},current["revision"]);current=self.store.apply(p["id"],"undo",{},current["revision"])
        self.assertEqual(current["timeline"],original);self.assertEqual(current["transitions"],[])

    def test_quick_actions_use_no_codex_and_preserve_protected_audio(self):
        for start,end in ((0,1),(1,2),(2,3)):
            self.p=self.store.apply(self.p["id"],"clip_add",{"media_id":self.asset["id"],"start":start,"end":end},self.p["revision"])
        self.p=self.store.apply(self.p["id"],"clip_update",{"clip_id":self.p["timeline"][0]["id"],"locked":True},self.p["revision"])
        self.ai.runner=lambda *_:self.fail("Quick edit must not call Codex")
        for action in QUICK_ACTIONS:
            job=self.wait_job(self.ai.start(self.p["id"],self.p["revision"],action["instructions"]))
            self.assertEqual(job["status"],"done",job);self.assertEqual(job["result"]["provider"],"local");self.p=self.store.get(self.p["id"])
        self.assertEqual(self.p["timeline"][0]["volume"],1);self.assertEqual(self.p["timeline"][1]["volume"],0);self.assertEqual(len(self.p["transitions"]),1)
        self.assertEqual(self.p["last_change"]["actor"],"Lili · ajuste local")
        self.p=self.store.apply(self.p["id"],"clip_update",{"clip_id":self.p["timeline"][1]["id"],"locked":True},self.p["revision"])
        before=copy.deepcopy(self.p)
        with self.assertRaises(EditorError):self.ai.start(self.p["id"],self.p["revision"],QUICK_ACTIONS[0]["instructions"])
        self.assertEqual(self.store.get(self.p["id"]),before)

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
