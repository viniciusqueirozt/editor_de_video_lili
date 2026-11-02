import copy,tempfile,unittest
from pathlib import Path
from urllib.parse import unquote
from lili.core import Store,uid
from lili.delivery import safe_stem,export_name,content_disposition,job_delivery

class DeliveryTests(unittest.TestCase):
    def test_names_include_snapshot_revision_quality_dimensions_and_id(self):
        name=export_name('Ensaio Ágata',12,'full',1080,1920,'a'*32)
        self.assertEqual(name,'Ensaio-Ágata-v12-final-1080x1920-aaaaaaaaaaaa.mp4')
        self.assertNotEqual(name,export_name('Ensaio Ágata',12,'preview',540,960,'b'*32))
    def test_untrusted_names_cannot_be_paths_control_headers_or_reserved_devices(self):
        for raw in ('../../CON','..\\..\\secret','\r\nX-Injected: evil','a";bad=1','\u202efdp.exe','猫'*300,'CON','NUL','...'):
            with self.subTest(raw=raw[:20]):
                name=export_name(raw,1,'full',1080,1920,'a'*32)
                self.assertLess(len(name.encode('utf-8')),255)
                self.assertFalse(any(c in name for c in '/\\<>:"|?*\r\n'))
                header=content_disposition(name);header.encode('ascii');self.assertNotIn('\r',header);self.assertNotIn('\n',header)
        self.assertEqual(safe_stem('CON'),'lili-CON')
    def test_header_contains_ascii_fallback_and_utf8_name(self):
        name='Ensaio-Ágata-v3-final.mp4';header=content_disposition(name)
        self.assertIn('filename="Ensaio-Agata-v3-final.mp4"',header)
        self.assertEqual(unquote(header.split("filename*=UTF-8''",1)[1]),name)
    def test_artifact_views_detect_missing_empty_changed_and_legacy_without_mutation(self):
        with tempfile.TemporaryDirectory(dir='work/tests') as root:
            store=Store(root);p=store.create('Synthetic');jid=uid();folder=store.folder(p['id'])/'exports'/jid;folder.mkdir(parents=True);file=folder/'video.mp4'
            job={'id':jid,'project_id':p['id'],'kind':'export','status':'done','result':{'revision':2,'quality':'preview','width':540,'height':960,'bytes':4}};baseline=copy.deepcopy(job)
            self.assertEqual(job_delivery(job,store)['result']['artifact_state'],'missing')
            file.write_bytes(b'');self.assertEqual(job_delivery(job,store)['result']['artifact_state'],'empty')
            file.write_bytes(b'123');self.assertEqual(job_delivery(job,store)['result']['artifact_state'],'changed')
            file.write_bytes(b'1234');view=job_delivery(job,store);self.assertTrue(view['result']['download_available']);self.assertTrue(view['result']['download_name'].startswith('lili-v2-previa-'))
            self.assertEqual(job,baseline)
            job['result'].pop('bytes');self.assertTrue(job_delivery(job,store)['result']['download_available'])
            job['kind']='import';self.assertNotIn('download_available',job_delivery(job,store)['result'])
            job['kind']='export';job.pop('result');view=job_delivery(job,store);self.assertTrue(view['result']['download_available']);self.assertTrue(view['result']['download_name'].startswith('lili-exportacao-'));self.assertNotIn('result',job)
