import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from lili.core import Store
from lili.remote import RemoteServer
from lili.server import EditorServer


class RemoteTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('work/tests').resolve()
        scratch.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch)
        self.root=Path(self.temp.name)
        self.editor=EditorServer(('127.0.0.1',0),Store(self.root/'projects'))
        self.remote=RemoteServer(('127.0.0.1',0),self.root/'remote',self.editor.server_port)
        self.threads=[]
        for server in (self.editor,self.remote):
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start();self.threads.append(thread)
        self.origin=f'http://127.0.0.1:{self.remote.server_port}'
        self.password='a-test-password-only-29'
        self.cookie=''

    def tearDown(self):
        for server in (self.remote,self.editor):
            server.shutdown();server.server_close()
        self.editor.media.pool.shutdown(wait=True)
        for thread in self.threads:thread.join(timeout=3)
        self.temp.cleanup()

    def request(self,path,method='GET',data=None,headers=None):
        hdr={'Origin':self.origin,**(headers or {})}
        if self.cookie:hdr['Cookie']=self.cookie
        if isinstance(data,dict):
            data=urlencode(data);hdr['Content-Type']='application/x-www-form-urlencoded'
        conn=http.client.HTTPConnection('127.0.0.1',self.remote.server_port,timeout=15)
        try:
            conn.request(method,path,body=data,headers=hdr)
            r=conn.getresponse()
            return r.status,dict(r.getheaders()),r.read()
        finally:conn.close()

    def setup_login(self):
        status,_,_=self.request('/auth/setup','POST',{'username':'elisa','password':self.password,'confirmation':self.password})
        self.assertEqual(status,303)
        status,headers,_=self.request('/auth/login','POST',{'username':'elisa','password':self.password})
        self.assertEqual(status,303)
        self.cookie=headers['Set-Cookie'].split(';')[0]
        self.assertIn('HttpOnly',headers['Set-Cookie'])
        self.assertIn('SameSite=Strict',headers['Set-Cookie'])

    def test_login_protects_project_api_media_and_survives_proxy(self):
        self.setup_login()
        config=(self.root/'remote/auth.json').read_text()
        self.assertNotIn(self.password,config)
        status,_,body=self.request('/api/projects')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body),[])
        status,_,body=self.request('/api/projects','POST',json.dumps({'name':'Pelo celular'}),{'Content-Type':'application/json'})
        self.assertEqual(status,201)
        self.assertEqual(json.loads(body)['name'],'Pelo celular')
        self.cookie=''
        for path in ('/api/projects','/api/projects/123/media/456/proxy','/api/projects/123/exports/456/video.mp4'):
            self.assertEqual(self.request(path)[0],401)

    def test_wrong_password_origin_forwarded_headers_and_logout(self):
        self.setup_login()
        self.assertEqual(self.request('/auth/setup')[0],404)
        self.assertEqual(self.request('/api/projects','POST','{}',{'Origin':'https://evil.example','Content-Type':'application/json'})[0],403)
        status,_,_=self.request('/auth/logout','POST','')
        self.assertEqual(status,303)
        self.assertEqual(self.request('/api/projects')[0],401)
        self.cookie=''
        self.assertEqual(self.request('/api/projects',headers={'X-Forwarded-For':'127.0.0.1','X-Forwarded-Host':'localhost','Tailscale-User-Login':'elisa'})[0],401)
        self.assertEqual(self.request('/auth/login','POST',{'username':'elisa','password':'incorrect'})[0],401)

    def test_remote_cookie_is_secure_and_setup_never_public(self):
        (self.root/'remote/public-url.txt').write_text('https://test.trycloudflare.com')
        hdr={'Host':'test.trycloudflare.com','Origin':'https://test.trycloudflare.com'}
        self.assertEqual(self.request('/auth/setup',headers=hdr)[0],404)
        self.setup_login()
        status,headers,_=self.request('/auth/login','POST',{'username':'elisa','password':self.password},hdr)
        self.assertEqual(status,303)
        self.assertIn('; Secure',headers['Set-Cookie'])
        self.assertEqual(self.request('/',headers={'Host':'unexpected.example'})[0],403)

    def test_rate_limit(self):
        self.setup_login()
        self.cookie=''
        for _ in range(8):self.assertEqual(self.request('/auth/login','POST',{'username':'elisa','password':'incorrect'})[0],401)
        self.assertEqual(self.request('/auth/login','POST',{'username':'elisa','password':self.password})[0],429)


if __name__=='__main__':unittest.main()
