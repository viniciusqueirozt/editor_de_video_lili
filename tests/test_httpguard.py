import http.client
import threading
import tempfile
import unittest
from email.message import Message
from pathlib import Path

from lili.core import EditorError, Store
from lili.httpguard import validate_headers
from lili.remote import RemoteServer
from lili.server import EditorServer


class HTTPGuardTests(unittest.TestCase):
    def test_rejects_ambiguous_or_unsupported_body_framing(self):
        cases = [[("Content-Length", "1"), ("Content-Length", "2")],
                 [("Content-Length", "2, 2")], [("Content-Length", "-1")],
                 [("Content-Length", "+2")], [("Content-Length", "1.5")],
                 [("Transfer-Encoding", "chunked")], [("Transfer-Encoding", "")],
                 [("Host", "localhost"), ("Host", "foreign.test")],
                 [("Content-Length", str(2 * 1024**3 + 1))]]
        for entries in cases:
            headers = Message()
            for key, value in entries:
                headers[key] = value
            with self.subTest(entries=entries), self.assertRaises(EditorError):
                validate_headers(headers)
        self.assertEqual(validate_headers(Message()), 0)
        headers = Message()
        headers["Content-Length"] = "8388608"
        self.assertEqual(validate_headers(headers), 8388608)

    def test_both_servers_reject_duplicate_lengths_before_reading_a_body(self):
        root = Path("work/tests").resolve()
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as scratch:
            editor = EditorServer(("127.0.0.1", 0), Store(Path(scratch) / "data"))
            remote = RemoteServer(("127.0.0.1", 0), Path(scratch) / "remote", editor.server_port)
            try:
                for server in (editor, remote):
                    thread = threading.Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                    try:
                        conn.putrequest("POST", "/auth/login")
                        conn.putheader("Content-Length", "9999")
                        conn.putheader("Content-Length", "0")
                        conn.endheaders()
                        response = conn.getresponse()
                        self.assertEqual(response.status, 400)
                        response.read()
                    finally:
                        conn.close()
                    server.shutdown()
                    thread.join(timeout=3)
            finally:
                remote.server_close()
                editor.server_close()
                editor.media.pool.shutdown(wait=True)

    def test_security_singletons_reject_duplicates_regardless_of_case(self):
        for name in ("Host", "Origin", "Sec-Fetch-Site", "Content-Type", "Cookie", "Authorization"):
            headers = Message()
            headers[name] = "first"
            headers[name.lower()] = "second"
            with self.subTest(name=name), self.assertRaises(EditorError):
                validate_headers(headers)
        headers = Message()
        headers["Cookie"] = "session=opaque; theme=light"
        headers["Origin"] = "https://example.invalid"
        headers["Content-Type"] = "application/json; charset=utf-8"
        self.assertEqual(validate_headers(headers), 0)

    def test_both_servers_reject_ambiguous_security_fields_before_authentication(self):
        root = Path("work/tests").resolve()
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as scratch:
            editor = EditorServer(("127.0.0.1", 0), Store(Path(scratch) / "data"))
            remote = RemoteServer(("127.0.0.1", 0), Path(scratch) / "remote", editor.server_port)
            threads = []
            try:
                for server in (editor, remote):
                    thread = threading.Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    threads.append(thread)
                    for name in ("Origin", "Sec-Fetch-Site", "Content-Type", "Cookie", "Authorization"):
                        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                        try:
                            conn.putrequest("POST", "/auth/setup")
                            conn.putheader("Content-Length", "1000")
                            conn.putheader(name, "first")
                            conn.putheader(name.lower(), "second")
                            conn.endheaders()  # No body: rejection must precede reads/auth.
                            response = conn.getresponse()
                            self.assertEqual(response.status, 400, name)
                            response.read()
                        finally:
                            conn.close()
                self.assertFalse((Path(scratch) / "remote/auth.json").exists())
            finally:
                for server in (remote, editor):
                    server.shutdown()
                    server.server_close()
                for thread in threads:
                    thread.join(timeout=3)
                editor.media.pool.shutdown(wait=True)
