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


if __name__ == "__main__":
    unittest.main()
