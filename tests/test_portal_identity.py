import hashlib
import json
import unittest
from email.message import Message
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

from lili.access import Principal
from lili.portal_identity import COOKIE, PortalSessionResolver
from lili.portal_agent import NoRedirect


class PortalIdentityTests(unittest.TestCase):
    def setUp(self):
        self.token = "a" * 48
        self.now = 1700000000
        self.opener = Mock()
        self.resolver = PortalSessionResolver("https://portal.owner.chatgpt.site", "b" * 64,
                                              opener=self.opener, clock=lambda: self.now)
        self.result = {"active": True, "subject": "c" * 48, "expires_at": self.now + 60,
                       "session_hash": hashlib.sha256(self.token.encode()).hexdigest()}
        self.response = Mock(status=200)
        self.response.headers = Message()
        self.response.headers["Content-Type"] = "application/json"
        self.response.__enter__ = Mock(return_value=self.response)
        self.response.__exit__ = Mock(return_value=False)
        self.opener.open.return_value = self.response
        self.set_response(self.result)

    def set_response(self, value):
        self.response.read.return_value = json.dumps(value).encode()

    def request(self, raw=None):
        headers = Message()
        headers["Cookie"] = raw if raw is not None else f"{COOKIE}={self.token}"
        return SimpleNamespace(headers=headers)

    def test_fixed_https_backchannel_and_token_bound_identity(self):
        self.assertEqual(self.resolver(self.request()), Principal(self.result["subject"]))
        req = self.opener.open.call_args.args[0]
        self.assertEqual(req.full_url, "https://portal.owner.chatgpt.site/api/device/session/validate")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {"session": self.token})
        self.assertNotIn(self.token, req.full_url)
        self.assertEqual(req.get_header("Authorization"), "Bearer " + "b" * 64)
        self.assertEqual(self.opener.open.call_args.kwargs, {"timeout": 3})
        # No cached authorization: revocation and expiry affect the next request.
        self.set_response({"active": False})
        self.assertIsNone(self.resolver(self.request()))
        self.set_response(self.result)
        self.now += 61
        self.assertIsNone(self.resolver(self.request()))
        self.assertEqual(self.opener.open.call_count, 3)

    def test_ambiguous_or_forged_cookies_do_not_reach_the_portal(self):
        requests = [self.request(f"{COOKIE}={self.token}; {COOKIE}={self.token}"),
                    self.request(f"{COOKIE}=free-user-id"), self.request("unrelated=x"),
                    self.request(f"{COOKIE}=" + "a" * 4097)]
        missing = SimpleNamespace(headers=Message())
        duplicated = self.request()
        duplicated.headers["Cookie"] = f"{COOKIE}={self.token}"
        for req in requests + [missing, duplicated]:
            req.headers["X-Lili-Identity"] = "c" * 48
            self.assertIsNone(self.resolver(req))
        self.opener.open.assert_not_called()

    def test_invalid_expired_mismatched_and_oversize_responses_fail_closed(self):
        changes = ({"active": 1}, {"active": False}, {"subject": "bad"},
                   {"expires_at": self.now}, {"expires_at": True},
                   {"expires_at": self.now + 86401}, {"session_hash": "f" * 64},
                   {"session_hash": None})
        for change in changes:
            self.set_response({**self.result, **change})
            self.assertIsNone(self.resolver(self.request()), change)
        for value in (None, [], "wrong", {"active": True}):
            self.set_response(value)
            self.assertIsNone(self.resolver(self.request()))
        for raw in (b"not json", b"x" * 4097):
            self.response.read.return_value = raw
            self.assertIsNone(self.resolver(self.request()))
        self.set_response(self.result)
        self.response.status = 202
        self.assertIsNone(self.resolver(self.request()))
        self.response.status = 200
        self.response.headers.replace_header("Content-Type", "text/html")
        self.assertIsNone(self.resolver(self.request()))

    def test_network_redirect_and_origin_guards(self):
        for error in (URLError("offline"), TimeoutError(), HTTPError("https://example.invalid", 302, "redirect", {}, None)):
            self.opener.open.side_effect = error
            self.assertIsNone(self.resolver(self.request()))
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))
        for origin in ("http://portal.owner.chatgpt.site", "https://evil.example", "https://portal.owner.chatgpt.site/path"):
            with self.assertRaises(ValueError):
                PortalSessionResolver(origin, "b" * 64)
