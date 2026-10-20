"""Cliente da API local usado pela CLI e pelo MCP."""

import http.client
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


class Client:
    def __init__(self, base="http://127.0.0.1:8765"):
        parsed = urlsplit(base)
        if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost") or parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("Use somente a URL HTTP local do servidor Lili.")
        self.base = base.rstrip("/")
        self.parsed = parsed

    def call(self, method, path, data=None, binary=False):
        body = json.dumps(data).encode() if data is not None else None
        req = Request(self.base + path, data=body, method=method, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=120) as response:
                content = response.read()
                return content if binary else json.loads(content)
        except HTTPError as exc:
            try:
                message = json.loads(exc.read()).get("error", str(exc))
            except ValueError:
                message = str(exc)
            raise ValueError(message) from None

    def upload(self, project_id, filename):
        file = Path(filename).resolve()
        connection = http.client.HTTPConnection(self.parsed.hostname, self.parsed.port or 80, timeout=300)
        try:
            with file.open("rb") as source:
                connection.request("PUT", f"/api/projects/{quote(project_id)}/upload?name={quote(file.name)}", body=source,
                                   headers={"Content-Length": str(file.stat().st_size), "Content-Type": "application/octet-stream"})
            response = connection.getresponse()
            data = json.loads(response.read())
            if response.status >= 400:
                raise ValueError(data.get("error", "Falha na importação."))
            return data
        finally:
            connection.close()
