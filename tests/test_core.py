import tempfile
import unittest
from pathlib import Path

from lili.core import EditorError, Store, script_blocks, uid


class ProjectTests(unittest.TestCase):
    def setUp(self):
        scratch = Path("work/tests").resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.p = self.store.create("Teste", "Chegada ao parque.\n\nCora explora o parque.")
        self.asset = {"id": uid(), "name": "cora.mov", "filename": "source.mov", "status": "ready", "kind": "video", "duration": 10, "has_audio": True, "tags": ["cora", "parque"]}
        self.store.add_media(self.p["id"], self.asset)
        self.refresh()

    def refresh(self):
        self.p = self.store.get(self.p["id"])

    def apply(self, operation, args):
        self.p = self.store.apply(self.p["id"], operation, args, self.p["revision"])
        return self.p

    def add(self):
        self.apply("clip_add", {"media_id": self.asset["id"], "start": 1, "end": 4})
        return self.p["timeline"][-1]

    def test_narration_fades_validate_atomically_and_undo(self):
        self.apply("narration_set", {"media_id": self.asset["id"]})
        original = self.p["narration"].copy()
        self.assertEqual(original["fade_in"], 0)
        revision = self.p["revision"]
        for changes in ({"fade_in": -1}, {"fade_out": 11}, {"fade_in": True},
                        {"fade_out": float("nan")}, {"fade_in": 6, "fade_out": 5}):
            with self.subTest(changes=changes), self.assertRaises(EditorError):
                self.apply("narration_set", {**original, **changes})
        self.refresh()
        self.assertEqual(self.p["revision"], revision)
        self.assertEqual(self.p["narration"], original)
        self.apply("narration_set", {**original, "fade_in": 2, "fade_out": 3})
        self.apply("undo", {})
        self.assertEqual(self.p["narration"], original)

    def test_rejects_stale_revision_without_losing_edit(self):
        revision = self.p["revision"]
        self.add()
        with self.assertRaises(EditorError) as error:
            self.store.apply(self.p["id"], "script_update", {"script": "Antigo"}, revision)
        self.assertEqual(error.exception.status, 409)
        self.refresh()
        self.assertEqual(len(self.p["timeline"]), 1)
        self.assertNotEqual(self.p["script"], "Antigo")

    def test_lock_protects_clip_from_update_removal_and_replacement(self):
        clip = self.add()
        self.apply("clip_update", {"clip_id": clip["id"], "locked": True})
        for operation, args in [("clip_update", {"clip_id": clip["id"], "end": 5}), ("clip_remove", {"clip_id": clip["id"]}), ("timeline_replace", {"clips": []})]:
            with self.subTest(operation=operation), self.assertRaises(EditorError):
                self.apply(operation, args)
        self.refresh()
        self.assertEqual(self.p["timeline"][0]["end"], 4)
        self.apply("timeline_replace", {"clips": self.p["timeline"]})
        self.apply("clip_update", {"clip_id": clip["id"], "locked": False})
        self.apply("clip_update", {"clip_id": clip["id"], "end": 5})

    def test_invalid_trim_is_atomic(self):
        clip = self.add()
        revision = self.p["revision"]
        for changes in ({"start": 5, "end": 4}, {"end": 11}, {"end": float("nan")}, {"start": True}):
            with self.subTest(changes=changes), self.assertRaises(EditorError):
                self.apply("clip_update", {"clip_id": clip["id"], **changes})
        self.refresh()
        self.assertEqual(self.p["revision"], revision)
        self.assertEqual(self.p["duration"], 3)

    def test_undo_preserves_imported_media(self):
        self.add()
        new_asset = {**self.asset, "id": uid(), "name": "outra.mov"}
        self.store.add_media(self.p["id"], new_asset)
        self.refresh()
        self.apply("undo", {})
        self.assertEqual(self.p["timeline"], [])
        self.assertEqual(len(self.p["media"]), 2)

    def test_split_preserves_duration_metadata_and_can_be_undone(self):
        clip = self.add()
        self.apply("clip_update", {"clip_id": clip["id"], "title": "Cora", "volume": 0.4, "block_id": "bloco-1"})
        original = self.p["timeline"][0].copy()
        self.apply("clip_split", {"clip_id": clip["id"], "at": 2.25})
        left, right = self.p["timeline"]
        self.assertEqual(self.p["duration"], 3)
        self.assertEqual((left["start"], left["end"], right["start"], right["end"]), (1, 2.25, 2.25, 4))
        self.assertEqual(left["id"], original["id"])
        self.assertNotEqual(right["id"], left["id"])
        for key in ("media_id", "label", "title", "volume", "block_id"):
            self.assertEqual(right[key], original[key])
        self.apply("undo", {})
        self.assertEqual(self.p["timeline"], [original])

    def test_trash_removal_cascades_only_after_confirmation_and_undo_restores_usage(self):
        clip = self.add()
        self.apply("narration_set", {"media_id": self.asset["id"]})
        with self.assertRaises(EditorError):
            self.apply("media_remove", {"media_id": self.asset["id"]})
        self.apply("media_remove", {"media_id": self.asset["id"], "remove_usage": True})
        self.assertEqual(self.p["media"], [])
        self.assertEqual(self.p["timeline"], [])
        self.assertIsNone(self.p["narration"])
        self.assertEqual(len(self.p["trash"]), 1)
        with self.assertRaises(EditorError):
            self.store.media(self.p["id"], self.asset["id"])
        for operation in ("clip_add", "narration_set", "media_annotate"):
            with self.subTest(operation=operation), self.assertRaises(EditorError):
                self.apply(operation, {"media_id": self.asset["id"]})
        newer = {**self.asset, "id": uid(), "status": "processing"}
        self.store.add_media(self.p["id"], newer)
        self.store.update_media(self.p["id"], self.asset["id"], {"note": "Preservar metadados"})
        self.refresh()
        self.apply("undo", {})
        self.assertEqual(self.p["timeline"], [clip])
        self.assertEqual(self.p["narration"]["media_id"], self.asset["id"])
        self.assertEqual(len(self.p["media"]), 2)
        self.assertEqual(self.p["media"][0]["note"], "Preservar metadados")

    def test_trash_respects_locks_and_processing_and_restore_is_library_only(self):
        clip = self.add()
        self.apply("clip_update", {"clip_id": clip["id"], "locked": True})
        with self.assertRaises(EditorError):
            self.apply("media_remove", {"media_id": self.asset["id"], "remove_usage": True})
        self.apply("clip_update", {"clip_id": clip["id"], "locked": False})
        self.apply("media_remove", {"media_id": self.asset["id"], "remove_usage": True})
        self.apply("media_restore", {"media_id": self.asset["id"]})
        self.assertEqual(len(self.p["media"]), 1)
        self.assertEqual(self.p["timeline"], [])
        self.assertEqual(self.p["trash"], [])
        self.store.update_media(self.p["id"], self.asset["id"], {"status": "processing"})
        self.refresh()
        with self.assertRaises(EditorError):
            self.apply("media_remove", {"media_id": self.asset["id"]})

    def test_invalid_or_locked_split_is_atomic(self):
        clip = self.add()
        revision = self.p["revision"]
        for at in (1, 1.09, 3.95, 4, 9, None, True):
            with self.subTest(at=at), self.assertRaises(EditorError):
                self.apply("clip_split", {"clip_id": clip["id"], "at": at})
        self.refresh()
        self.assertEqual(self.p["revision"], revision)
        self.assertEqual(len(self.p["timeline"]), 1)
        self.apply("clip_update", {"clip_id": clip["id"], "locked": True})
        with self.assertRaises(EditorError):
            self.apply("clip_split", {"clip_id": clip["id"], "at": 2})

    def test_agent_and_manual_edits_share_state_after_restart(self):
        clip = self.add()
        self.p = self.store.apply(self.p["id"], "clip_update", {"clip_id": clip["id"], "title": "Cora"}, self.p["revision"], "codex")
        reread = Store(self.temp.name).get(self.p["id"])
        self.assertEqual(reread["timeline"][0]["title"], "Cora")
        self.assertEqual(reread["last_change"]["actor"], "codex")

    def test_draft_is_labeled_and_respects_locks(self):
        result = self.store.draft(self.p["id"], self.p["revision"])
        self.p = result["project"]
        self.assertEqual(result["method"], "tags_and_script_length")
        self.assertEqual(len(self.p["timeline"]), 2)
        self.assertTrue(all(c["end"] <= 10 for c in self.p["timeline"]))
        self.apply("clip_update", {"clip_id": self.p["timeline"][0]["id"], "locked": True})
        with self.assertRaises(EditorError):
            self.store.draft(self.p["id"], self.p["revision"])

    def test_blocks_keep_script_order(self):
        self.assertEqual([b["text"] for b in script_blocks("A\n\nB\ncom outra linha\n\nC")], ["A", "B\ncom outra linha", "C"])

    def test_duplicate_is_editable_preserves_protected_original_and_can_be_undone(self):
        clip = self.add()
        self.apply("clip_update", {"clip_id": clip["id"], "locked": True, "title": ""})
        original = self.p["timeline"][0].copy()
        self.apply("clip_duplicate", {"clip_id": clip["id"]})
        left, right = self.p["timeline"]
        self.assertEqual(left, original)
        self.assertFalse(right["locked"])
        self.assertNotEqual(left["id"], right["id"])
        self.assertEqual((left["start"], left["end"]), (right["start"], right["end"]))
        self.apply("clip_update", {"clip_id": right["id"], "end": 5})
        self.apply("undo", {})
        self.apply("undo", {})
        self.assertEqual(self.p["timeline"], [original])

    def test_requests_remain_pending_until_agent_completes(self):
        self.apply("request_add", {"text": "Trocar a abertura"})
        request = self.p["requests"][0]
        self.assertEqual(request["status"], "pending")
        self.apply("request_complete", {"request_id": request["id"], "result": "Abertura atualizada"})
        self.assertEqual(self.p["requests"][0]["status"], "done")

    def test_visual_fades_are_atomic_undoable_and_preserve_split_edges(self):
        clip = self.add()
        for changes in ({"fade_in": True}, {"fade_out": -1}, {"fade_in": 2, "fade_out": 2}):
            rev = self.p["revision"]
            with self.assertRaises(EditorError): self.apply("clip_update", {"clip_id": clip["id"], **changes})
            self.refresh(); self.assertEqual(self.p["revision"], rev)
        self.apply("clip_update", {"clip_id": clip["id"], "fade_in": .4, "fade_out": .5})
        self.apply("clip_split", {"clip_id": clip["id"], "at": 2.5})
        left, right = self.p["timeline"]
        self.assertEqual((left["fade_in"], left["fade_out"], right["fade_in"], right["fade_out"]), (.4, 0, 0, .5))
        self.apply("undo", {})
        self.assertEqual(len(self.p["timeline"]), 1)
        self.assertEqual(self.p["timeline"][0]["fade_out"], .5)

    def test_caption_styles_validate_preserve_on_duplicate_and_undo(self):
        clip=self.add()
        for key in ("title_font", "title_size", "title_position"):
            with self.assertRaises(EditorError):self.apply("clip_update", {"clip_id":clip["id"],key:"invalid"})
        self.apply("clip_update", {"clip_id":clip["id"],"title":"Legenda manual","title_font":"serif","title_size":"large","title_position":"bottom"})
        self.apply("clip_duplicate", {"clip_id":clip["id"]})
        self.assertEqual(self.p["timeline"][1]["title_font"],"serif")
        self.assertEqual(self.p["timeline"][1]["title_position"],"bottom")
        self.apply("undo",{});self.apply("undo",{})
        self.assertEqual(self.p["timeline"][0]["title"],"")

    def test_canvas_format_updates_are_atomic_and_undoable(self):
        original=self.p["settings"].copy()
        with self.assertRaises(EditorError):self.apply("settings_update",{"format":"bad"})
        self.apply("settings_update",{"format":"square"})
        self.assertEqual((self.p["settings"]["width"],self.p["settings"]["height"]),(1080,1080))
        self.apply("undo",{});self.assertEqual(self.p["settings"],original)


if __name__ == "__main__":
    unittest.main()
