import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from lili.core import Store
from lili.remote import RemoteServer, RemoteHandler
from unittest.mock import patch
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

    def test_interrupted_json_forwarding_cannot_apply_a_partial_request(self):
        import socket
        from lili.server import Handler
        finished=threading.Event();original_handler=self.editor.RequestHandlerClass
        class CheckedHandler(Handler):
            def handle_request(handler):
                try:super(CheckedHandler,handler).handle_request()
                finally:finished.set()
        self.editor.RequestHandlerClass=CheckedHandler
        self.addCleanup(setattr,self.editor,'RequestHandlerClass',original_handler)
        self.setup_login();before=len(self.editor.store.list());body=b'{"name":"Interrupted proxy request"}'
        conn=http.client.HTTPConnection('127.0.0.1',self.remote.server_port,timeout=5)
        try:
            conn.putrequest('POST','/api/projects');conn.putheader('Origin',self.origin);conn.putheader('Cookie',self.cookie);conn.putheader('Content-Type','application/json');conn.putheader('Content-Length',str(len(body)+8));conn.endheaders();conn.send(body);conn.sock.shutdown(socket.SHUT_WR)
            response=conn.getresponse();response.read();self.assertEqual(response.status,400)
        finally:conn.close()
        self.assertTrue(finished.wait(3));self.assertEqual(len(self.editor.store.list()),before)

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

    def test_brand_assets_are_public_but_project_data_stays_private(self):
        self.setup_login()
        self.cookie=''
        for path,content_type in (('/favicon.svg?v=ritmo-1','image/svg+xml'),('/icon-192.png?v=ritmo-1','image/png'),('/icon-512.png?v=ritmo-1','image/png')):
            with self.subTest(path=path):
                status,headers,body=self.request(path)
                self.assertEqual(status,200)
                self.assertIn(content_type,headers['Content-Type'])
                self.assertNotIn('Set-Cookie',headers)
                self.assertTrue(body)
        for path in ('/api/projects','/api/ai/status','/api/projects/'+'a'*32+'/context'):
            with self.subTest(path=path):self.assertEqual(self.request(path)[0],401)
        self.assertEqual(self.request('/app.js')[0],303)

    def test_rate_limit(self):
        self.setup_login()
        self.cookie=''
        for _ in range(8):self.assertEqual(self.request('/auth/login','POST',{'username':'elisa','password':'incorrect'})[0],401)
        self.assertEqual(self.request('/auth/login','POST',{'username':'elisa','password':self.password})[0],429)

    def test_private_browser_form_uses_same_origin_fetch_metadata(self):
        self.setup_login()
        self.cookie=''
        form={'username':'elisa','password':self.password}
        self.assertEqual(self.request('/auth/login','POST',form,{'Origin':'null','Sec-Fetch-Site':'same-origin'})[0],303)
        for headers in ({'Origin':'null'}, {'Origin':'null','Sec-Fetch-Site':'same-site'}, {'Origin':'null','Sec-Fetch-Site':'cross-site'}, {'Origin':'https://evil.example','Sec-Fetch-Site':'same-origin'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request('/auth/login','POST',form,headers)[0],403)

    def test_portal_link_navigation_allows_login_but_not_cross_site_requests(self):
        self.setup_login()
        self.cookie=''
        navigation={'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'navigate',
                    'Sec-Fetch-Dest':'document','Sec-Fetch-User':'?1'}
        status,headers,_=self.request('/',headers=navigation)
        self.assertEqual(status,303)
        self.assertEqual(headers['Location'],'/auth/login')
        status,_,body=self.request('/auth/login',headers=navigation)
        self.assertEqual(status,200)
        self.assertIn('Entre no seu estúdio',body.decode())
        for path in ('/api/projects','/auth/setup','/app.js','/auth/status'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path,headers=navigation)[0],403)
        # Public entry works without optional mobile navigation metadata.
        for metadata in ({'Sec-Fetch-Site':'cross-site'},
                         {**navigation,'Sec-Fetch-User':''},
                         {**navigation,'Sec-Fetch-Mode':'cors'},
                         {**navigation,'Sec-Fetch-Dest':'iframe'}):
            with self.subTest(metadata=metadata):
                self.assertEqual(self.request('/',headers=metadata)[0],303)
                status,headers,body=self.request('/auth/login',headers=metadata)
                self.assertEqual(status,200)
                self.assertIn('Entre no seu estúdio',body.decode())
                self.assertEqual(headers['X-Frame-Options'],'DENY')
                self.assertEqual(self.request('/api/projects',headers=metadata)[0],403)
        # Even with a valid cookie, cross-site entry must not proxy the editor.
        status,headers,_=self.request('/auth/login','POST',{'username':'elisa','password':self.password})
        self.assertEqual(status,303)
        self.cookie=headers['Set-Cookie'].split(';')[0]
        status,headers,body=self.request('/',headers={'Sec-Fetch-Site':'cross-site'})
        self.assertEqual(status,303)
        self.assertEqual(headers['Location'],'/auth/login')
        self.assertEqual(body,b'')
        self.assertEqual(self.request('/auth/login','POST',{'username':'elisa','password':self.password},navigation)[0],403)

    def test_logout_all_revokes_sessions_but_foreign_origin_cannot_trigger_it(self):
        self.setup_login();first=self.cookie
        status,headers,_=self.request('/auth/login','POST',{'username':'elisa','password':self.password})
        self.assertEqual(status,303);second=headers['Set-Cookie'].split(';')[0]
        self.assertEqual(self.request('/auth/status')[0],200)
        self.assertEqual(self.request('/auth/logout-all','POST','',{'Origin':'https://foreign.example'})[0],403)
        self.assertEqual(self.request('/api/projects')[0],200)
        status,_,body=self.request('/auth/status');self.assertTrue(json.loads(body)['features']['logout_all'])
        self.assertEqual(self.request('/auth/logout-all','POST','')[0],303)
        for cookie in (first,second):
            self.cookie=cookie;self.assertEqual(self.request('/api/projects')[0],401)

    def test_duplicate_session_cookie_is_rejected(self):
        self.setup_login();valid=self.cookie
        for cookie in (valid+'; '+valid,valid+'; lili_session=bad','lili_session=bad'):
            self.cookie=cookie;self.assertEqual(self.request('/api/projects')[0],401)
        self.cookie=valid;self.assertEqual(self.request('/api/projects')[0],200)

    def test_slow_login_body_does_not_block_authenticated_requests(self):
        self.setup_login();entered=threading.Event();finished=threading.Event()
        original=RemoteHandler.read_form
        def observe(handler):
            entered.set()
            try:return original(handler)
            finally:finished.set()
        slow=http.client.HTTPConnection('127.0.0.1',self.remote.server_port,timeout=3)
        with patch.object(RemoteHandler,'read_form',observe):
            try:
                slow.putrequest('POST','/auth/login');slow.putheader('Origin',self.origin)
                slow.putheader('Content-Type','application/x-www-form-urlencoded');slow.putheader('Content-Length','1000');slow.endheaders()
                self.assertTrue(entered.wait(3))
                quick=http.client.HTTPConnection('127.0.0.1',self.remote.server_port,timeout=1)
                try:
                    quick.request('GET','/auth/status',headers={'Cookie':self.cookie})
                    response=quick.getresponse();self.assertEqual(response.status,200);response.read()
                finally:quick.close()
                body=urlencode({'username':'elisa','password':'wrong','padding':'x'*900}).encode()
                slow.send(body+b' '*(1000-len(body)))
                response=slow.getresponse();self.assertEqual(response.status,401);response.read()
            finally:slow.close();finished.wait(3)


if __name__=='__main__':unittest.main()
