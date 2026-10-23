"""Opt-in portal session introspection; no production endpoint/configuration yet.

The opaque editor cookie is distinct from the portal login cookie. A future
single-use ticket exchange must mint it before this resolver can be enabled.
"""
import hashlib
import hmac
import json
import re
import time
from http.cookies import CookieError, SimpleCookie
from urllib.request import Request

from .access import Principal
from .portal_agent import PortalClient

COOKIE = "__Host-lili_editor"
_TOKEN = re.compile(r"[a-f0-9]{48}")


class PortalSessionResolver:
    def __init__(self, origin, device_key, *, opener=None, clock=time.time):
        # Reuse the connector's HTTPS origin/key validation and no-redirect
        # opener. The browser cannot choose a destination or supply this key.
        self._client = PortalClient(origin, device_key, opener=opener)
        self.clock = clock

    def __call__(self, request):
        cookies = request.headers.get_all("Cookie", [])
        if len(cookies) != 1 or len(cookies[0]) > 4096:
            return None
        raw = cookies[0]
        # SimpleCookie otherwise silently keeps the last duplicate value.
        if sum(part.strip().split("=", 1)[0] == COOKIE for part in raw.split(";")) != 1:
            return None
        try:
            parsed = SimpleCookie()
            parsed.load(raw)
            token = parsed[COOKIE].value
        except (CookieError, KeyError, ValueError):
            return None
        if _TOKEN.fullmatch(token) is None:
            return None
        return self.validate(token)

    def validate(self, token):
        if not isinstance(token, str) or _TOKEN.fullmatch(token) is None:
            return None
        request = Request(self._client.origin + "/api/device/session/validate",
                          data=json.dumps({"session": token}).encode("ascii"),
                          headers={"Authorization": "Bearer " + self._client.key,
                                   "Content-Type": "application/json", "Accept": "application/json",
                                   "User-Agent": "Lili-Portal-Identity/1.0"})
        try:
            with self._client.opener.open(request, timeout=3) as response:
                if response.status != 200 or response.headers.get_content_type() != "application/json":
                    return None
                raw = response.read(4097)
                if len(raw) > 4096:
                    return None
                result = json.loads(raw)
            if not isinstance(result, dict) or result.get("active") is not True:
                return None
            expires = result.get("expires_at")
            now = self.clock()
            if type(expires) is not int or not now < expires <= now + 86400:
                return None
            digest = result.get("session_hash")
            expected = hashlib.sha256(token.encode("ascii")).hexdigest()
            if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None or not hmac.compare_digest(digest, expected):
                return None
            return Principal(result.get("subject"))
        except (OSError, ValueError, TypeError):
            # No identity cache or shared-login fallback when portal is offline,
            # revoked or malformed. Never expose cookies, keys or response text.
            return None
