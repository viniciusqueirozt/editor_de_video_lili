import tempfile
import unittest
from pathlib import Path
from lili.core import Store, EditorError, uid
from lili.transitions import clean_transitions, clip_transition_filters

class TransitionTests(unittest.TestCase):
    def setUp(self):
        root=Path("work/tests");root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.p=self.store.create("Synthetic transitions", "")
        asset={"id":uid(),"name":"synthetic.mp4","filename":"synthetic.mp4","duration":10,"status":"ready","kind":"video","has_audio":False}
        self.store.add_media(self.p["id"],asset);self.p=self.store.get(self.p["id"])
        for _ in range(3): self.command("clip_add",{"media_id":asset["id"],"start":0,"end":2})
        self.a,self.b,self.c=[c["id"] for c in self.p["timeline"]]
    def command(self,op,args):
        self.p=self.store.apply(self.p["id"],op,args,self.p["revision"]);return self.p
    def transition(self,**args):
        return self.command("transition_set",{"left":self.a,"right":self.b,"kind":"white","duration":.8,**args})
    def test_pair_history_duration_and_removal(self):
        self.transition();self.assertEqual(self.p["duration"],6)
        self.assertEqual(self.p["transitions"][0]["kind"],"white")
        self.command("undo",{});self.assertEqual(self.p["transitions"],[])
        self.command("redo",{});self.assertEqual(len(self.p["transitions"]),1)
        self.transition(kind="none");self.assertEqual(self.p["transitions"],[])
        self.command("undo",{});self.assertEqual(len(self.p["transitions"]),1)
    def test_dissolve_bulk_preserves_clock_and_protected_pairs(self):
        self.command("clip_update",{"clip_id":self.a,"locked":True})
        baseline=self.p["timeline"]
        self.command("transition_set",{"all":True,"kind":"dissolve","duration":.6})
        self.assertEqual(self.p["timeline"],baseline);self.assertEqual(self.p["duration"],6)
        self.assertEqual(self.p["transitions"],[{"left":self.b,"right":self.c,"kind":"dissolve","duration":.6}])
        self.command("undo",{});self.assertEqual(self.p["transitions"],[])
        self.command("redo",{});self.assertEqual(len(self.p["transitions"]),1)
        before=self.store.get(self.p["id"])
        with self.assertRaises(EditorError):self.command("timeline_replace",{"clips":self.p["timeline"],"transition_style":{"kind":[]}})
        self.assertEqual(self.store.get(self.p["id"]),before)

    def test_invalid_commands_are_atomic(self):
        for args in ({"left":self.a,"right":self.c},{"kind":[]},{"kind":"unsupported"},{"duration":True},{"duration":float("nan")},{"duration":float("inf")},{"duration":-.1},{"duration":2.1}):
            before=self.store.get(self.p["id"])
            with self.assertRaises(EditorError):self.transition(**args)
            self.assertEqual(self.store.get(self.p["id"]),before)
    def test_either_protected_scene_blocks_change(self):
        for clip in (self.a,self.b):
            self.command("clip_update",{"clip_id":clip,"locked":True})
            with self.assertRaises(EditorError):self.transition()
            self.command("clip_update",{"clip_id":clip,"locked":False})
    def test_reorder_remove_and_undo_keep_pair_identity(self):
        self.transition();self.command("clip_move",{"clip_id":self.b,"index":2});self.assertEqual(self.p["transitions"],[])
        self.command("undo",{});self.assertEqual(len(self.p["transitions"]),1)
        self.command("clip_remove",{"clip_id":self.a});self.assertEqual(self.p["transitions"],[])
        self.command("undo",{});self.assertEqual(len(self.p["transitions"]),1)
    def test_shortening_and_speed_bound_duration_without_shifting_tracks(self):
        self.transition(duration=2)
        self.command("clip_update",{"clip_id":self.a,"speed":4})
        self.assertEqual(self.p["transitions"][0]["duration"],.5)
        self.assertEqual(self.p["duration"],4.5)
        self.command("undo",{});self.assertEqual(self.p["transitions"][0]["duration"],2)
    def test_two_junctions_do_not_overlap_inside_middle_scene(self):
        self.transition(duration=2)
        self.transition(left=self.b,right=self.c,kind="black",duration=2)
        filters=clip_transition_filters(self.p,1)
        self.assertIn("fade=t=in:st=0:d=1.0:color=white",filters)
        self.assertIn("fade=t=out:st=1.0:d=1.0:color=black",filters)
        self.assertEqual(self.p["duration"],6)
    def test_legacy_project_and_old_history_default_to_no_transitions(self):
        raw=self.store._read(self.p["id"]);raw.pop("transitions",None)
        for snapshot in raw["history"]:snapshot.pop("transitions",None)
        self.store._write(raw);self.p=self.store.get(self.p["id"])
        self.assertEqual(self.p["transitions"],[])
        self.command("undo",{});self.assertEqual(self.p["transitions"],[])
        self.command("redo",{});self.assertEqual(self.p["transitions"],[])

    def test_neighbor_edit_cannot_indirectly_change_a_protected_transition(self):
        self.transition(duration=2)
        self.command("clip_update",{"clip_id":self.a,"locked":True})
        for op,args in (("clip_update",{"clip_id":self.b,"speed":4}),("clip_remove",{"clip_id":self.b}),("clip_move",{"clip_id":self.b,"index":2})):
            before=self.store.get(self.p["id"])
            with self.assertRaises(EditorError):self.command(op,args)
            self.assertEqual(self.store.get(self.p["id"]),before)
        self.command("clip_update",{"clip_id":self.b,"label":"Allowed: same junction"})
        self.command("clip_update",{"clip_id":self.a,"locked":False})
        self.command("clip_update",{"clip_id":self.b,"speed":4})
        self.assertEqual(self.p["transitions"][0]["duration"],.5)
