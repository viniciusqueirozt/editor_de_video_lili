import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from lili.access import Principal
from lili.client import Client
from lili.core import Store,uid
from lili.server import EditorServer

A="a"*48
B="b"*48

class AccessHTTPTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('work/tests');scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.identity=Principal(A)
        # Test-owned identity provider, deliberately independent of all headers.
        self.server=EditorServer(('127.0.0.1',0),self.store,identity_resolver=lambda _:self.identity)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.server.media.pool.shutdown(wait=True);self.thread.join(timeout=3)

    def request(self,path,method='GET',data=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            body=json.dumps(data) if data is not None else None
            conn.request(method,path,body,headers={'Content-Type':'application/json',**(headers or {})})
            r=conn.getresponse();raw=r.read()
            return r.status,json.loads(raw) if r.getheader('Content-Type','').startswith('application/json') else raw
        finally:conn.close()

    def create(self):
        status,p=self.request('/api/projects','POST',{'name':'Projeto privado','owner_id':B})
        self.assertEqual(status,201);return p

    def grant(self,p,permissions):
        self.identity=Principal(A)
        status,sharing=self.request(f"/api/projects/{p['id']}/sharing")
        self.assertEqual(status,200)
        status,result=self.request(f"/api/projects/{p['id']}/sharing",'POST',{'subject':B,'permissions':permissions,'expected_revision':sharing['revision']})
        self.assertEqual(status,200,result);return result

    def test_private_listing_and_all_project_paths_reject_other_users(self):
        p=self.create();self.identity=Principal(B);other=self.create()
        status,rows=self.request('/api/projects');self.assertEqual([x['id'] for x in rows],[other['id']])
        for suffix in ('','/context','/jobs','/sharing','/media/'+uid()+'/original','/exports/'+uid()+'/video.mp4'):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.request(f"/api/projects/{p['id']}"+suffix,headers={'X-Lili-User-Id':A,'X-Owner-Id':A})[0],404)
        for op in ('commands','uploads','draft','ai-edit','exports','trash','restore','purge','sharing'):
            with self.subTest(operation=op):self.assertEqual(self.request(f"/api/projects/{p['id']}/{op}",'POST',{'expected_revision':p['revision'],'confirmation':'EXCLUIR'})[0],404)
        self.identity=Principal(A)
        sharing=self.request(f"/api/projects/{p['id']}/sharing")[1]
        self.assertEqual(sharing['owner_id'],A) # Browser owner_id was ignored.
        self.assertNotIn('access',self.request(f"/api/projects/{p['id']}")[1])

    def test_view_download_edit_and_revoke_are_independent(self):
        p=self.create();folder=self.store.folder(p['id'])/'media';folder.mkdir()
        asset={'id':uid(),'name':'Sintético','filename':'source.mp4','proxy':'proxy.mp4','status':'ready','kind':'video','duration':1,'has_audio':False}
        (folder/'source.mp4').write_bytes(b'original');(folder/'proxy.mp4').write_bytes(b'preview')
        self.store.add_media(p['id'],asset)
        job=uid();export=self.store.folder(p['id'])/'exports'/job;export.mkdir(parents=True);(export/'video.mp4').write_bytes(b'final')
        self.server.media.jobs[job]={'id':job,'project_id':p['id'],'kind':'export','status':'done'}
        self.grant(p,['view']);self.identity=Principal(B)
        self.assertEqual(self.request(f"/api/projects/{p['id']}/media/{asset['id']}/proxy"),(200,b'preview'))
        self.assertEqual(self.request(f"/api/projects/{p['id']}/media/{asset['id']}/original")[0],404)
        self.assertEqual(self.request(f"/api/projects/{p['id']}/exports/{job}/video.mp4")[0],404)
        self.assertEqual(self.request(f"/api/projects/{p['id']}/commands",'POST',{})[0],404)
        self.grant(p,['view','download_exports']);self.identity=Principal(B)
        self.assertEqual(self.request(f"/api/projects/{p['id']}/exports/{job}/video.mp4"),(200,b'final'))
        self.assertEqual(self.request(f"/api/projects/{p['id']}/media/{asset['id']}/original")[0],404)
        self.grant(p,['view','edit','download_sources']);self.identity=Principal(B)
        self.assertEqual(self.request(f"/api/projects/{p['id']}/media/{asset['id']}/original"),(200,b'original'))
        fresh=self.request(f"/api/projects/{p['id']}")[1]
        status,changed=self.request(f"/api/projects/{p['id']}/commands",'POST',{'operation':'script_update','args':{'script':'Revisado'},'expected_revision':fresh['revision'],'actor':'owner'})
        self.assertEqual(status,200);self.assertEqual(changed['last_change']['actor'],'user:'+B)
        for action in ('sharing','trash','restore','purge'):
            self.assertEqual(self.request(f"/api/projects/{p['id']}/{action}",'POST',{})[0],404)
        self.grant(p,[]);self.identity=Principal(B)
        for path in (f"/api/projects/{p['id']}",f"/api/projects/{p['id']}/media/{asset['id']}/proxy",f"/api/jobs/{job}"):
            self.assertEqual(self.request(path)[0],404)

    def test_missing_identity_and_unassigned_legacy_projects_fail_closed(self):
        legacy=self.store.create('Legado sem dono')
        self.assertEqual(self.request('/api/projects')[1],[])
        self.assertEqual(self.request(f"/api/projects/{legacy['id']}")[0],404)
        self.identity=None
        self.assertEqual(self.request('/api/projects',headers={'X-Lili-User-Id':A})[0],401)

    def test_invalid_permissions_are_atomic_and_undo_cannot_regrant_access(self):
        p=self.create()
        for permissions in (['edit'],['view','admin'],['view','view'],'view',[{}]):
            with self.subTest(permissions=permissions):
                status,_=self.request(f"/api/projects/{p['id']}/sharing",'POST',{'subject':B,'permissions':permissions,'expected_revision':p['revision']})
                self.assertEqual(status,400)
        self.grant(p,['view','edit'])
        self.identity=Principal(B);fresh=self.request(f"/api/projects/{p['id']}")[1]
        self.request(f"/api/projects/{p['id']}/commands",'POST',{'operation':'script_update','args':{'script':'Editado'},'expected_revision':fresh['revision']})
        self.grant(p,[]);self.identity=Principal(A)
        fresh=self.request(f"/api/projects/{p['id']}")[1]
        self.assertEqual(self.request(f"/api/projects/{p['id']}/commands",'POST',{'operation':'undo','args':{},'expected_revision':fresh['revision']})[0],200)
        self.identity=Principal(B);self.assertEqual(self.request(f"/api/projects/{p['id']}")[0],404)
        self.identity=Principal(A);fresh=self.request(f"/api/projects/{p['id']}")[1]
        self.assertEqual(self.request(f"/api/projects/{p['id']}/trash",'POST',{'expected_revision':fresh['revision']})[0],200)
        self.identity=Principal(B);self.assertEqual(self.request('/api/projects?trash=1')[1],[])
        self.identity=Principal(A);self.assertEqual(len(self.request('/api/projects?trash=1')[1]),1)

    def test_upload_cancellation_requires_edit_access_and_unblocks_project_trash(self):
        self.assertTrue(self.request("/api/health")[1]["features"]["upload_cancel"])
        p = self.create()
        base = f"/api/projects/{p['id']}"
        status, upload = self.request(base + "/uploads", "POST", {"name": "partial.mp4", "size": 6})
        self.assertEqual(status, 201)
        cancel = base + "/uploads/" + upload["upload_id"] + "/cancel"
        temporary = self.server.uploads.pending[upload["upload_id"]]["path"]
        self.assertEqual(self.request(base + "/trash", "POST", {"expected_revision": p["revision"]})[0], 409)
        self.identity = Principal(B)
        self.assertEqual(self.request(cancel, "POST", {})[0], 404)
        self.grant(p, ["view"])
        self.identity = Principal(B)
        self.assertEqual(self.request(cancel, "POST", {})[0], 404)
        self.assertTrue(temporary.exists())
        self.identity = Principal(A)
        client = Client(f"http://127.0.0.1:{self.server.server_port}")
        self.assertEqual(client.cancel_upload(p["id"], upload["upload_id"]), {"cancelled": True, "removed_bytes": 0})
        self.assertFalse(temporary.exists())
        self.assertEqual(self.request(cancel, "POST", {})[0], 404)
        current = self.request(base)[1]
        self.assertEqual(self.request(base + "/trash", "POST", {"expected_revision": current["revision"]})[0], 200)
