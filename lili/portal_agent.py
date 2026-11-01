"""Outbound-only connector: reports tunnel health and accepts only reconnect jobs."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent.parent


def tunnel_url(value):
    if not isinstance(value, str) or len(value) > 180:
        return None
    try:
        u = urlsplit(value)
        if (u.scheme == "https" and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com", u.hostname or "")
                and not u.username and not u.password and not u.port and u.path in ("", "/") and not u.query and not u.fragment):
            return f"https://{u.hostname}"
    except ValueError:
        pass
    return None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class PortalClient:
    def __init__(self, origin, key, opener=None):
        u = urlsplit(origin)
        if (u.scheme != "https" or not re.fullmatch(r"[a-z0-9-]+\.[a-z0-9-]+\.chatgpt\.site", u.hostname or "")
                or u.port or u.username or u.password or u.path not in ("", "/") or u.query or u.fragment):
            raise ValueError("Endereço do portal inválido.")
        if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key):
            raise ValueError("Chave de dispositivo inválida.")
        self.origin, self.key = origin.rstrip("/"), key
        self.opener = opener or build_opener(NoRedirect())

    def call(self, action, data=None):
        if action not in ("poll", "report"):
            raise ValueError("Ação do conector não permitida.")
        req = Request(self.origin + "/api/device/" + action,
                      data=json.dumps(data).encode() if data is not None else None,
                      headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json",
                               "User-Agent": "Lili-Portal-Connector/1.0", "Accept": "application/json"})
        with self.opener.open(req, timeout=5) as response:
            raw = response.read(16385)
            if len(raw) > 16384:
                raise ValueError("Resposta do portal muito grande.")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("Resposta do portal inválida.")
            return result


class TunnelController:
    def __init__(self, root=ROOT, probe=None, runner=None, wait=None):
        self.root = Path(root).resolve()
        self.probe = probe or self.healthy
        self.runner = runner or subprocess.run
        self.wait = wait or time.sleep

    @staticmethod
    def healthy(url):
        url = tunnel_url(url)
        if not url:
            return False
        try:
            req = Request(url + "/auth/login", headers={"User-Agent": "Lili-Portal-Connector"})
            with build_opener(NoRedirect()).open(req, timeout=4) as response:
                return response.status == 200 and "Entre no seu estúdio" in response.read(65536).decode("utf-8", errors="replace")
        except (OSError, ValueError):
            return False

    def current(self):
        try:
            url = tunnel_url((self.root / "work/remote/public-url.txt").read_text().strip())
        except OSError:
            url = None
        return {"url": url, "healthy": bool(url and self.probe(url))}

    def reconnect(self):
        state = self.current()
        if state["healthy"]:
            return state
        # A second probe avoids replacing a good link after a transient failure.
        self.wait(3)
        state = self.current()
        if state["healthy"]:
            return state
        script = self.root / "scripts/reconnect-portal-tunnel.ps1"
        result = self.runner(["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-File", str(script)],
                             cwd=self.root, timeout=100, capture_output=True,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise RuntimeError("O notebook não conseguiu restabelecer o túnel.")
        return self.current()


class Agent:
    def __init__(self, client, controller, clock=time.monotonic):
        self.client, self.controller, self.clock = client, controller, clock
        self.future = None
        self.job_id = None
        self.pending_job = None
        self.next_check = 0

    @staticmethod
    def validate_job(job):
        if job is not None and (not isinstance(job, dict) or job.get("action") != "reconnect"
                or not isinstance(job.get("id"), str) or not re.fullmatch(r"[a-f0-9]{48}", job["id"])):
            raise ValueError("O portal retornou uma ação não permitida.")
        return job

    def step(self, executor):
        # Presence is independent of slow external probes and reconnection work.
        job = self.validate_job(self.client.call("poll").get("job"))
        if job:
            self.pending_job = job
        if self.future is not None and self.future.done():
            try:
                state = self.future.result()
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
                state = {"url": None, "healthy": False}
            if self.job_id:
                state = {**state, "jobId": self.job_id}
            try:
                # A normal probe may have finished after a reconnect was claimed.
                if self.job_id or self.pending_job is None:
                    self.client.call("report", state)
            except HTTPError as error:
                if error.code != 409 or not self.job_id:
                    raise
                # The lease expired: never retry that result over a newer job.
            self.future = None
            self.job_id = None
            self.next_check = self.clock() + 15
        if self.future is None:
            if self.pending_job:
                self.job_id = self.pending_job["id"]
                self.pending_job = None
                self.future = executor.submit(self.controller.reconnect)
            elif self.clock() >= self.next_check:
                self.future = executor.submit(self.controller.current)

    def once(self):
        job = self.validate_job(self.client.call("poll").get("job"))
        if job:
            try:
                state = self.controller.reconnect()
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
                self.client.call("report", {"url": None, "healthy": False, "jobId": job["id"]})
                raise RuntimeError("Não foi possível reconectar. O editor e os arquivos foram preservados.") from None
            self.client.call("report", {**state, "jobId": job["id"]})
        else:
            self.client.call("report", self.controller.current())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "work/remote/portal-agent.json"))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    agent = Agent(PortalClient(config["portal_url"], config["device_key"]), TunnelController())
    lock_path = ROOT / "work/remote/portal-agent.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        # A process-wide Windows lock prevents two connectors from managing a tunnel.
        import msvcrt
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise SystemExit("O conector da Lili já está em execução.") from None
        if args.once:
            try:
                agent.once()
            except (OSError, ValueError, RuntimeError):
                raise SystemExit("O portal não respondeu. Verifique a ativação do portal e a conexão do notebook.") from None
            return
        disconnected = False
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="lili-tunnel") as executor:
            while True:
                try:
                    agent.step(executor)
                    if disconnected:
                        print("Comunicação com o portal restabelecida.", flush=True)
                    disconnected = False
                except (OSError, ValueError, RuntimeError):
                    if not disconnected:
                        print("Conector aguardando o portal ou a internet.", flush=True)
                    disconnected = True
                time.sleep(3)


if __name__ == "__main__":
    main()
