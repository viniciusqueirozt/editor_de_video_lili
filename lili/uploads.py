"""Sequential uploads in 8 MiB requests, including through an HTTPS tunnel."""

import threading
from pathlib import Path

from .core import EditorError, number, text, uid
from .media import ALLOWED

CHUNK_SIZE = 8 * 1024**2


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
        size = number(data.get("size"), 1, 2*1024**3)
        if size != int(size):
            raise EditorError("Tamanho de arquivo inválido.")
        with self.lock:
            if len(self.pending) >= 20:
                raise EditorError("Há muitos envios pendentes. Termine os envios atuais ou reinicie o editor.", 409)
            upload_id = uid()
            folder = self.store.folder(project_id)/"media"
            folder.mkdir(exist_ok=True)
            path = folder/(upload_id+".upload")
            path.touch(exist_ok=False)
            self.pending[upload_id] = {"project": project_id, "name": name, "size": int(size), "received": 0, "path": path, "suffix": suffix}
            return {"upload_id": upload_id, "chunk_size": CHUNK_SIZE}

    def find(self, project_id, upload_id):
        item = self.pending.get(upload_id)
        if not item or item["project"] != project_id:
            raise EditorError("Envio não encontrado. Reenvie o arquivo.", 404)
        return item

    def append(self, project_id, upload_id, offset, length, stream):
        with self.lock:
            item = self.find(project_id, upload_id)
            offset = number(offset, 0, item["size"])
            if not 0 < length <= CHUNK_SIZE or offset+length > item["size"]:
                raise EditorError("Bloco de envio inválido.", 413)
            # A lost response may cause the browser to repeat the last block.
            if offset+length == item["received"]:
                return {"received": item["received"]}
            if offset != item["received"]:
                raise EditorError("Os blocos precisam chegar na ordem do arquivo.", 409)
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
