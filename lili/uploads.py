"""Sequential uploads in 8 MiB requests, including through an HTTPS tunnel."""

import threading
import shutil
import re
from pathlib import Path

from .core import EditorError, text, uid
from .media import ALLOWED

CHUNK_SIZE = 8 * 1024**2
DISK_HEADROOM = 256 * 1024**2


class Uploads:
    def __init__(self, store, media):
        self.store, self.media = store, media
        self.pending = {}
        self.lock = threading.RLock()

    def start(self, project_id, data):
        self.store.get(project_id)
        name = text(data.get("name", ""), 240)
        suffix = Path(name).suffix.lower()
        if suffix not in ALLOWED:
            raise EditorError("Envie um vídeo ou áudio compatível.", 415)
        size = data.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= 2*1024**3:
            raise EditorError("Informe o tamanho do arquivo como um número inteiro de bytes, até 2 GB.")
        with self.lock:
            if len(self.pending) >= 20:
                raise EditorError("Há muitos envios pendentes. Termine os envios atuais ou reinicie o editor.", 409)
            upload_id = uid()
            folder = self.store.folder(project_id)/"media"
            folder.mkdir(exist_ok=True)
            # Reserve outstanding bytes across projects, not just this request.
            remaining = sum(item["size"] - item["received"] for item in self.pending.values())
            self.require_space(folder, remaining + size)
            path = folder/(upload_id+".upload")
            path.touch(exist_ok=False)
            self.pending[upload_id] = {"project": project_id, "name": name, "size": int(size), "received": 0, "path": path, "suffix": suffix}
            return {"upload_id": upload_id, "chunk_size": CHUNK_SIZE}

    @staticmethod
    def require_space(folder, incoming):
        try:
            free = shutil.disk_usage(folder).free
        except OSError:
            raise EditorError("Não foi possível verificar o espaço livre do notebook. Tente novamente.", 503) from None
        if free < incoming + DISK_HEADROOM:
            raise EditorError("Espaço insuficiente no notebook. Libere espaço e tente novamente; seus arquivos recebidos foram preservados.", 507)

    def find(self, project_id, upload_id):
        item = self.pending.get(upload_id)
        if not item or item["project"] != project_id:
            raise EditorError("Envio não encontrado. Reenvie o arquivo.", 404)
        return item

    def append(self, project_id, upload_id, offset, length, stream):
        with self.lock:
            item = self.find(project_id, upload_id)
            if isinstance(offset, str) and re.fullmatch(r"[0-9]{1,12}", offset):
                offset = int(offset)
            if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= item["size"]:
                raise EditorError("A posição do bloco precisa ser um número inteiro válido.")
            if isinstance(length, bool) or not isinstance(length, int) or not 0 < length <= CHUNK_SIZE or offset+length > item["size"]:
                raise EditorError("Bloco de envio inválido.", 413)
            # A retry is acknowledged only when its entire body matches the
            # bytes already on disk. Never acknowledge an unread request body.
            if offset+length == item["received"]:
                with item["path"].open("rb") as original:
                    original.seek(offset)
                    remaining = length
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            raise EditorError("Reenvio interrompido. Tente novamente.")
                        if chunk != original.read(len(chunk)):
                            raise EditorError("O bloco reenviado difere do arquivo recebido. Reenvie o mesmo bloco ou importe o arquivo novamente.", 409)
                        remaining -= len(chunk)
                return {"received": item["received"]}
            if offset != item["received"]:
                raise EditorError("Os blocos precisam chegar na ordem do arquivo.", 409)
            self.require_space(item["path"].parent, length)
            with item["path"].open("r+b") as out:
                out.seek(item["received"])
                try:
                    remaining = length
                    while remaining:
                        chunk = stream.read(min(65536, remaining))
                        if not chunk:
                            raise EditorError("Envio interrompido. Tente novamente.")
                        out.write(chunk)
                        remaining -= len(chunk)
                except Exception:
                    out.truncate(item["received"])
                    raise
            item["received"] += length
            return {"received": item["received"]}

    def complete(self, project_id, upload_id):
        with self.lock:
            item = self.find(project_id, upload_id)
            if item["received"] != item["size"]:
                raise EditorError("O envio ainda não terminou.", 409)
            target = item["path"].with_suffix(item["suffix"])
            item["path"].replace(target)
            result = self.media.register(project_id, target, item["name"], upload_id)
            del self.pending[upload_id]
            return result
