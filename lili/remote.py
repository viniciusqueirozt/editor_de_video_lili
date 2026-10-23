"""Authenticated loopback gateway. Only this port may be exposed by a tunnel.

The editing server stays on localhost. The gateway never trusts forwarded
headers to bypass authentication, and stores no plaintext password.
"""

import argparse
import hashlib
import hmac
import html
import http.client
import json
import secrets
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .access import Principal
from .identity import IdentitySigner

COOKIE = "lili_session"
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}


class RemoteServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, root, editor_port=8765, *, identity_resolver=None, identity_signer=None):
        # Opt-in only: both ends must be wired by trusted startup code. The
        # resolver must validate the portal session on every request, without
        # trusting user IDs from the browser or falling back to shared login.
        if (identity_resolver is None) != (identity_signer is None):
            raise ValueError("Individual identity requires a resolver and signer together")
        if identity_resolver is not None and (not callable(identity_resolver) or not isinstance(identity_signer, IdentitySigner)):
            raise ValueError("Invalid individual identity configuration")
        self.identity_resolver = identity_resolver
        self.identity_signer = identity_signer
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.editor_port = editor_port
        self.sessions = {}
        self.failures = []
        self.auth_lock = threading.RLock()
        super().__init__(address, RemoteHandler)

    def credential(self):
        path = self.root / "auth.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def public_origin(self):
        path = self.root / "public-url.txt"
        if not path.exists():
            return None
        url = urlsplit(path.read_text().strip())
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.port or url.path not in ("", "/") or url.query or url.fragment:
            return None
        return f"https://{url.hostname}"


