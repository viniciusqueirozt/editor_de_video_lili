"""Contract of the existing atomic API used by subtitle organization."""
import copy
import tempfile
import unittest
from pathlib import Path
from lili.core import Store, EditorError, uid
from lili.subtitles import to_srt, parse_srt

class CaptionOrganizationTests(unittest.TestCase):
    def setUp(self):
        root=Path("work/tests").resolve();root.mkdir(parents=True,exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=root);self.addCleanup(temp.cleanup)
        self.store=Store(temp.name);p=self.store.create("Synthetic subtitle tools")
        self.pid=p["id"]
        self.asset={"id":uid(),"name":"synthetic.mov","filename":"synthetic.mov","status":"ready","kind":"video","duration":5,"has_audio":True}
        self.store.add_media(self.pid,self.asset)
        self.command("clip_add",{"media_id":self.asset["id"],"start":0,"end":5})
        self.command("narration_set",{"media_id":self.asset["id"],"offset":0})
        self.rows=[{"id":uid(),"start":.2,"end":1.2,"text":"Olá Cora","title_font":"serif"},{"id":uid(),"start":1.5,"end":2.5,"text":"Outro passeio"}]
        self.command("captions_replace",{"captions":self.rows})
    def command(self,op,args):
        p=self.store.get(self.pid)
        return self.store.apply(self.pid,op,args,p["revision"])
    def test_split_merge_shift_are_atomic_reversible_and_keep_other_tracks(self):
        before=self.store.get(self.pid);a,b=before["captions"]
        proposals=[
            [{**a,"end":.7,"text":"Olá"},{**a,"id":uid(),"start":.7,"text":"Cora"},b],
            [{**a,"end":b["end"],"text":a["text"]+" "+b["text"]}],
            [{**c,"start":c["start"]+.3,"end":c["end"]+.3} for c in before["captions"]],
        ]
        for proposal in proposals:
            with self.subTest(proposal=proposal):
                saved=self.command("captions_replace",{"captions":proposal})
                for key in ("timeline","narration","music","audio_clips","media"):
                    self.assertEqual(saved.get(key),before.get(key))
                decoded=parse_srt(to_srt(saved["captions"]))
                self.assertEqual([(c["start"],c["end"],c["text"]) for c in decoded],[(c["start"],c["end"],c["text"]) for c in saved["captions"]])
                undone=self.command("undo",{})
                self.assertEqual(undone["captions"],before["captions"])
                redone=self.command("redo",{})
                self.assertEqual(redone["captions"],saved["captions"])
                self.command("undo",{})
    def test_invalid_and_stale_proposals_never_mutate_saved_state(self):
        before=self.store.get(self.pid)
        for bad in ([{**before["captions"][0],"start":-1}], [{**before["captions"][0],"end":.21}], [before["captions"][0],{**before["captions"][1],"start":.8}]):
            with self.assertRaises(EditorError): self.command("captions_replace",{"captions":bad})
            self.assertEqual(self.store.get(self.pid)["revision"],before["revision"])
            self.assertEqual(self.store.get(self.pid)["captions"],before["captions"])
        with self.assertRaises(EditorError):
            self.store.apply(self.pid,"captions_replace",{"captions":[]},before["revision"]-1)
        self.assertEqual(self.store.get(self.pid)["captions"],before["captions"])

    def test_browser_assets_are_available_through_the_editor_routes(self):
        import threading
        from urllib.request import urlopen
        from lili.server import EditorServer
        server=EditorServer(("127.0.0.1",0),self.store)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}"
            for path,kind in (("caption-tools.js","javascript"),("caption-tools-ui.js","javascript"),("caption-tools.css","css")):
                with urlopen(base+"/"+path,timeout=5) as response:
                    self.assertEqual(response.status,200)
                    self.assertIn(kind,response.headers["Content-Type"])
                    self.assertGreater(len(response.read()),500)
            with urlopen(base+"/editor",timeout=5) as response:
                html=response.read().decode()
            self.assertIn('id="caption-tools-dialog"',html)
            self.assertLess(html.index('/caption-tools.js'),html.index('/caption-tools-ui.js'))
        finally:
            server.shutdown();server.server_close();server.media.pool.shutdown(wait=True);worker.join(timeout=5)
