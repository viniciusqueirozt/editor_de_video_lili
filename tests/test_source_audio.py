import copy
import tempfile
import unittest
from pathlib import Path
from lili.core import Store,EditorError,uid

class SourceAudioTests(unittest.TestCase):
    def setUp(self):
        root=Path("work/tests");root.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name);self.p=self.store.create("Synthetic independent audio","")
        self.asset={"id":uid(),"name":"sound.mp4","filename":"sound.mp4","kind":"video","duration":10,"has_audio":True,"status":"ready"}
        self.store.add_media(self.p["id"],self.asset);self.p=self.store.get(self.p["id"])
    def command(self,op,args):
        self.p=self.store.apply(self.p["id"],op,args,self.p["revision"]);return self.p
    def insert(self,**extra):
        self.command("clip_add",{"media_id":self.asset["id"],"start":1,"end":5,"speed":2,"volume":.6,"audio_fade_in":.2,"audio_fade_out":.3,"separate_audio":True,**extra})
        return self.p["audio_clips"][-1]
    def test_new_scene_creates_independent_aligned_audio_atomically(self):
        self.command("clip_add",{"media_id":self.asset["id"],"start":0,"end":2})
        sound=copy.deepcopy(self.insert());clip=copy.deepcopy(self.p["timeline"][-1])
        self.assertTrue(clip["audio_detached"]);self.assertEqual(sound["offset"],2);self.assertEqual(sound["speed"],2)
        self.assertEqual((sound["start"],sound["end"],sound["volume"]),(1,5,.6));self.assertEqual(sound["source_clip_id"],clip["id"])
        self.command("clip_update",{"clip_id":clip["id"],"start":2,"audio_fade_in":0})
        self.assertEqual(self.p["audio_clips"][0],sound)
        current=copy.deepcopy(self.p["timeline"])
        self.command("audio_clip_update",{"audio_id":sound["id"],"start":1.5,"end":4,"speed":1.25,"offset":.5,"volume":.2})
        self.assertEqual(self.p["timeline"],current);self.assertEqual(self.p["audio_clips"][0]["volume"],.2)
        self.command("undo",{});self.assertEqual(self.p["audio_clips"][0],sound)
        self.command("redo",{});self.assertEqual(self.p["audio_clips"][0]["offset"],.5)
    def test_audio_split_duplicate_remove_never_rewrites_video(self):
        sound=self.insert();video=copy.deepcopy(self.p["timeline"])
        self.command("audio_clip_split",{"audio_id":sound["id"],"at":3})
        left,right=self.p["audio_clips"];self.assertEqual((left["start"],left["end"],right["start"],right["end"]),(1,3,3,5))
        self.assertEqual(right["offset"],1);self.assertEqual(left["fade_out"],0);self.assertEqual(right["fade_in"],0)
        self.command("audio_clip_duplicate",{"audio_id":right["id"]});self.assertEqual(self.p["audio_clips"][-1]["offset"],2)
        self.command("audio_clip_remove",{"audio_id":left["id"]});self.assertEqual(self.p["timeline"],video)
        self.command("clip_remove",{"clip_id":video[0]["id"]});self.assertEqual(len(self.p["audio_clips"]),2)
    def test_legacy_read_is_unchanged_and_detach_is_one_undo(self):
        self.command("clip_add",{"media_id":self.asset["id"],"start":2,"end":4,"volume":.7})
        target=self.store.folder(self.p["id"])/"project.json";raw=target.read_bytes();self.store.get(self.p["id"]);self.assertEqual(target.read_bytes(),raw)
        old=copy.deepcopy(self.p["timeline"]);self.command("audio_detach",{"clip_id":old[0]["id"],"offset":.5})
        self.assertEqual(len(self.p["audio_clips"]),1);self.assertEqual(self.p["audio_clips"][0]["offset"],.5)
        with self.assertRaises(EditorError):self.command("audio_detach",{"clip_id":old[0]["id"]})
        self.command("undo",{});self.assertEqual(self.p["audio_clips"],[]);self.assertEqual(self.p["timeline"],old)
    def test_detach_then_split_is_atomic_and_undoable(self):
        self.command("clip_add",{"media_id":self.asset["id"],"start":0,"end":4})
        clip=self.p["timeline"][0]
        self.command("audio_detach",{"clip_id":clip["id"],"then":"split","at":2})
        self.assertEqual(len(self.p["audio_clips"]),2);self.command("undo",{});self.assertEqual(self.p["audio_clips"],[])
        before=copy.deepcopy(self.p)
        with self.assertRaises(EditorError):self.command("audio_detach",{"clip_id":clip["id"],"then":"split","at":.01})
        self.assertEqual(self.store.get(self.p["id"]),before)
    def test_invalid_audio_updates_and_locks_are_atomic(self):
        sound=self.insert();before=copy.deepcopy(self.p)
        for changes in ({"start":True},{"start":-1},{"end":11},{"end":1.01},{"speed":0},{"speed":float("nan")},{"offset":1801},{"volume":3},{"fade_in":2,"fade_out":2},{"locked":"yes"}):
            with self.assertRaises(EditorError):self.command("audio_clip_update",{"audio_id":sound["id"],**changes})
            self.assertEqual(self.store.get(self.p["id"]),before)
        self.command("audio_clip_update",{"audio_id":sound["id"],"locked":True});before=copy.deepcopy(self.p)
        with self.assertRaises(EditorError):self.command("audio_clip_remove",{"audio_id":sound["id"]})
        self.assertEqual(self.store.get(self.p["id"]),before)
        self.command("audio_clip_update",{"audio_id":sound["id"],"locked":False})
    def test_media_removal_accounts_for_audio_even_after_video_is_removed(self):
        sound=self.insert();self.command("clip_remove",{"clip_id":self.p["timeline"][0]["id"]});before=copy.deepcopy(self.p)
        with self.assertRaises(EditorError):self.command("media_remove",{"media_id":self.asset["id"]})
        self.assertEqual(self.store.get(self.p["id"]),before)
        self.command("media_remove",{"media_id":self.asset["id"],"remove_usage":True});self.assertEqual(self.p["audio_clips"],[])
        self.command("undo",{});self.assertEqual(self.p["audio_clips"][0],sound)
    def test_old_history_defaults_audio_to_empty_and_cannot_reenable_embedded_sound(self):
        sound=self.insert();before=copy.deepcopy(self.p)
        clip={**self.p["timeline"][0],"audio_detached":False}
        with self.assertRaises(EditorError):self.command("timeline_replace",{"clips":[clip]})
        self.assertEqual(self.store.get(self.p["id"]),before)
        raw=self.store._read(self.p["id"])
        for item in raw["history"]:item.pop("audio_clips",None)
        self.store._write(raw);self.command("undo",{});self.assertEqual(self.p["audio_clips"],[])

    def test_audio_fades_do_not_constrain_detached_image_cuts(self):
        self.command("clip_add",{"media_id":self.asset["id"],"start":0,"end":4,"audio_fade_in":1,"audio_fade_out":1,"separate_audio":True})
        sound=copy.deepcopy(self.p["audio_clips"])
        self.assertEqual(sound[0]["fade_in"],1);self.assertEqual(sound[0]["fade_out"],1)
        clip=self.p["timeline"][0]
        self.command("clip_update",{"clip_id":clip["id"],"end":.1})
        self.assertEqual(self.p["timeline"][0]["end"],.1);self.assertEqual(self.p["audio_clips"],sound)
