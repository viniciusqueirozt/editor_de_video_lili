import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from lili.access import Principal
from lili.core import Store
from lili.identity import IdentitySigner, IdentityVerifier
from lili.remote import RemoteServer
from lili.server import EditorServer


class GatewayIdentityTests(unittest.TestCase):
    def setUp(self):
        scratch = Path("work/tests")
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "projects")
        self.a, self.b = Principal("a" * 48), Principal("b" * 48)
        # Fake opaque sessions are resolved by server-owned test state only.
        self.sessions = {"session=opaque-a": self.a, "session=opaque-b": self.b}
        key, audience = b"synthetic-only-transport-key-00000", "gateway-test-instance"
        self.editor = EditorServer(("127.0.0.1", 0), self.store,
                                   identity_resolver=IdentityVerifier(key, audience))
        self.gateway = RemoteServer(("127.0.0.1", 0), self.root / "gateway",
                                    self.editor.server_port,
                                    identity_resolver=lambda req: self.sessions.get(req.headers.get("Cookie")),
                                    identity_signer=IdentitySigner(key, audience))
        def forbidden_shared_credential_read():
            raise AssertionError("Individual mode must not inspect shared credentials")
        self.gateway.credential = forbidden_shared_credential_read
        self.threads = []
        for server in (self.editor, self.gateway):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.threads.append(thread)

    def tearDown(self):
        for server in (self.gateway, self.editor):
            server.shutdown()
            server.server_close()
        self.editor.media.pool.shutdown(wait=True)
        for thread in self.threads:
            thread.join(timeout=3)
        self.temp.cleanup()

    def request(self, path="/api/projects", cookie="session=opaque-a", method="GET", body=None, headers=None):
        hdr = {"Origin": f"http://127.0.0.1:{self.gateway.server_port}"}
        if cookie is not None:
            hdr["Cookie"] = cookie
        if body is not None:
            body = json.dumps(body)
            hdr["Content-Type"] = "application/json"
        hdr.update(headers or {})
        conn = http.client.HTTPConnection("127.0.0.1", self.gateway.server_port, timeout=5)
        try:
            conn.request(method, path, body=body, headers=hdr)
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()

    def test_authenticated_gateway_signs_creation_and_filters_other_accounts(self):
        status, body = self.request(method="POST", body={"name": "Synthetic A", "owner_id": self.b.subject})
        self.assertEqual(status, 201)
        project_id = json.loads(body)["id"]
        self.assertEqual(self.store._read(project_id)["access"]["owner_id"], self.a.subject)
        status, body = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[0]["id"], project_id)
        status, body = self.request(cookie="session=opaque-b")
        self.assertEqual((status, json.loads(body)), (200, []))
        self.assertEqual(self.request(f"/api/projects/{project_id}", cookie="session=opaque-b")[0], 404)
        self.assertEqual(self.request(f"/api/projects/{project_id}", cookie="session=opaque-b", headers={
            "X-Lili-Identity": self.a.subject, "X-Lili-Identity-Time": "1",
            "X-Lili-Identity-Nonce": "0" * 32, "X-Lili-Identity-Signature": "0" * 64,
            "Authorization": "Bearer fabricated", "X-Forwarded-User": self.a.subject})[0], 404)
        # A forged inbound assertion cannot corrupt a valid server-resolved A.
        self.assertEqual(self.request(headers={"X-Lili-Identity": self.b.subject})[0], 200)

    def test_revoked_missing_invalid_sessions_never_fall_back_to_shared_login(self):
        self.assertEqual(self.request("/auth/status")[0], 200)
        for path in ("/auth/setup", "/auth/login", "/auth/logout", "/auth/login?ignored=1"):
            self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request("/auth/login", headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertFalse((self.root / "gateway/auth.json").exists())
        for cookie in (None, "session=unknown"):
            self.assertEqual(self.request(cookie=cookie, headers={"X-Lili-Identity": self.a.subject})[0], 401)
        self.sessions["session=opaque-a"] = self.a.subject  # Even a raw ID is insufficient.
        self.assertEqual(self.request()[0], 401)
        self.sessions.pop("session=opaque-a")  # Expiry/revocation checked anew, no identity cache.
        self.assertEqual(self.request()[0], 401)
        self.gateway.identity_resolver = lambda req: (_ for _ in ()).throw(RuntimeError("offline"))
        self.assertEqual(self.request()[0], 502)

    def test_mismatched_transport_is_rejected_and_configuration_requires_both_parts(self):
        self.gateway.identity_signer = IdentitySigner(b"different-synthetic-key-0000000000", "gateway-test-instance")
        self.assertEqual(self.request()[0], 401)
        configurations = ({"identity_resolver": lambda req: self.a},
                          {"identity_signer": self.gateway.identity_signer},
                          {"identity_resolver": "invalid", "identity_signer": self.gateway.identity_signer})
        for config in configurations:
            with self.assertRaises(ValueError):
                RemoteServer(("127.0.0.1", 0), self.root / "unused", **config)
        self.assertFalse((self.root / "unused").exists())
