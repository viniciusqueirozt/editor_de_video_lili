"""Read-only discovery of an optional Concat engine over its documented MCP API.

No Concat source is embedded. Editing/rendering is deliberately not exposed until
project translation, capability checks and license/distribution choices are ready.
"""
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path
from .core import EditorError

ROOT=Path(__file__).resolve().parent.parent
REFERENCE_COMMIT="f0c0169628c61de7311f7fc15ee5be82dd611d2e"
MAX_LINE=1024*1024


def find_concat(environ=None):
    env=os.environ if environ is None else environ
    configured=env.get("LILI_CONCAT")
    candidates=[Path(configured)] if configured else [Path(env.get("LOCALAPPDATA",str(Path.home()/"AppData/Local")))/"Programs/Concat/concat.exe",Path(env.get("ProgramFiles","C:/Program Files"))/"Concat/concat.exe"]
    for path in candidates:
        if path.is_absolute() and path.is_file():return path.resolve()
    return None


class ConcatBridge:
    def __init__(self,executable=None,scope=None,popen=None,timeout=10):
        self.executable=Path(executable).resolve() if executable else find_concat()
        self.scope=Path(scope or ROOT/"work/concat-engine").resolve()
        self.popen=popen or subprocess.Popen
        self.timeout=timeout

    def availability(self):
        installed=bool(self.executable and self.executable.is_file())
        return {"installed":installed,"editing_ready":False,"protocol":"mcp_stdio","integration":"read_only_discovery",
                "reference_commit":REFERENCE_COMMIT,"message":"Motor encontrado; a descoberta não ativa efeitos no editor." if installed else "O motor Concat ainda não está instalado/vinculado. A edição atual continua usando FFmpeg."}

    def inspect(self):
        if not self.availability()["installed"]:return self.availability()
        self.scope.mkdir(parents=True,exist_ok=True)
        env={k:v for k,v in os.environ.items() if k in ("PATH","SystemRoot","SYSTEMROOT","WINDIR","TEMP","TMP","USERPROFILE","LOCALAPPDATA","APPDATA")}
        env["CONCAT_MCP_ROOTS"]=str(self.scope)
        try:
            process=self.popen([str(self.executable),"--mcp","headless"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=self.scope,env=env,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        except OSError:
            raise EditorError("Não foi possível iniciar o motor Concat configurado. Confira a instalação no notebook.",503) from None
        incoming=queue.Queue(maxsize=128)
        def read():
            try:
                while True:
                    line=process.stdout.readline(MAX_LINE+1)
                    if not line:incoming.put(None,timeout=1);return
                    if len(line)>MAX_LINE:incoming.put(ValueError("Resposta muito grande"),timeout=1);return
                    incoming.put(line,timeout=1)
            except (OSError,ValueError,queue.Full):
                try:incoming.put_nowait(None)
                except queue.Full:pass
        reader=threading.Thread(target=read,daemon=True,name="lili-concat-read");reader.start()
        deadline=time.monotonic()+self.timeout;serial=0
        def send(payload):
            process.stdin.write(json.dumps(payload,allow_nan=False).encode("utf-8")+b"\n");process.stdin.flush()
        def request(method,params):
            nonlocal serial
            serial+=1;request_id=serial;send({"jsonrpc":"2.0","id":request_id,"method":method,"params":params})
            for _ in range(128):
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError
                raw=incoming.get(timeout=remaining)
                if raw is None or isinstance(raw,Exception):raise ValueError("Resposta indisponível")
                value=json.loads(raw)
                if not isinstance(value,dict) or value.get("id")!=request_id:continue
                if value.get("error") or not isinstance(value.get("result"),dict):raise ValueError("Resposta recusada")
                return value["result"]
            raise ValueError("Excesso de mensagens")
        def unpack(result):
            if result.get("isError"):raise ValueError("Consulta recusada")
            if isinstance(result.get("structuredContent"),dict):return result["structuredContent"]
            for item in result.get("content",[]):
                if item.get("type")=="text":
                    try:return json.loads(item["text"])
                    except (ValueError,TypeError):continue
            return result
        try:
            initialized=request("initialize",{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"lili","version":"0.1.0"}})
            send({"jsonrpc":"2.0","method":"notifications/initialized"})
            tools=[];cursor=None;cursors=set()
            for _ in range(16):
                result=request("tools/list",{} if cursor is None else {"cursor":cursor})
                page=result.get("tools")
                if not isinstance(page,list) or any(not isinstance(t,dict) or not isinstance(t.get("name"),str) for t in page):raise ValueError("Catálogo inválido")
                tools.extend(page);cursor=result.get("nextCursor")
                if not cursor:break
                if not isinstance(cursor,str) or cursor in cursors:raise ValueError("Paginação inválida")
                cursors.add(cursor)
            else:raise ValueError("Catálogo muito grande")
            names={t["name"] for t in tools}
            version=unpack(request("tools/call",{"name":"concat_version","arguments":{}})) if "concat_version" in names else initialized.get("serverInfo",{})
            catalogue=unpack(request("tools/call",{"name":"effects_list","arguments":{}})) if "effects_list" in names else None
            return {**self.availability(),"discovery_ok":True,"engine":version,"tools":tools,"catalogue":catalogue}
        except (OSError,ValueError,TypeError,queue.Empty,TimeoutError) as error:
            raise EditorError("O Concat não respondeu a uma descoberta válida no prazo. A montagem da Lili foi preservada.",503) from None
        finally:
            try:process.stdin.close()
            except OSError:pass
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
            reader.join(timeout=.2)
