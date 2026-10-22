import tempfile
import unittest
from pathlib import Path
import stat
from types import SimpleNamespace
from unittest.mock import patch
from lili.core import Store, EditorError, uid

class TrashTests(unittest.TestCase):
    def setUp(self):
        base=Path("work/tests");base.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.p=self.store.create("Descartável")
        self.assets=[]
        for i in range(2):
            asset={"id":uid(),"name":f"take{i}.mov","filename":f"take{i}.mov","status":"ready","kind":"video","duration":10,"has_audio":True}
            self.store.add_media(self.p["id"],asset);self.assets.append(asset)
        self.refresh()

    def refresh(self):self.p=self.store.get(self.p["id"])
    def edit(self,op,args):
        self.p=self.store.apply(self.p["id"],op,args,self.p["revision"])

    def test_bulk_remove_and_single_undo_restore_timeline_voice_and_library(self):
        for asset in self.assets:self.edit("clip_add",{"media_id":asset["id"]})
        self.edit("narration_set",{"media_id":self.assets[1]["id"],"fade_in":1})
        before=self.p
        self.edit("media_remove_many",{"media_ids":[a["id"] for a in self.assets],"remove_usage":True})
        self.assertEqual(self.p["media"],[]);self.assertEqual(len(self.p["trash"]),2)
        self.assertEqual(self.p["timeline"],[]);self.assertIsNone(self.p["narration"])
        self.edit("undo",{})
        for field in ("media","timeline","narration"):self.assertEqual(self.p[field],before[field])

    def test_invalid_bulk_or_protected_scene_never_partially_deletes(self):
        a,b=[a["id"] for a in self.assets]
        self.edit("clip_add",{"media_id":b,"locked":True})
        revision=self.p["revision"]
        for ids in ([a,b],[a,uid()],[a,a],[],"all",[None]):
            with self.subTest(ids=ids),self.assertRaises(EditorError):
                self.edit("media_remove_many",{"media_ids":ids,"remove_usage":True})
            self.refresh();self.assertEqual(self.p["revision"],revision)
            self.assertEqual(len(self.p["media"]),2)

    def test_bulk_requires_usage_confirmation(self):
        self.edit("clip_add",{"media_id":self.assets[0]["id"]})
        with self.assertRaises(EditorError):
            self.edit("media_remove_many",{"media_ids":[self.assets[0]["id"]]})
        self.refresh();self.assertEqual(len(self.p["media"]),2)

    def test_project_trash_restore_survives_restart_and_preserves_source(self):
        folder=self.store.folder(self.p["id"]);source=folder/"original-test.mov";source.write_bytes(b"preserve")
        self.edit("clip_add",{"media_id":self.assets[0]["id"],"locked":True})
        timeline=self.p["timeline"]
        self.store.project_trash(self.p["id"],self.p["revision"])
        self.store=Store(self.temp.name)
        self.assertEqual(self.store.list(),[])
        trashed=self.store.list(trash=True);self.assertEqual(len(trashed),1)
        with self.assertRaises(EditorError):self.store.get(self.p["id"])
        with self.assertRaises(EditorError):self.edit("script_update",{"script":"changed"})
        with self.assertRaises(EditorError):self.store.project_trash(self.p["id"],self.p["revision"],restore=True)
        self.store.project_trash(self.p["id"],trashed[0]["revision"],restore=True)
        self.refresh();self.assertEqual(self.p["timeline"],timeline)
        self.assertEqual(source.read_bytes(),b"preserve")
        self.assertEqual(len(self.store.list()),1);self.assertEqual(self.store.list(trash=True),[])

    def test_project_trash_rejects_processing_and_stale_revision(self):
        self.store.update_media(self.p["id"],self.assets[0]["id"],{"status":"processing"})
        with self.assertRaises(EditorError):self.store.project_trash(self.p["id"],self.p["revision"])
        self.refresh()
        with self.assertRaises(EditorError):self.store.project_trash(self.p["id"],self.p["revision"])
        self.assertEqual(len(self.store.list()),1)

    def test_permanent_delete_requires_trash_confirmation_and_current_revision(self):
        folder=self.store.folder(self.p['id'])
        with self.assertRaises(EditorError):self.store.purge_project(self.p['id'],self.p['revision'],'EXCLUIR')
        hidden=self.store.project_trash(self.p['id'],self.p['revision'])
        for revision,confirmation in ((hidden['revision'],'excluir'),(hidden['revision'],None),(hidden['revision']-1,'EXCLUIR'),(True,'EXCLUIR')):
            with self.subTest(revision=revision,confirmation=confirmation),self.assertRaises(EditorError):
                self.store.purge_project(self.p['id'],revision,confirmation)
            self.assertTrue(folder.exists())

    def test_permanent_delete_removes_only_the_selected_project_files(self):
        folder=self.store.folder(self.p['id'])
        external=Path(self.temp.name)/'downloads-original.mov';external.write_bytes(b'outside')
        other=self.store.create('Outro projeto');other_folder=self.store.folder(other['id'])
        for name in ('media/original.mov','media/proxy.mp4','exports/job/video.mp4'):
            f=folder/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'synthetic video bytes')
        hidden=self.store.project_trash(self.p['id'],self.p['revision'])
        result=self.store.purge_project(self.p['id'],hidden['revision'],'EXCLUIR')
        self.assertTrue(result['permanent']);self.assertGreater(result['removed_bytes'],60)
        self.assertFalse(folder.exists());self.assertTrue(other_folder.exists());self.assertEqual(external.read_bytes(),b'outside')
        self.assertEqual(self.store.list(trash=True),[])
        with self.assertRaises(EditorError):self.store.project_trash(self.p['id'],hidden['revision'],restore=True)

    def test_reparse_point_in_project_blocks_deletion_before_any_file_is_removed(self):
        folder=self.store.folder(self.p['id']);link=folder/'external-link';link.write_bytes(b'keep')
        hidden=self.store.project_trash(self.p['id'],self.p['revision'])
        original=Path.lstat
        def lstat(path,*args,**kwargs):
            if path==link:return SimpleNamespace(st_mode=stat.S_IFDIR,st_file_attributes=0x400,st_size=0)
            return original(path,*args,**kwargs)
        with patch.object(Path,'lstat',lstat),patch('lili.core.shutil.rmtree') as remove:
            with self.assertRaises(EditorError):self.store.purge_project(self.p['id'],hidden['revision'],'EXCLUIR')
            remove.assert_not_called()
        self.assertEqual(link.read_bytes(),b'keep');self.assertTrue((folder/'project.json').exists())

    def test_permanent_delete_rejects_paths_outside_project_ids(self):
        for value in ('..','../outside','',None,'0'*31):
            with self.subTest(value=value),self.assertRaises(EditorError):self.store.purge_project(value,1,'EXCLUIR')
        self.assertTrue(self.store.folder(self.p['id']).exists())