class RemoteHandler(BaseHTTPRequestHandler):
    server_version = "Lili"

    def setup(self):
        super().setup()
        self.connection.settimeout(120)

    def log_message(self, *args):
        # No URLs, credentials or session cookies in logs.
        pass

    def do_GET(self):
        self.dispatch()

    def do_HEAD(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def do_PUT(self):
        self.dispatch()

    def origins(self):
        port = self.server.server_port
        local = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
        public = self.server.public_origin()
        return local | ({public} if public else set())

    def origin(self):
        host = self.headers.get("Host", "")
        return next((origin for origin in self.origins() if urlsplit(origin).netloc == host), None)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        super().end_headers()

    def send(self, body, status=200, headers=None):
        body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def form(self, setup=False, error="", status=200):
        heading = "Prepare seu acesso" if setup else "Entre no seu estúdio"
        explanation = "Crie o login que vocês usarão no iPhone. Guarde a senha; ela não será enviada para o Codex." if setup else "Seu material e suas histórias ficam no seu estúdio."
        confirmation = '<label for="confirmation">Repita a senha</label><input id="confirmation" name="confirmation" type="password" autocomplete="new-password" required minlength="12">' if setup else ""
        autocomplete = "new-password" if setup else "current-password"
        action = "/auth/setup" if setup else "/auth/login"
        body = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#f7f6f2"><title>Lili · Acesso</title><link rel="icon" href="/favicon.svg?v=ritmo-1" type="image/svg+xml"><link rel="apple-touch-icon" href="/icon-192.png?v=ritmo-1"><style>
        *{{box-sizing:border-box}}body{{margin:0;min-height:100dvh;display:grid;place-items:center;padding:24px;background:#f7f6f2;color:#292d29;font:15px/1.6 'Segoe UI',Arial,sans-serif}}main{{width:100%;max-width:400px;padding:32px;background:white;border:1px solid #e7e7df;border-radius:20px}}.brand{{font:700 44px Georgia;color:#e76548}}h1{{font-size:23px;margin:20px 0 10px}}p{{color:#687268;font-size:14px}}label{{display:block;font-size:13px;margin:20px 0 7px}}input,button{{font:inherit;font-size:16px;width:100%;padding:12px;border-radius:8px;border:1px solid #dce0d5}}button{{background:#e76548;color:white;border:0;margin-top:24px;font-weight:600;cursor:pointer;touch-action:manipulation}}.error{{color:#a03f2a;background:#fff0ea;padding:10px;border-radius:8px}}small{{display:block;margin-top:20px;color:#778170}}input:focus-visible,button:focus-visible{{outline:2px solid #66856c;outline-offset:3px}}</style></head><body><main><div class="brand"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="64" height="64" style="stroke:none" role="img" aria-label="Lili"><rect x="18" y="20" width="16" height="72" rx="8" fill="#283c30"/><circle cx="52" cy="40" r="8" fill="#789460"/><rect x="44" y="58" width="16" height="50" rx="8" fill="#283c30"/><rect x="70" y="20" width="16" height="72" rx="8" fill="#283c30"/><circle cx="104" cy="40" r="8" fill="#789460"/><rect x="96" y="58" width="16" height="50" rx="8" fill="#283c30"/></svg></div><h1>{heading}</h1><p>{explanation}</p>{f'<p class="error" role="alert">{html.escape(error)}</p>' if error else ''}<form method="post" action="{action}"><label for="username">Usuário</label><input id="username" name="username" autocomplete="username" autocapitalize="none" maxlength="60" required><label for="password">Senha{' · pelo menos 12 caracteres' if setup else ''}</label><input id="password" name="password" type="password" autocomplete="{autocomplete}" maxlength="256" {'minlength="12"' if setup else ''} required>{confirmation}<button>{'Criar acesso' if setup else 'Entrar'}</button></form><small>{'O acesso externo só será ativado na próxima etapa.' if setup else 'Mantenha o computador do estúdio ligado e conectado.'}</small></main></body></html>'''
        self.send(body, status)

    def read_form(self):
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            raise ValueError("Formulário inválido.")
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size <= 4096:
            raise ValueError("Formulário inválido.")
        data = parse_qs(self.rfile.read(size).decode("utf-8"))
        return {key: values[0] for key, values in data.items()}

    def authenticated(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            token = cookie[COOKIE].value
        except (KeyError, ValueError):
            return False
        with self.server.auth_lock:
            return self.server.sessions.get(hashlib.sha256(token.encode()).hexdigest(), 0) > time.time()

    def auth(self, setup):
        local = self.origin().startswith("http://")
        with self.server.auth_lock:
            credential = self.server.credential()
            if setup and (credential or not local):
                return self.send("Página não encontrada.", 404)
            if not setup and not credential:
                return self.form(True) if local else self.send("Acesso não configurado.", 503)
            if self.command in ("GET", "HEAD"):
                return self.form(setup)
            if self.command != "POST":
                return self.send("Método não permitido.", 405)
            data = self.read_form()
            username, password = data.get("username", "").strip(), data.get("password", "")
            if setup:
                if not 2 <= len(username) <= 60 or not 12 <= len(password) <= 256 or password != data.get("confirmation"):
                    return self.form(True, "Use um usuário com 2 a 60 caracteres e uma senha de pelo menos 12 caracteres. Repita a mesma senha.", 400)
                salt = secrets.token_hex(16)
                credential = {"username": username, "salt": salt, "hash": hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()}
                # Exclusive creation: an existing account cannot be overwritten.
                with (self.server.root / "auth.json").open("x", encoding="utf-8") as target:
                    json.dump(credential, target)
                return self.send("", 303, {"Location": "/auth/login"})
            self.server.failures = [t for t in self.server.failures if time.time()-t < 900]
            if len(self.server.failures) >= 8:
                return self.form(False, "Muitas tentativas. Aguarde 15 minutos antes de tentar novamente.", 429)
            hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(credential["salt"]), 600000).hex()
            if not hmac.compare_digest(username.encode(), credential["username"].encode()) or not hmac.compare_digest(hashed, credential["hash"]):
                self.server.failures.append(time.time())
                return self.form(False, "Usuário ou senha incorretos.", 401)
            self.server.failures.clear()
            self.server.sessions = {key:expiry for key,expiry in self.server.sessions.items() if expiry>time.time()}
            token = secrets.token_urlsafe(32)
            self.server.sessions[hashlib.sha256(token.encode()).hexdigest()] = time.time()+86400
            secure = "; Secure" if not local else ""
            return self.send("", 303, {"Location": "/", "Set-Cookie": f"{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400{secure}"})

    def dispatch(self):
        try:
            from .httpguard import validate_headers
            validate_headers(self.headers)
            origin = self.origin()
            if not origin:
                return self.send("Endereço não permitido.", 403)
            if self.headers.get("Sec-Fetch-Site") == "cross-site":
                if self.server.identity_resolver is not None:
                    return self.send("Origem não permitida.", 403)
                # Entry pages contain only the public login form. Do not rely
                # on optional navigation metadata from mobile/embedded browsers,
                # and never proxy an authenticated cross-site entry request.
                if self.command == "GET" and self.path == "/":
                    return self.send("", 303, {"Location": "/auth/login"})
                if self.command == "GET" and self.path == "/auth/login":
                    return self.auth(False)
                return self.send("Origem não permitida.", 403)
            if self.command not in ("GET", "HEAD"):
                request_origin = self.headers.get("Origin")
                # A privacy-preserving browser can send Origin: null on a form
                # navigation. Fetch Metadata is browser-controlled, so accept
                # only same-origin requests in that case, never same-site or
                # cross-site. An explicit foreign Origin is always rejected.
                metadata_same_origin = self.headers.get("Sec-Fetch-Site") == "same-origin"
                if request_origin != origin and not (request_origin in (None, "null") and metadata_same_origin):
                    return self.send("Origem não permitida.", 403)
            self.principal = None
            if self.server.identity_resolver is not None:
                principal = self.server.identity_resolver(self)
                if not isinstance(principal, Principal):
                    return self.send("Entre pelo portal para acessar o estúdio.", 401)
                self.principal = principal
                if self.path == "/auth/status" and self.command == "GET":
                    return self.send(json.dumps({"authenticated": True}))
                if urlsplit(self.path).path.startswith("/auth/"):
                    return self.send("Use sua conta individual no portal.", 404)
                return self.proxy()
            if self.command in ("GET", "HEAD") and urlsplit(self.path).path in ("/favicon.svg", "/icon-192.png", "/icon-512.png"):
                # Only public branding assets, never project media or APIs.
                return self.proxy()
            if self.path in ("/auth/login", "/auth/setup"):
                return self.auth(self.path == "/auth/setup")
            if not self.server.credential():
                return self.send("", 303, {"Location": "/auth/setup"}) if origin.startswith("http://") else self.send("Acesso não configurado.", 503)
            if not self.authenticated():
                if self.path.startswith("/api/"):
                    return self.send('{"error":"Entre novamente para acessar o estúdio."}', 401)
                return self.send("", 303, {"Location": "/auth/login"})
            if self.path == "/auth/status" and self.command == "GET":
                return self.send(json.dumps({"authenticated": True}))
            if self.path == "/auth/logout" and self.command == "POST":
                cookie = SimpleCookie(self.headers.get("Cookie", ""))
                with self.server.auth_lock:
                    self.server.sessions.pop(hashlib.sha256(cookie[COOKIE].value.encode()).hexdigest(), None)
                return self.send("", 303, {"Location": "/auth/login", "Set-Cookie": f"{COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"})
            self.proxy()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except (ValueError, UnicodeError):
            self.send("Solicitação inválida.", 400)
        except Exception:
            self.send("O estúdio está indisponível. Verifique se o editor está aberto no computador.", 502)

    def proxy(self):
        if not self.path.startswith("/") or self.path.startswith("//"):
            return self.send("Caminho inválido.", 400)
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 <= size <= 2*1024**3 or self.headers.get("Transfer-Encoding"):
            return self.send("Envio inválido.", 413)
        target = http.client.HTTPConnection("127.0.0.1", self.server.editor_port, timeout=300)
        try:
            target.putrequest(self.command, self.path, skip_host=True, skip_accept_encoding=True)
            target.putheader("Host", f"127.0.0.1:{self.server.editor_port}")
            for key in ("Content-Type", "Content-Length", "Range", "Accept"):
                if self.headers.get(key):
                    target.putheader(key, self.headers[key])
            if self.command not in ("GET", "HEAD"):
                target.putheader("Origin", f"http://127.0.0.1:{self.server.editor_port}")
            if self.server.identity_signer is not None:
                # The allowlist above discards all browser identity assertions,
                # cookies and authorization headers. Mint a fresh local proof.
                signed = self.server.identity_signer.headers(
                    self.principal, self.command, self.path, length=size,
                    content_type=self.headers.get("Content-Type", ""))
                for key, value in signed.items():
                    target.putheader(key, value)
            target.endheaders()
            remaining = size
            while remaining:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    raise ValueError("Envio interrompido")
                target.send(chunk)
                remaining -= len(chunk)
            response = target.getresponse()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in HOP | {"server", "date", "cache-control", "content-security-policy", "x-content-type-options", "referrer-policy", "set-cookie"}:
                    self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                while chunk := response.read(65536):
                    self.wfile.write(chunk)
        finally:
            target.close()


def main():
    parser = argparse.ArgumentParser(description="Login para acesso remoto à Lili")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--editor-port", type=int, default=8765)
    parser.add_argument("--root", default="work/remote")
    args = parser.parse_args()
    server = RemoteServer(("127.0.0.1", args.port), args.root, args.editor_port)
    print(f"Prepare o login em http://127.0.0.1:{args.port}/auth/setup", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
