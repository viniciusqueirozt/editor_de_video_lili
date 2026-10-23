import http.client
import json
import tempfile
import threading
import unittest
from email.message import Message
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from lili.access import Principal
from lili.core import Store
from lili.identity import IdentitySigner,IdentityVerifier
from lili.server import EditorServer

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.time=1700000000
        self.signer=IdentitySigner(b'test-only-key-not-a-real-secret!!','test-server-instance',lambda:self.time)
        self.verifier=IdentityVerifier(b'test-only-key-not-a-real-secret!!','test-server-instance',lambda:self.time)
        self.user=Principal('a'*48)

    def request(self,headers,method='GET',target='/api/projects'):
        message=Message()
        for key,value in headers.items():message[key]=value
        return SimpleNamespace(headers=message,command=method,path=target)

    def test_signature_binds_subject_method_path_body_metadata_and_instance(self):
        headers=self.signer.headers(self.user,'POST','/api/projects?x=1',length=2,content_type='application/json')
        headers.update({'Content-Length':'2','Content-Type':'application/json'})
        for change in ({'X-Lili-Identity':'b'*48},{'X-Lili-Identity-Signature':'0'*64},{'Content-Length':'3'},{'Content-Type':'text/plain'}):
            self.assertIsNone(self.verifier(self.request({**headers,**change},'POST','/api/projects?x=1')))
        self.assertIsNone(self.verifier(self.request(headers,'PUT','/api/projects?x=1')))
        self.assertIsNone(self.verifier(self.request(headers,'POST','/api/projects?x=2')))
        wrong_instance=IdentityVerifier(b'test-only-key-not-a-real-secret!!','other-server-instance',lambda:self.time)
        self.assertIsNone(wrong_instance(self.request(headers,'POST','/api/projects?x=1')))
        self.assertEqual(self.verifier(self.request(headers,'POST','/api/projects?x=1')),self.user)

    def test_replay_duplicates_expiration_future_and_capacity_fail_closed(self):
        headers=self.signer.headers(self.user,'GET','/api/projects')
        req=self.request(headers);req.headers['X-Lili-Identity']=self.user.subject
        self.assertIsNone(self.verifier(req))
        self.assertEqual(self.verifier(self.request(headers)),self.user)
        self.assertIsNone(self.verifier(self.request(headers)))
        self.time+=31
        self.assertIsNone(self.verifier(self.request(headers)))
        future=IdentitySigner(b'test-only-key-not-a-real-secret!!','test-server-instance',lambda:self.time+6)
        self.assertIsNone(self.verifier(self.request(future.headers(self.user,'GET','/api/projects'))))
        bounded=IdentityVerifier(b'test-only-key-not-a-real-secret!!','test-server-instance',lambda:self.time,capacity=1)
        self.assertEqual(bounded(self.request(self.signer.headers(self.user,'GET','/api/projects'))),self.user)
        self.assertIsNone(bounded(self.request(self.signer.headers(self.user,'GET','/api/projects'))))
        self.time+=31
        self.assertEqual(bounded(self.request(self.signer.headers(self.user,'GET','/api/projects'))),self.user)

    def test_concurrent_replay_has_exactly_one_winner(self):
        headers=self.signer.headers(self.user,'GET','/api/projects')
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:self.verifier(self.request(headers)),range(8)))
        self.assertEqual(results.count(self.user),1)
        self.assertEqual(results.count(None),7)

    def test_unsigned_headers_invalid_configuration_and_ambiguous_size_are_rejected(self):
        self.assertIsNone(self.verifier(self.request({'X-Lili-Identity':self.user.subject})))
        for key,audience in ((b'short','test-server-instance'),('plain-string-key-not-valid-here','test-server-instance'),(b'x'*32,'')):
            with self.assertRaises(ValueError):IdentityVerifier(key,audience)
        headers=self.signer.headers(self.user,'GET','/api/projects')
        req=self.request(headers);req.headers['Content-Length']='0';req.headers['Content-Length']='0'
        self.assertIsNone(self.verifier(req))
        with self.assertRaises(ValueError):self.signer.headers(self.user,'GET','//foreign')

    def test_signed_identity_resolver_integrates_with_real_http_permissions(self):
        scratch=Path('work/tests');scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            store=Store(folder);p=store.create('Privado de A',owner_id=self.user.subject)
            server=EditorServer(('127.0.0.1',0),store,identity_resolver=self.verifier)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            def call(headers):
                conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                try:
                    conn.request('GET','/api/projects',headers=headers);r=conn.getresponse();return r.status,json.loads(r.read())
                finally:conn.close()
            try:
                self.assertEqual(call({'X-Lili-Identity':self.user.subject})[0],401)
                signed=self.signer.headers(self.user,'GET','/api/projects')
                status,rows=call(signed);self.assertEqual(status,200);self.assertEqual(rows[0]['id'],p['id'])
                self.assertEqual(call(signed)[0],401)
                status,rows=call(self.signer.headers(Principal('b'*48),'GET','/api/projects'))
                self.assertEqual((status,rows),(200,[]))
            finally:
                server.shutdown();server.server_close();server.media.pool.shutdown(wait=True);thread.join(timeout=3)
