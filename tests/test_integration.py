import copy
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from lili.client import Client
from lili.core import EditorError, Store, uid
from lili.media import executable, probe, run
from lili.server import EditorServer


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch = Path("work/tests").resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=scratch)
        cls.root = Path(cls.temp.name)
        cls.store = Store(cls.root / "data")
        cls.server = EditorServer(("127.0.0.1", 0), cls.store)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.client = Client(cls.base)
        cls.source = cls.root / "sem-audio.mp4"
        run(["-f", "lavfi", "-i", "color=c=green:s=160x90:r=24:d=1.6", "-c:v", "libx264", "-pix_fmt", "yuv420p", cls.source])
        cls.audio = cls.root / "voz.wav"
        run(["-f", "lavfi", "-i", "sine=frequency=440:duration=2.5", "-ar", "16000", cls.audio])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server.media.pool.shutdown(wait=True)
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def wait_job(self, job_id):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            job = self.client.call("GET", "/api/jobs/" + job_id)
            if job["status"] in ("done", "error"):
                self.assertEqual(job["status"], "done", job.get("error"))
                return job
            time.sleep(.08)
        self.fail("Tempo excedido no processamento")

    def test_concat_http_missing_engine_is_read_only(self):
        with patch('lili.concat_bridge.find_concat',return_value=None), patch('lili.concat_bridge.subprocess.Popen') as spawn:
            status=self.client.call('GET','/api/concat/status')
            self.assertFalse(status['installed']);self.assertFalse(status['editing_ready'])
            result=self.client.call('POST','/api/concat/inspect',{'name':'edit_apply','arguments':{'command':'ignored'}})
            self.assertEqual(result,status);spawn.assert_not_called()
            self.assertTrue(self.client.call('GET','/api/health')['features']['source_audio_clips'])

    def test_scene_audio_fades_after_speed_and_peak_limiter(self):
        import array, math
        source=self.root/'loud-scene.mp4'
        run(['-f','lavfi','-i','color=c=blue:s=160x90:r=30:d=2.4','-f','lavfi','-i','sine=frequency=440:duration=2.4','-af','volume=7','-c:v','libx264','-c:a','aac','-shortest',source])
        p=self.client.call('POST','/api/projects',{'name':'Fades do som da cena'})
        upload=self.client.upload(p['id'],source);self.wait_job(upload['job']['id'])
        p=self.client.call('GET','/api/projects/'+p['id'])
        p=self.client.call('POST',f"/api/projects/{p['id']}/commands",{'operation':'clip_add','args':{'media_id':upload['media_id'],'start':0,'end':2.4,'speed':2,'volume':2,'audio_fade_in':.3,'audio_fade_out':.3},'expected_revision':p['revision']})
        job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
        output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
        data=subprocess.run([executable(),'-v','error','-i',str(output),'-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True)
        samples=array.array('f',data.stdout)
        def rms(a,b):
            section=samples[int(a*16000):int(b*16000)]
            return math.sqrt(sum(v*v for v in section)/len(section))
        self.assertGreater(rms(.5,.7),.4)
        self.assertLess(rms(.02,.06),rms(.5,.7)*.4)
        self.assertLess(rms(1.14,1.18),rms(.5,.7)*.5)
        self.assertLess(max(map(abs,samples)),1.05)
        self.assertAlmostEqual(probe(output)['duration'],1.2,delta=.1)

    def test_still_photo_upload_preview_and_export_preserve_original(self):
        from PIL import Image
        source=self.root/'foto.jpg'
        exif=Image.Exif();exif[274]=6
        Image.new('RGB',(120,80),'red').save(source,exif=exif)
        original=source.read_bytes()
        p=self.client.call('POST','/api/projects',{'name':'Foto sintética'})
        upload=self.client.upload(p['id'],source);self.wait_job(upload['job']['id'])
        p=self.client.call('GET','/api/projects/'+p['id'])
        asset=p['media'][0]
        self.assertTrue(asset['is_still']);self.assertFalse(asset['has_audio'])
        self.assertEqual((asset['width'],asset['height']),(80,120))
        self.assertEqual(self.client.call('GET',f"/api/projects/{p['id']}/media/{asset['id']}/original",binary=True),original)
        self.assertTrue(self.client.call('GET',f"/api/projects/{p['id']}/media/{asset['id']}/frame.jpg?at=20",binary=True).startswith(b'\xff\xd8'))
        self.assertTrue(self.client.call('GET',f"/api/projects/{p['id']}/media/{asset['id']}/sheet.jpg",binary=True).startswith(b'\xff\xd8'))
        p=self.client.call('POST',f"/api/projects/{p['id']}/commands",{'operation':'clip_add','args':{'media_id':asset['id'],'start':10,'end':10.6},'expected_revision':p['revision']})
        job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
        output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
        self.assertAlmostEqual(probe(output)['duration'],.6,delta=.1)
        decoded=subprocess.run([executable(),'-v','error','-ss','0.2','-i',str(output),'-frames:v','1','-vf','scale=1:1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True).stdout
        self.assertGreater(decoded[0],150);self.assertLess(decoded[1],40)
        self.assertEqual(source.read_bytes(),original)

    def test_music_trim_offset_duck_and_mix_in_export(self):
        import array
        import math
        p = self.client.call("POST", "/api/projects", {"name": "Música sintética"})
        music_file, voice_file = self.root / "music880.wav", self.root / "voice440.wav"
        run(["-f", "lavfi", "-i", "sine=frequency=880:duration=4", music_file])
        run(["-f", "lavfi", "-i", "sine=frequency=440:duration=1", voice_file])
        assets = []
        for path in (self.source, music_file, voice_file):
            upload = self.client.upload(p["id"], path)
            self.wait_job(upload["job"]["id"])
            assets.append(upload["media_id"])
        p = self.client.call("GET", "/api/projects/" + p["id"])
        for operation, args in [
            ("timeline_replace", {"clips": [{"media_id": assets[0], "start": 0, "end": 1.6, "volume": 0}] * 2}),
            ("narration_set", {"media_id": assets[2], "offset": 1}),
            ("music_set", {"media_id": assets[1], "start": .5, "end": 3, "offset": .2, "volume": .8, "fade_in": .2, "fade_out": .3}),
        ]:
            p = self.client.call("POST", f"/api/projects/{p['id']}/commands", {"operation": operation, "args": args, "expected_revision": p["revision"]})
        job = self.client.call("POST", f"/api/projects/{p['id']}/exports", {"expected_revision": p["revision"], "quality": "preview"})
        self.wait_job(job["id"])
        output = self.store.folder(p["id"]) / "exports" / job["id"] / "video.mp4"
        data = subprocess.run([executable(), "-v", "error", "-i", str(output), "-f", "f32le", "-ac", "1", "-ar", "16000", "pipe:1"], capture_output=True, check=True)
        samples = array.array("f", data.stdout)
        def amplitude(start, end):
            values = samples[int(start*16000):int(end*16000)]
            return 2*abs(sum(value*complex(math.cos(2*math.pi*880*i/16000), math.sin(2*math.pi*880*i/16000)) for i,value in enumerate(values)))/len(values)
        normal = amplitude(.6, .8)
        self.assertGreater(normal, .04)
        self.assertLess(amplitude(.05, .15), normal*.02)
        self.assertAlmostEqual(amplitude(1.4, 1.6)/normal, .25, delta=.06)
        self.assertAlmostEqual(amplitude(2.1, 2.3)/normal, 1, delta=.1)
        self.assertLess(amplitude(2.9, 3.1), normal*.02)
        self.assertAlmostEqual(probe(output)["duration"], 3.2, delta=.1)

    def test_narration_source_trim_fades_duck_and_legacy_export(self):
        import array, math
        voice_file,music_file=self.root/'voice-markers.wav',self.root/'trim-music.wav'
        run(['-f','lavfi','-i','sine=frequency=220:duration=1','-f','lavfi','-i','sine=frequency=440:duration=2','-f','lavfi','-i','sine=frequency=880:duration=1','-filter_complex','[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]','-map','[a]',voice_file])
        run(['-f','lavfi','-i','sine=frequency=1000:duration=4',music_file])
        original=voice_file.read_bytes();p=self.client.call('POST','/api/projects',{'name':'Narration trim synthetic'})
        ids=[]
        for path in (self.source,voice_file,music_file):
            up=self.client.upload(p['id'],path);self.wait_job(up['job']['id']);ids.append(up['media_id'])
        p=self.store.get(p['id'])
        for op,args in [('timeline_replace',{'clips':[{'media_id':ids[0],'start':0,'end':1.6,'volume':0}]*2}),('narration_set',{'media_id':ids[1],'start':1,'end':3,'offset':.5,'volume':.5,'fade_in':.2,'fade_out':.2}),('music_set',{'media_id':ids[2],'volume':.8})]:
            p=self.store.apply(p['id'],op,args,p['revision'])
        baseline=p['timeline']
        def render_samples():
            job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
            output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
            raw=subprocess.run([executable(),'-v','error','-i',str(output),'-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
            return array.array('f',raw),probe(output)['duration']
        def tone(samples,freq,a,b):
            values=samples[int(a*16000):int(b*16000)]
            return 2*abs(sum(v*complex(math.cos(2*math.pi*freq*i/16000),math.sin(2*math.pi*freq*i/16000)) for i,v in enumerate(values)))/len(values)
        samples,length=render_samples();voice=tone(samples,440,1.2,1.4)
        self.assertGreater(voice,.03);self.assertLess(tone(samples,220,1.2,1.4),voice*.08);self.assertLess(tone(samples,880,1.2,1.4),voice*.08)
        self.assertLess(tone(samples,440,.52,.56),voice*.5);self.assertLess(tone(samples,440,2.44,2.48),voice*.5)
        self.assertLess(tone(samples,440,.2,.4),voice*.03)
        self.assertLess(tone(samples,440,2.8,3),voice*.03)
        music=tone(samples,1000,.2,.4);self.assertGreater(music,.04)
        self.assertAlmostEqual(tone(samples,1000,1.2,1.4)/music,.25,delta=.06)
        self.assertAlmostEqual(tone(samples,1000,2.8,3)/music,1,delta=.1)
        self.assertAlmostEqual(length,3.2,delta=.1);self.assertEqual(self.store.get(p['id'])['timeline'],baseline)
        # A project from before source intervals has no start/end keys at all.
        legacy=self.store._read(p['id']);legacy['narration'].pop('start');legacy['narration'].pop('end');self.store._write(legacy)
        samples,length=render_samples();self.assertGreater(tone(samples,220,.8,1),.02)
        self.assertAlmostEqual(tone(samples,1000,2.8,3)/music,.25,delta=.06)
        self.assertEqual(voice_file.read_bytes(),original);self.assertAlmostEqual(length,3.2,delta=.1)

    def test_narration_fades_in_export_with_offset(self):
        import array
        import math
        p = self.client.call("POST", "/api/projects", {"name": "Fades sintéticos"})
        video = self.client.upload(p["id"], self.source)
        self.wait_job(video["job"]["id"])
        audio = self.client.upload(p["id"], self.audio)
        self.wait_job(audio["job"]["id"])
        p = self.client.call("GET", "/api/projects/" + p["id"])
        for operation, args in [
            ("timeline_replace", {"clips": [{"media_id": video["media_id"], "start": 0, "end": 1.6, "volume": 0}] * 2}),
            ("narration_set", {"media_id": audio["media_id"], "offset": .3, "fade_in": .6, "fade_out": .6}),
        ]:
            p = self.client.call("POST", f"/api/projects/{p['id']}/commands", {"operation": operation, "args": args, "expected_revision": p["revision"]})
        job = self.client.call("POST", f"/api/projects/{p['id']}/exports", {"expected_revision": p["revision"], "quality": "preview"})
        self.wait_job(job["id"])
        output = self.store.folder(p["id"]) / "exports" / job["id"] / "video.mp4"
        decoded = subprocess.run([executable(), "-v", "error", "-i", str(output), "-f", "f32le", "-ac", "1", "-ar", "16000", "pipe:1"], capture_output=True, check=True)
        samples = array.array("f", decoded.stdout)
        def rms(start, end):
            values = samples[int(start*16000):int(end*16000)]
            return math.sqrt(sum(v*v for v in values)/len(values))
        middle = rms(1.2, 1.4)
        self.assertGreater(middle, .04)
        self.assertLess(rms(.05, .15), middle*.01)
        self.assertLess(rms(.35, .45), middle*.3)
        self.assertLess(rms(2.6, 2.7), middle*.4)
        self.assertLess(rms(2.95, 3.05), middle*.01)

    def test_full_upload_edit_export_narration_and_mcp(self):
        p = self.client.call("POST", "/api/projects", {"name": "Integração", "script": "Cora no parque"})
        job = self.client.upload(p["id"], self.source)
        self.wait_job(job["job"]["id"])
        voice = self.client.upload(p["id"], self.audio)
        self.wait_job(voice["job"]["id"])
        p = self.client.call("GET", "/api/projects/" + p["id"])
        asset = next(a for a in p["media"] if a["kind"] == "video")
        self.assertFalse(asset["has_audio"])
        self.assertTrue(self.client.call("GET", f"/api/projects/{p['id']}/media/{asset['id']}/sheet.jpg", binary=True).startswith(b"\xff\xd8"))

        def edit(operation, args):
            nonlocal p
            p = self.client.call("POST", f"/api/projects/{p['id']}/commands", {"operation": operation, "args": args, "expected_revision": p["revision"], "actor": "codex"})

        edit("timeline_replace", {"clips": [{"media_id": asset["id"], "start": .1, "end": 1.2, "volume": 0, "title": "Cora: um dia\nd'água %"}, {"media_id": asset["id"], "start": .3, "end": 1.4, "volume": .3}]})
        edit("narration_set", {"media_id": voice["media_id"], "volume": .5, "offset": .1})
        wave = self.client.call("GET", f"/api/projects/{p['id']}/media/{voice['media_id']}/waveform.json")
        self.assertAlmostEqual(wave["duration"], 2.5, delta=.05)
        self.assertGreater(len(wave["peaks"]), 100)
        self.assertGreater(max(wave["peaks"]), .05)
        self.assertLessEqual(max(wave["peaks"]), 1)
        edit("clip_split", {"clip_id": p["timeline"][0]["id"], "at": .6})
        self.assertEqual(len(p["timeline"]), 3)
        edit("undo", {})
        job = self.client.call("POST", f"/api/projects/{p['id']}/exports", {"expected_revision": p["revision"], "quality": "preview"})
        revision = p["revision"]
        edit("clip_update", {"clip_id": p["timeline"][0]["id"], "title": "Mudança posterior"})
        result = self.wait_job(job["id"])["result"]
        self.assertEqual(result["revision"], revision)
        self.assertAlmostEqual(result["duration"], 2.2, delta=.15)
        video_path = self.store.folder(p["id"]) / "exports" / job["id"] / "video.mp4"
        details = probe(video_path)
        self.assertEqual((details["width"], details["height"]), (540, 960))
        self.assertTrue(details["has_audio"])
        frame = self.client.call("GET", f"/api/projects/{p['id']}/media/{asset['id']}/frame.jpg?at=0.5", binary=True)
        self.assertTrue(frame.startswith(b"\xff\xd8"))
        with urlopen(Request(self.base + result["url"], headers={"Range": "bytes=0-31"})) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(len(response.read()), 32)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + result["url"], headers={"Range": "bytes=999999999-"}))
        self.assertEqual(error.exception.code, 416)
        # Trash hides every media endpoint without deleting the source on disk.
        source_path = self.store.folder(p["id"]) / "media" / asset["filename"]
        edit("media_remove", {"media_id": asset["id"], "remove_usage": True})
        self.assertTrue(source_path.exists())
        with self.assertRaises(HTTPError) as missing:
            urlopen(self.base + f"/api/projects/{p['id']}/media/{asset['id']}/thumbnail")
        self.assertEqual(missing.exception.code, 404)
        edit("undo", {})
        self.assertTrue(self.client.call("GET", f"/api/projects/{p['id']}/media/{asset['id']}/thumbnail", binary=True))
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "lili_project_context", "arguments": {"project_id": p["id"]}}},
        ]
        process = subprocess.run([sys.executable, "-m", "lili.mcp", "--url", self.base], input="\n".join(json.dumps(m) for m in messages) + "\n", capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(responses), 3)
        self.assertEqual(len(responses[1]["result"]["tools"]), 7)
        context = json.loads(responses[2]["result"]["content"][0]["text"])
        self.assertEqual(context["project"]["timeline"][0]["title"], "Mudança posterior")

    def test_rotation_metadata_is_respected(self):
        rotated = self.root / "rotated.mp4"
        run(["-display_rotation", "90", "-i", self.source, "-c", "copy", rotated])
        details = probe(rotated)
        self.assertEqual((details["width"], details["height"]), (90, 160))

    def test_chunk_upload_retry_imports_identical_video(self):
        p = self.client.call("POST", "/api/projects", {"name": "Envio em blocos"})
        raw = self.source.read_bytes()
        upload = self.client.call("POST", f"/api/projects/{p['id']}/uploads", {"name": "original.mp4", "size": len(raw)})
        split = len(raw)//2
        for offset, data in ((0, raw[:split]), (0, raw[:split]), (split, raw[split:])):
            req = Request(self.base+f"/api/projects/{p['id']}/uploads/{upload['upload_id']}?offset={offset}", data=data, method="PUT")
            with urlopen(req) as response:
                self.assertEqual(json.loads(response.read())["received"], offset+len(data))
        # Conflicting retransmissions and fractional byte positions fail over
        # HTTP too, before import; the successfully received source stays intact.
        for offset, data, status in ((str(split), b"x" * (len(raw)-split), 409), ("0.00001", b"x", 400)):
            req = Request(self.base+f"/api/projects/{p['id']}/uploads/{upload['upload_id']}?offset={offset}", data=data, method="PUT")
            with self.subTest(offset=offset), self.assertRaises(HTTPError) as error:
                urlopen(req)
            self.assertEqual(error.exception.code, status)
        job = self.client.call("POST", f"/api/projects/{p['id']}/uploads/{upload['upload_id']}/complete", {})
        self.wait_job(job["job"]["id"])
        asset = self.store.media(p['id'], job['media_id'])
        self.assertEqual(self.server.media.source(p['id'], asset).read_bytes(), raw)
        self.assertEqual(asset['status'], 'ready')

    def test_direct_upload_low_disk_rejects_before_creating_media(self):
        p = self.client.call("POST", "/api/projects", {"name": "Disco insuficiente"})
        with patch("lili.uploads.shutil.disk_usage", return_value=SimpleNamespace(free=0)):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(self.base+f"/api/projects/{p['id']}/upload?name=test.mp4", data=b"video", method="PUT"))
        self.assertEqual(error.exception.code,507)
        self.assertIn("Espaço insuficiente",error.exception.read().decode())
        self.assertEqual(self.store.get(p['id'])['media'],[])
        self.assertEqual(list((self.store.folder(p['id'])/'media').iterdir()),[])

    def test_direct_upload_disk_check_failure_cleans_partial_file(self):
        p = self.client.call("POST", "/api/projects", {"name": "Disco ocupado durante envio"})
        # Initial check and first 1 MiB succeed; the next block is rejected.
        with patch.object(self.server.uploads,"require_space",side_effect=[None,None,EditorError("Espaço insuficiente.",507)]) as check:
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(self.base+f"/api/projects/{p['id']}/upload?name=test.mp4", data=b"x"*(1024*1024+1), method="PUT"))
        self.assertEqual(error.exception.code,507)
        self.assertEqual(check.call_count,3)
        self.assertEqual(self.store.get(p['id'])['media'],[])
        self.assertEqual(list((self.store.folder(p['id'])/'media').iterdir()),[])

    def test_home_editor_routes_and_project_trash_restore_api(self):
        for path,marker in (("/",b"project-grid"),("/editor",b"media-list"),("/home.js",b"loadProjects"),("/home.css",b".project-grid")):
            with urlopen(self.base+path) as response:
                self.assertEqual(response.status,200)
                self.assertIn(marker,response.read())
        p=self.client.call("POST","/api/projects",{"name":"Lixeira HTTP"})
        hidden=self.client.call("POST",f"/api/projects/{p['id']}/trash",{"expected_revision":p['revision']})
        self.assertNotIn(p['id'],[x['id'] for x in self.client.call("GET","/api/projects")])
        self.assertIn(p['id'],[x['id'] for x in self.client.call("GET","/api/projects?trash=1")])
        for suffix in ("","/jobs","/context"):
            with self.assertRaises(HTTPError) as error:urlopen(self.base+f"/api/projects/{p['id']}"+suffix)
            self.assertEqual(error.exception.code,404)
        self.client.call("POST",f"/api/projects/{p['id']}/restore",{"expected_revision":hidden['revision']})
        self.assertEqual(self.client.call("GET",f"/api/projects/{p['id']}")['name'],p['name'])

    def test_project_with_pending_upload_cannot_be_hidden(self):
        p=self.client.call("POST","/api/projects",{"name":"Envio em andamento"})
        self.client.call("POST",f"/api/projects/{p['id']}/uploads",{"name":"test.mp4","size":10})
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base+f"/api/projects/{p['id']}/trash",method="POST",data=json.dumps({"expected_revision":p['revision']}).encode(),headers={"Content-Type":"application/json"}))
        self.assertEqual(error.exception.code,409)
        self.assertEqual(self.client.call("GET",f"/api/projects/{p['id']}")['revision'],p['revision'])

    def test_permanent_project_deletion_api_blocks_jobs_and_stale_submissions(self):
        p=self.client.call('POST','/api/projects',{'name':'Purge HTTP sintético'})
        hidden=self.client.call('POST',f"/api/projects/{p['id']}/trash",{'expected_revision':p['revision']})
        job_id=uid()
        with self.server.media.lock:self.server.media.jobs[job_id]={'id':job_id,'project_id':p['id'],'status':'running','kind':'export'}
        def purge(data):
            return urlopen(Request(self.base+f"/api/projects/{p['id']}/purge",method='POST',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'}))
        args={'expected_revision':hidden['revision'],'confirmation':'EXCLUIR'}
        with self.assertRaises(HTTPError) as error:purge(args)
        self.assertEqual(error.exception.code,409)
        with self.server.media.lock:self.server.media.jobs[job_id]['status']='done'
        with self.assertRaises(HTTPError) as error:purge({'expected_revision':hidden['revision']})
        self.assertEqual(error.exception.code,400)
        result=self.client.call('POST',f"/api/projects/{p['id']}/purge",args)
        self.assertTrue(result['permanent']);self.assertFalse(self.store.folder(p['id']).exists())
        with self.assertRaises(EditorError):self.server.media.submit(p['id'],'export',lambda _:None)
        self.assertEqual(len([j for j in self.server.media.jobs.values() if j['project_id']==p['id']]),1)

    def test_external_origin_and_host_are_rejected(self):
        for headers in ({"Origin": "https://external.example"}, {"Host": "external.example"}):
            with self.subTest(headers=headers), self.assertRaises(HTTPError) as error:
                urlopen(Request(self.base + "/api/health", headers=headers))
            self.assertEqual(error.exception.code, 403)

    def test_paths_and_malformed_json(self):
        for path in ("/../README.md", "/%2e%2e/README.md", "/api/projects/not-a-project"):
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.base + path)
            self.assertEqual(error.exception.code, 404)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/projects", data=b"[]", headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 400)

    def test_imported_sound_effect_blocks_mix_without_replacing_voice_or_music(self):
        import array, math
        effect=self.root/'synthetic-chime.wav'
        run(['-f','lavfi','-i','sine=frequency=880:duration=1','-ar','16000',effect])
        original_bytes=effect.read_bytes()
        self.assertTrue(self.client.call('GET','/api/health')['features']['library_sounds'])
        p=self.client.call('POST','/api/projects',{'name':'Imported sound blocks'})
        uploaded=[]
        for source in (self.source,self.audio,effect):
            upload=self.client.upload(p['id'],source);self.wait_job(upload['job']['id']);uploaded.append(upload['media_id'])
        p=self.client.call('GET','/api/projects/'+p['id'])
        def command(operation,args):
            nonlocal p
            p=self.client.call('POST',f"/api/projects/{p['id']}/commands",{'operation':operation,'args':args,'expected_revision':p['revision']})
        for _ in range(2):command('clip_add',{'media_id':uploaded[0],'start':0,'end':1.6})
        command('narration_set',{'media_id':uploaded[1],'volume':.2})
        command('music_set',{'media_id':uploaded[1],'volume':.2,'duck':False})
        visual=copy.deepcopy(p['timeline']);voice=copy.deepcopy(p['narration']);music=copy.deepcopy(p['music'])
        command('audio_clip_add',{'media_id':uploaded[2],'start':.1,'end':.9,'offset':1,'volume':.5,'fade_in':.1,'fade_out':.1})
        sound=p['audio_clips'][0];self.assertIsNone(sound['source_clip_id'])
        command('audio_clip_duplicate',{'audio_id':sound['id']})
        self.assertEqual(p['timeline'],visual);self.assertEqual(p['narration'],voice);self.assertEqual(p['music'],music)
        command('undo',{});self.assertEqual(len(p['audio_clips']),1)
        command('redo',{});self.assertEqual(len(p['audio_clips']),2)
        job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
        output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
        raw=subprocess.run([executable(),'-v','error','-i',str(output),'-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
        samples=array.array('f',raw)
        def rms(a,b):
            values=samples[int(a*16000):int(b*16000)];return math.sqrt(sum(x*x for x in values)/len(values))
        baseline=rms(.3,.7)
        self.assertGreater(rms(1.2,1.5),baseline*1.4);self.assertGreater(rms(2,2.3),baseline*1.4)
        self.assertLess(rms(2.8,3),.002);self.assertAlmostEqual(probe(output)['duration'],3.2,delta=.12)
        self.assertEqual(effect.read_bytes(),original_bytes)

    def test_source_audio_separation_independent_timing_and_no_double_sound(self):
        import array,math
        source=self.root/'source-with-independent-sound.mp4'
        run(['-f','lavfi','-i','color=c=red:s=160x90:r=30:d=4','-f','lavfi','-i','sine=frequency=440:duration=4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',source])
        original=source.read_bytes();p=self.client.call('POST','/api/projects',{'name':'Independent source audio'})
        up=self.client.upload(p['id'],source);self.wait_job(up['job']['id'])
        filler=self.client.upload(p['id'],self.source);self.wait_job(filler['job']['id']);p=self.store.get(p['id'])
        p=self.store.apply(p['id'],'clip_add',{'media_id':up['media_id'],'start':0,'end':2,'speed':2,'volume':.7,'separate_audio':True},p['revision'])
        sound=p['audio_clips'][0];self.assertEqual(sound['speed'],2);self.assertTrue(p['timeline'][0]['audio_detached'])
        for _ in range(2):p=self.store.apply(p['id'],'clip_add',{'media_id':filler['media_id'],'start':0,'end':1.6},p['revision'])
        p=self.store.apply(p['id'],'audio_clip_update',{'audio_id':sound['id'],'start':1,'end':3,'speed':1,'offset':.5,'volume':.5,'fade_in':.2,'fade_out':.2},p['revision'])
        separate=copy.deepcopy(p['audio_clips']);p=self.store.apply(p['id'],'clip_update',{'clip_id':p['timeline'][0]['id'],'start':.5,'end':1.5,'speed':1},p['revision']);self.assertEqual(p['audio_clips'],separate)
        def render():
            job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
            output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
            samples=array.array('f',subprocess.run([executable(),'-v','error','-i',str(output),'-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout)
            return samples,probe(output)['duration']
        def tone(samples,a,b):
            values=samples[int(a*16000):int(b*16000)];return 2*abs(sum(v*complex(math.cos(2*math.pi*440*i/16000),math.sin(2*math.pi*440*i/16000)) for i,v in enumerate(values)))/len(values)
        samples,length=render();self.assertAlmostEqual(length,4.2,delta=.1)
        self.assertLess(tone(samples,.1,.3),.002,'Embedded original audio must stay muted')
        level=tone(samples,1.1,1.3);self.assertGreater(level,.05);self.assertLess(level,.085,'No doubled original sound')
        self.assertLess(tone(samples,2.8,3),.002)
        p=self.store.apply(p['id'],'audio_clip_split',{'audio_id':sound['id'],'at':2},p['revision']);left,right=p['audio_clips']
        p=self.store.apply(p['id'],'audio_clip_duplicate',{'audio_id':right['id']},p['revision'])
        p=self.store.apply(p['id'],'audio_clip_remove',{'audio_id':left['id']},p['revision'])
        samples,length=render();self.assertLess(tone(samples,.8,1),.002);self.assertGreater(tone(samples,1.8,2),.05);self.assertGreater(tone(samples,2.8,3),.05)
        self.assertEqual(source.read_bytes(),original)

    def test_spatial_transitions_move_images_preserve_clock_audio_and_draft(self):
        import array, math
        p=self.client.call('POST','/api/projects',{'name':'Spatial transition samples'});ids=[];originals={}
        self.assertTrue(self.client.call('GET','/api/health')['features']['spatial_transitions'])
        for name,base,right,freq in (('outgoing','red','yellow',440),('incoming','blue','green',880)):
            path=self.root/(name+'-spatial.mp4')
            run(['-f','lavfi','-i',f'color=c={base}:s=160x90:r=30:d=1.6,drawbox=x=80:y=0:w=80:h=90:color={right}:t=fill','-f','lavfi','-i',f'sine=frequency={freq}:duration=1.6','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',path])
            originals[path]=path.read_bytes();upload=self.client.upload(p['id'],path);self.wait_job(upload['job']['id']);ids.append(upload['media_id'])
        p=self.store.get(p['id']);p=self.store.apply(p['id'],'settings_update',{'format':'landscape'},p['revision'])
        for media_id in ids:p=self.store.apply(p['id'],'clip_add',{'media_id':media_id,'start':0,'end':1.6},p['revision'])
        colors={'red':lambda r,g,b:r>180 and g<50 and b<50,'yellow':lambda r,g,b:r>180 and g>180 and b<50,'blue':lambda r,g,b:b>180 and r<50 and g<50,'green':lambda r,g,b:g>70 and r<50 and b<50}
        expected={'wipe_left':('red','green'),'wipe_right':('blue','yellow'),'slide_left':('yellow','blue'),'slide_right':('green','red')}
        for kind,(left_color,right_color) in expected.items():
            with self.subTest(kind=kind):
                p=self.store.apply(p['id'],'transition_set',{'left':p['timeline'][0]['id'],'right':p['timeline'][1]['id'],'kind':kind,'duration':.8},p['revision'])
                baseline=copy.deepcopy(p)
                job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
                output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
                raw=subprocess.run([executable(),'-v','error','-i',str(output),'-vf','scale=80:46,format=rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True).stdout
                size=80*46*3;frames=[raw[i:i+size] for i in range(0,len(raw),size)]
                def pixel(t,x):
                    start=(23*80+x)*3;return tuple(frames[round(t*30)][start:start+3])
                self.assertTrue(colors[left_color](*pixel(1.6,10)),(kind,'left',pixel(1.6,10)))
                self.assertTrue(colors[right_color](*pixel(1.6,70)),(kind,'right',pixel(1.6,70)))
                self.assertTrue(colors['red'](*pixel(.5,10)));self.assertTrue(colors['green'](*pixel(3,70)))
                self.assertGreater(len(set(frame[23*80*3:24*80*3] for frame in frames[37:59])),10,'must contain continuous spatial motion, not a dry cut')
                self.assertAlmostEqual(probe(output)['duration'],3.2,delta=.1)
                samples=array.array('f',subprocess.run([executable(),'-v','error','-i',str(output),'-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout)
                def tone(freq,a,b):
                    v=samples[int(a*16000):int(b*16000)];return 2*abs(sum(x*complex(math.cos(2*math.pi*freq*i/16000),math.sin(2*math.pi*freq*i/16000)) for i,x in enumerate(v)))/len(v)
                self.assertGreater(tone(440,1.2,1.4),.06);self.assertGreater(tone(880,1.9,2.1),.06);self.assertLess(tone(440,1.9,2.1),.01)
                preview=self.client.call('POST',f"/api/projects/{p['id']}/transition-preview",{'expected_revision':p['revision'],'left':p['timeline'][0]['id'],'right':p['timeline'][1]['id'],'kind':kind,'duration':.8})
                result=self.wait_job(preview['id'])['result'];self.assertEqual(result['preview_scope'],'transition');self.assertAlmostEqual(result['duration'],3,delta=.1)
                preview_file=self.store.folder(p['id'])/'exports'/preview['id']/'video.mp4'
                frame=subprocess.run([executable(),'-v','error','-ss','1.5','-i',str(preview_file),'-frames:v','1','-vf','scale=80:46,format=rgb24','-f','rawvideo','pipe:1'],capture_output=True,check=True).stdout
                for x,color in ((10,left_color),(70,right_color)):
                    index=(23*80+x)*3;self.assertTrue(colors[color](*frame[index:index+3]),(kind,'draft',x,tuple(frame[index:index+3])))
                self.assertEqual(self.store.get(p['id']),baseline)
        full=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'full'});result=self.wait_job(full['id'])['result']
        self.assertEqual((result['width'],result['height']),(1920,1080));self.assertAlmostEqual(result['duration'],3.2,delta=.1)
        for path,raw in originals.items():self.assertEqual(path.read_bytes(),raw)

    def test_dissolve_mix_pixels_audio_timing_and_draft_preview(self):
        import array,math
        p=self.client.call("POST","/api/projects",{"name":"Synthetic dissolve"});ids=[]
        for name,freq in (("red",440),("blue",880)):
            path=self.root/(name+"-dissolve.mp4")
            run(["-f","lavfi","-i",f"color=c={name}:s=160x90:r=30:d=1.6","-f","lavfi","-i",f"sine=frequency={freq}:duration=1.6","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-shortest",path])
            up=self.client.upload(p["id"],path);self.wait_job(up["job"]["id"]);ids.append(up["media_id"])
        up=self.client.upload(p["id"],self.source);self.wait_job(up["job"]["id"]);ids.append(up["media_id"])
        p=self.store.get(p["id"])
        for media_id in ids:p=self.store.apply(p["id"],"clip_add",{"media_id":media_id,"start":0,"end":1.6},p["revision"])
        p=self.store.apply(p["id"],"transition_set",{"all":True,"kind":"dissolve","duration":.8},p["revision"])
        baseline=copy.deepcopy(p)
        job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
        output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
        raw=subprocess.run([executable(),"-v","error","-i",str(output),"-vf","crop=20:20:(iw-20)/2:(ih-20)/2,scale=1:1,format=rgb24","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
        pixels=[tuple(raw[i:i+3]) for i in range(0,len(raw),3)]
        for at in (1.5,1.6,1.7):
            r,g,b=pixels[round(at*30)];self.assertGreater(r,50);self.assertGreater(b,50);self.assertLess(g,20)
        self.assertGreater(pixels[20][0],230);self.assertGreater(pixels[70][2],230);self.assertGreater(pixels[-6][1],90)
        self.assertAlmostEqual(probe(output)["duration"],4.8,delta=.1)
        audio=array.array('f',subprocess.run([executable(),"-v","error","-i",str(output),"-f","f32le","-ac","1","-ar","16000","pipe:1"],capture_output=True,check=True).stdout)
        def tone(freq,a,b):
            values=audio[int(a*16000):int(b*16000)];return 2*abs(sum(v*complex(math.cos(2*math.pi*freq*i/16000),math.sin(2*math.pi*freq*i/16000)) for i,v in enumerate(values)))/len(values)
        self.assertGreater(tone(440,1.2,1.4),.06);self.assertGreater(tone(880,2,2.2),.06);self.assertLess(tone(440,2,2.2),.01)
        draft=self.client.call("POST",f"/api/projects/{p['id']}/transition-preview",{"expected_revision":p["revision"],"left":p["timeline"][0]["id"],"right":p["timeline"][1]["id"],"kind":"dissolve","duration":.8})
        result=self.wait_job(draft["id"])["result"];self.assertEqual(result["preview_scope"],"transition");self.assertAlmostEqual(result["duration"],3,delta=.1)
        self.assertEqual(self.store.get(p["id"]),baseline)
        # Existing visual/audio fades keep their original time base in a draft.
        p=self.store.apply(p["id"],"clip_update",{"clip_id":p["timeline"][0]["id"],"fade_out":1.6,"audio_fade_out":1.6},p["revision"])
        faded=self.client.call("POST",f"/api/projects/{p['id']}/transition-preview",{"expected_revision":p["revision"],"left":p["timeline"][0]["id"],"right":p["timeline"][1]["id"],"kind":"dissolve","duration":.8})
        result=self.wait_job(faded["id"])["result"];self.assertAlmostEqual(result["duration"],3.2,delta=.1);self.assertAlmostEqual(result["preview_seek"],.1,delta=.01)
        self.assertEqual(self.store.get(p["id"]),p)
        p=self.store.apply(p["id"],"clip_update",{"clip_id":p["timeline"][0]["id"],"fade_out":0,"audio_fade_out":0},p["revision"])
        # A dry junction before a dissolve must also keep a constant frame rate.
        p=self.store.apply(p["id"],"transition_set",{"left":p["timeline"][0]["id"],"right":p["timeline"][1]["id"],"kind":"none"},p["revision"])
        mixed=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"full"})
        result=self.wait_job(mixed["id"])["result"];self.assertAlmostEqual(result["duration"],4.8,delta=.1)
        self.assertEqual((result["width"],result["height"]),(1080,1920))

    def test_pair_color_transitions_render_two_sides_without_changing_audio_or_duration(self):
        p=self.client.call("POST","/api/projects",{"name":"Synthetic pair passages"})
        imported=self.client.upload(p["id"],self.source);self.wait_job(imported["job"]["id"])
        audio=self.client.upload(p["id"],self.audio);self.wait_job(audio["job"]["id"])
        p=self.store.get(p["id"])
        for _ in range(2):
            p=self.store.apply(p["id"],"clip_add",{"media_id":imported["media_id"],"start":.2,"end":1.4},p["revision"])
        p=self.store.apply(p["id"],"narration_set",{"media_id":audio["media_id"],"offset":.2},p["revision"])
        original_clips=p["timeline"];narration=p["narration"]
        for kind in ("white","black"):
            p=self.store.apply(p["id"],"transition_set",{"left":p["timeline"][0]["id"],"right":p["timeline"][1]["id"],"kind":kind,"duration":.8},p["revision"])
            self.assertEqual(p["timeline"],original_clips);self.assertEqual(p["narration"],narration)
            job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
            output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
            raw=subprocess.run([executable(),"-v","error","-i",str(output),"-vf","crop=20:20:(iw-20)/2:(ih-20)/2,scale=1:1,format=gray","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
            self.assertAlmostEqual(probe(output)["duration"],2.4,delta=.15)
            self.assertGreater(raw[10],30);self.assertGreater(raw[-8],30)
            if kind=="white":self.assertGreater(raw[35],200);self.assertGreater(raw[36],235)
            else:self.assertLess(raw[35],15);self.assertLess(raw[36],10)
            audio_data=subprocess.run([executable(),"-v","error","-ss","1.05","-i",str(output),"-t","0.3","-vn","-f","s16le","-ac","1","-ar","8000","pipe:1"],capture_output=True,check=True).stdout
            import array
            samples=array.array("h",audio_data)
            self.assertGreater(max(abs(v) for v in samples),500)

    def test_visual_fades_render_black_edges_and_keep_duration(self):
        p = self.client.call("POST", "/api/projects", {"name": "Visual fades synthetic"})
        imported = self.client.upload(p["id"], self.source)
        self.wait_job(imported["job"]["id"])
        p = self.store.get(p["id"])
        p = self.client.call("POST", f"/api/projects/{p['id']}/commands", {"operation": "clip_add", "args": {"media_id": imported["media_id"], "start": .2, "end": 1.4, "fade_in": .3, "fade_out": .3}, "expected_revision": p["revision"]})
        job = self.client.call("POST", f"/api/projects/{p['id']}/exports", {"expected_revision": p["revision"], "quality": "preview"})
        self.wait_job(job["id"])
        output = self.store.folder(p["id"]) / "exports" / job["id"] / "video.mp4"
        raw = subprocess.run([executable(), "-v", "error", "-i", str(output), "-vf", "crop=20:20:(iw-20)/2:(ih-20)/2,scale=1:1,format=gray", "-f", "rawvideo", "pipe:1"], capture_output=True, check=True).stdout
        self.assertLess(raw[0], 5)
        self.assertGreater(raw[len(raw)//2], 30)
        self.assertLess(raw[-1], raw[len(raw)//2] * .3)
        self.assertAlmostEqual(probe(output)["duration"], 1.2, delta=.12)

    def test_caption_export_uses_style_font_and_lower_position(self):
        p=self.client.call("POST","/api/projects",{"name":"Caption synthetic"})
        imported=self.client.upload(p["id"],self.source);self.wait_job(imported["job"]["id"])
        p=self.store.get(p["id"])
        p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_add","args":{"media_id":imported["media_id"],"start":0,"end":.5,"title":"Legenda de teste","title_position":"bottom","title_font":"serif","title_size":"large"},"expected_revision":p["revision"]})
        job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
        output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
        data=subprocess.run([executable(),"-v","error","-i",str(output),"-frames:v","1","-vf","format=gray","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
        w,h=540,960
        bright=[(i//w) for i,v in enumerate(data) if v>200]
        self.assertGreater(len(bright),50)
        self.assertGreater(min(bright),h*.68)
        self.assertLess(max(bright),h*.84)

    def test_independent_subtitle_draft_payload_timing_style_and_undo_export(self):
        p=self.client.call("POST","/api/projects",{"name":"Subtitle draft synthetic"})
        imported=self.client.upload(p["id"],self.source);self.wait_job(imported["job"]["id"])
        def edit(op,args):
            nonlocal p
            p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":op,"args":args,"expected_revision":p["revision"]})
        p=self.client.call("GET","/api/projects/"+p['id'])
        edit("clip_add",{"media_id":imported['media_id'],"start":0,"end":1.6})
        baseline=p['timeline']
        edit("caption_add",{"start":.3,"end":.8,"text":"Legenda inferior","title_font":"serif","title_size":"large","title_position":"bottom"})
        first=p['captions'][0]
        edit("caption_update",{"caption_id":first['id'],"start":.35,"end":.85,"text":"Texto revisado","title_font":"serif","title_size":"large","title_position":"bottom"})
        edit("undo",{});self.assertEqual(p['captions'][0],first)
        edit("redo",{});self.assertEqual(p['captions'][0]['text'],"Texto revisado")
        edit("caption_add",{"start":1,"end":1.5,"text":"Topo","title_font":"mono","title_size":"small","title_position":"top"})
        self.assertEqual(p['timeline'],baseline)
        srt=self.client.call('GET',f"/api/projects/{p['id']}/captions.srt",binary=True).decode('utf-8')
        self.assertIn('00:00:00,350 --> 00:00:00,850',srt);self.assertIn('Texto revisado',srt)
        job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
        output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
        def white_rows(at):
            raw=subprocess.run([executable(),'-v','error','-ss',str(at),'-i',str(output),'-frames:v','1','-vf','format=gray','-f','rawvideo','pipe:1'],capture_output=True,check=True).stdout
            return [i//540 for i,value in enumerate(raw) if value>200]
        self.assertEqual(white_rows(.1),[])
        lower,upper=white_rows(.5),white_rows(1.2)
        self.assertGreater(len(lower),50);self.assertGreater(min(lower),960*.65);self.assertLess(max(lower),960*.85)
        self.assertGreater(len(upper),5);self.assertLess(max(upper),960*.3)
        self.assertGreater(len(lower),len(upper));self.assertAlmostEqual(probe(output)['duration'],1.6,delta=.1)

    def test_export_unavailable_used_sources_fail_before_job_creation(self):
        p=self.client.call("POST","/api/projects",{"name":"Export preflight synthetic"})
        uploaded=self.client.upload(p['id'],self.source);self.wait_job(uploaded['job']['id'])
        p=self.client.call('GET','/api/projects/'+p['id'])
        p=self.client.call('POST',f"/api/projects/{p['id']}/commands",{'operation':'clip_add','args':{'media_id':uploaded['media_id']},'expected_revision':p['revision']})
        before=set(self.server.media.jobs)
        for changes in ({'status':'processing'},{'status':'error'},{'status':'ready','deleted_at':'synthetic'}):
            self.store.update_media(p['id'],uploaded['media_id'],changes);p=self.store.get(p['id'])
            with self.assertRaises(HTTPError) as denied:
                urlopen(Request(self.base+f"/api/projects/{p['id']}/exports",data=json.dumps({'expected_revision':p['revision'],'quality':'preview'}).encode(),headers={'Content-Type':'application/json'},method='POST'))
            self.assertEqual(denied.exception.code,409);self.assertEqual(set(self.server.media.jobs),before)
        self.store.update_media(p['id'],uploaded['media_id'],{'status':'ready','deleted_at':None});p=self.store.get(p['id'])
        with patch.object(self.server.media,'source',return_value=self.root/'absent-synthetic.mp4'):
            with self.assertRaises(HTTPError) as denied:
                urlopen(Request(self.base+f"/api/projects/{p['id']}/exports",data=json.dumps({'expected_revision':p['revision'],'quality':'preview'}).encode(),headers={'Content-Type':'application/json'},method='POST'))
            self.assertEqual(denied.exception.code,409)
        self.assertEqual(set(self.server.media.jobs),before);self.assertEqual(self.store.get(p['id'])['revision'],p['revision'])

    def test_export_presets_render_square_landscape_and_balanced(self):
        p=self.client.call("POST","/api/projects",{"name":"Formats synthetic"})
        imported=self.client.upload(p["id"],self.source);self.wait_job(imported["job"]["id"]);p=self.store.get(p["id"])
        p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_add","args":{"media_id":imported["media_id"],"start":0,"end":.2},"expected_revision":p["revision"]})
        for canvas,quality,dimensions,crf in (("square","preview",(540,540),25),("landscape","balanced",(1280,720),23),("vertical","high",(1080,1920),18)):
            p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"settings_update","args":{"format":canvas},"expected_revision":p["revision"]})
            job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":quality});done=self.wait_job(job["id"])
            details=done["result"];self.assertEqual((details["width"],details["height"]),dimensions)
            self.assertEqual(details["crf"],crf);self.assertGreater(details["bytes"],0)
            self.assertEqual(details["codec"],"h264")
            output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
            self.assertEqual((probe(output)["width"],probe(output)["height"]),dimensions)

    def test_crop_position_and_watermark_render_on_synthetic_pattern(self):
        source=self.root/"red-blue-pattern.mp4"
        run(["-f","lavfi","-i","color=c=red:s=160x90:r=30:d=0.4,drawbox=x=80:y=0:w=80:h=90:color=blue:t=fill","-c:v","libx264","-pix_fmt","yuv420p",source])
        p=self.client.call("POST","/api/projects",{"name":"Framing synthetic"})
        imported=self.client.upload(p["id"],source);self.wait_job(imported["job"]["id"]);p=self.store.get(p["id"])
        p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_add","args":{"media_id":imported["media_id"],"start":0,"end":.3,"framing":"cover","pan_x":0},"expected_revision":p["revision"]})
        clip=p["timeline"][0]
        for pan in (0,1):
            p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_update","args":{"clip_id":clip["id"],"pan_x":pan},"expected_revision":p["revision"]})
            p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"watermark_set","args":{"text":"LILI","position":"top_left","opacity":1},"expected_revision":p["revision"]})
            job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
            output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
            rgb=subprocess.run([executable(),"-v","error","-i",str(output),"-frames:v","1","-vf","crop=2:2:(iw-2)/2:(ih-2)/2,format=rgb24","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
            self.assertGreater(rgb[0 if pan==0 else 2],180)
            raw=subprocess.run([executable(),"-v","error","-i",str(output),"-frames:v","1","-vf","crop=160:120:0:0,format=gray","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
            self.assertGreater(sum(v>200 for v in raw),10)

    def test_appearance_grades_keep_metadata_and_render_each_look(self):
        p=self.client.call("POST","/api/projects",{"name":"Synthetic local looks"})
        imported=self.client.upload(p["id"],self.source);self.wait_job(imported["job"]["id"])
        voice=self.client.upload(p["id"],self.audio);self.wait_job(voice["job"]["id"])
        p=self.store.get(p["id"])
        looks=[(1,1,1),(1.04,.9,.9),(1.02,1.12,1.25),(1,1.16,.82),(1,1.06,0),(1.12,1.02,1.02)]
        for i,_ in enumerate(looks):
            p=self.store.apply(p["id"],"clip_add",{"media_id":imported["media_id"],"start":.2,"end":1.2,"label":f"Scene {i+1}","block_id":"keep-block","volume":.35,"title":"Keep title","title_position":"bottom"},p["revision"])
        p=self.store.apply(p["id"],"narration_set",{"media_id":voice["media_id"],"offset":.2,"volume":.5},p["revision"])
        p=self.store.apply(p["id"],"caption_add",{"start":.1,"end":2,"text":"Keep subtitle"},p["revision"])
        from copy import deepcopy
        baseline=deepcopy(p)
        for clip,(brightness,contrast,saturation) in zip(baseline["timeline"],looks):
            p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_update","args":{"clip_id":clip["id"],"brightness":brightness,"contrast":contrast,"saturation":saturation},"expected_revision":p["revision"]})
            actual=next(c for c in p["timeline"] if c["id"]==clip["id"])
            for key in clip:
                if key not in ("brightness","contrast","saturation"):self.assertEqual(actual[key],clip[key])
        self.assertEqual(p["narration"],baseline["narration"]);self.assertEqual(p["captions"],baseline["captions"]);self.assertEqual(p["duration"],6)
        p=self.store.apply(p["id"],"undo",{},p["revision"]);self.assertEqual(p["timeline"][-1]["brightness"],1)
        p=self.store.apply(p["id"],"redo",{},p["revision"]);self.assertEqual(p["timeline"][-1]["brightness"],1.12)
        job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
        output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
        self.assertAlmostEqual(probe(output)["duration"],6,delta=.2)
        for i,(brightness,contrast,saturation) in enumerate(looks):
            raw=subprocess.run([executable(),"-v","error","-ss",str(i+.5),"-i",str(output),"-frames:v","1","-vf","crop=20:20:(iw-20)/2:(ih-20)/2,scale=1:1,format=rgb24","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
            base=[min(255,max(0,v*brightness*contrast+.5*(1-contrast)*brightness*255)) for v in (0,128,0)]
            luma=sum(a*b for a,b in zip(base,(.2126,.7152,.0722)))
            expected=[min(255,max(0,luma+(v-luma)*saturation)) for v in base]
            self.assertEqual(len(raw),3)
            for actual,value in zip(raw,expected):self.assertAlmostEqual(actual,value,delta=7,msg=f"look {i}")

    def test_color_adjustment_exports_desaturated_pixels(self):
        p=self.client.call("POST","/api/projects",{"name":"Color synthetic"})
        imported=self.client.upload(p["id"],self.source);self.wait_job(imported["job"]["id"]);p=self.store.get(p["id"])
        p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_add","args":{"media_id":imported["media_id"],"start":0,"end":.3,"framing":"cover","saturation":0,"brightness":.8,"contrast":1.1},"expected_revision":p["revision"]})
        job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
        output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
        rgb=subprocess.run([executable(),"-v","error","-i",str(output),"-frames:v","1","-vf","crop=2:2:(iw-2)/2:(ih-2)/2,format=rgb24","-f","rawvideo","pipe:1"],capture_output=True,check=True).stdout
        self.assertLess(max(rgb[:3])-min(rgb[:3]),5)
        self.assertGreater(rgb[0],5)

    def test_speed_export_duration_and_audio_pitch(self):
        import array
        source=self.root/"speed-tone.mp4"
        run(["-f","lavfi","-i","color=c=green:s=160x90:r=30:d=1.6","-f","lavfi","-i","sine=frequency=440:duration=1.6","-shortest","-c:v","libx264","-c:a","aac",source])
        p=self.client.call("POST","/api/projects",{"name":"Speed synthetic"})
        imported=self.client.upload(p["id"],source);self.wait_job(imported["job"]["id"]);p=self.store.get(p["id"])
        p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_add","args":{"media_id":imported["media_id"],"start":.2,"end":1.4},"expected_revision":p["revision"]})
        for speed,length in ((.5,2.4),(2,.6),(4,.3)):
            p=self.client.call("POST",f"/api/projects/{p['id']}/commands",{"operation":"clip_update","args":{"clip_id":p["timeline"][0]["id"],"speed":speed},"expected_revision":p["revision"]})
            job=self.client.call("POST",f"/api/projects/{p['id']}/exports",{"expected_revision":p["revision"],"quality":"preview"});self.wait_job(job["id"])
            output=self.store.folder(p["id"])/"exports"/job["id"]/"video.mp4"
            self.assertAlmostEqual(probe(output)["duration"],length,delta=.12)
            raw=subprocess.run([executable(),"-v","error","-i",str(output),"-vn","-ar","16000","-ac","1","-f","f32le","pipe:1"],capture_output=True,check=True).stdout
            samples=array.array('f');samples.frombytes(raw);samples=samples[int(.05*16000):int((length-.05)*16000)]
            crossings=sum(1 for a,b in zip(samples,samples[1:]) if (a<0<=b) or (b<0<=a))
            self.assertAlmostEqual(crossings/(2*len(samples)/16000),440,delta=15)

    def test_timed_subtitle_crosses_cut_and_srt_download_roundtrips(self):
        p=self.client.call("POST","/api/projects",{"name":"Timed subtitles"})
        imported=self.client.upload(p['id'],self.source);self.wait_job(imported['job']['id']);p=self.store.get(p['id'])
        p=self.client.call('POST',f"/api/projects/{p['id']}/commands",{'operation':'timeline_replace','args':{'clips':[{'media_id':imported['media_id'],'start':0,'end':.5}]*2},'expected_revision':p['revision']})
        p=self.client.call('POST',f"/api/projects/{p['id']}/commands",{'operation':'captions_import','args':{'srt':'1\n00:00:00,200 --> 00:00:00,800\nLegenda no corte'},'expected_revision':p['revision']})
        data=self.client.call('GET',f"/api/projects/{p['id']}/captions.srt",binary=True)
        self.assertIn(b'00:00:00,200 --> 00:00:00,800',data)
        job=self.client.call('POST',f"/api/projects/{p['id']}/exports",{'expected_revision':p['revision'],'quality':'preview'});self.wait_job(job['id'])
        output=self.store.folder(p['id'])/'exports'/job['id']/'video.mp4'
        raw=subprocess.run([executable(),'-v','error','-i',str(output),'-vf','crop=540:300:0:650,format=gray','-f','rawvideo','pipe:1'],capture_output=True,check=True).stdout
        size=540*300;frames=[sum(value>200 for value in raw[i:i+size]) for i in range(0,len(raw),size)]
        self.assertEqual(frames[0],0);self.assertGreater(frames[9],30);self.assertGreater(frames[18],30);self.assertEqual(frames[-1],0)


if __name__ == "__main__":
    unittest.main()
