"""Estado de projeto, revisões e operações independentes do motor de vídeo."""

import copy
import json
import math
import re
import threading
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path


class EditorError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def uid():
    return uuid.uuid4().hex


def now():
    return datetime.now(timezone.utc).isoformat()


def number(value, minimum=0, maximum=86400):
    if isinstance(value, bool):
        raise EditorError("Informe um número válido.")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise EditorError("Informe um número válido.") from None
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise EditorError(f"O valor deve estar entre {minimum} e {maximum}.")
    return round(value, 4)


def text(value, limit=20000):
    if not isinstance(value, str) or len(value) > limit:
        raise EditorError(f"Texto inválido. Limite: {limit} caracteres.")
    return value.strip()


def tokens(value):
    value = unicodedata.normalize("NFKD", value.lower())
    words = re.findall(r"[a-z0-9]+", "".join(c for c in value if not unicodedata.combining(c)))
    return {w for w in words if len(w) > 3}


def script_blocks(script):
    return [{"id": f"bloco-{i + 1}", "text": part.strip()}
            for i, part in enumerate(re.split(r"\n\s*\n", script.strip())) if part.strip()]


def duration(project):
    return round(sum(c["end"] - c["start"] for c in project["timeline"]), 4)


class Store:
    SNAPSHOT_FIELDS = ("name", "script", "timeline", "narration", "settings")

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def folder(self, project_id):
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise EditorError("Projeto não encontrado.", 404)
        return self.root / project_id

    def _read(self, project_id):
        try:
            return json.loads((self.folder(project_id) / "project.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise EditorError("Projeto não encontrado.", 404) from None

    def _write(self, project):
        folder = self.folder(project["id"])
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "project.json"
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        temp.replace(target)

    @staticmethod
    def public(project):
        result = copy.deepcopy(project)
        result["undo_available"] = bool(result.pop("history", []))
        result["duration"] = duration(result)
        result["blocks"] = script_blocks(result["script"])
        return result

    def get(self, project_id):
        with self.lock:
            return self.public(self._read(project_id))

    def list(self):
        with self.lock:
            result = []
            for path in self.root.glob("*/project.json"):
                p = self._read(path.parent.name)
                result.append({k: p[k] for k in ("id", "name", "revision", "updated_at", "description")})
            return sorted(result, key=lambda p: p["updated_at"], reverse=True)

    def create(self, name, script="", description=""):
        with self.lock:
            p = {"id": uid(), "name": text(name, 120) or "Novo projeto", "script": text(script),
                 "description": text(description, 1000), "revision": 1, "updated_at": now(),
                 "media": [], "timeline": [], "narration": None, "requests": [], "history": [],
                 "settings": {"width": 1080, "height": 1920, "fps": 30},
                 "last_change": {"actor": "editor", "operation": "create"}}
            self._write(p)
            return self.public(p)

    def media(self, project_id, media_id):
        p = self.get(project_id)
        return self.find(p["media"], media_id, "Arquivo")

    @staticmethod
    def find(items, item_id, label="Cena"):
        for item in items:
            if item["id"] == item_id:
                return item
        raise EditorError(f"{label} não encontrado.", 404)

    def add_media(self, project_id, media):
        with self.lock:
            p = self._read(project_id)
            p["media"].append(media)
            self._touch(p, "system", "media_import")
            self._write(p)

    def update_media(self, project_id, media_id, changes):
        with self.lock:
            p = self._read(project_id)
            self.find(p["media"], media_id, "Arquivo").update(changes)
            self._touch(p, "system", "media_ready")
            self._write(p)

    @staticmethod
    def _touch(p, actor, operation):
        p["revision"] += 1
        p["updated_at"] = now()
        p["last_change"] = {"actor": actor, "operation": operation}

    def validate_clip(self, p, data):
        if not isinstance(data, dict):
            raise EditorError("Cada cena precisa ser um objeto com arquivo, entrada e saída.")
        asset = self.find(p["media"], data.get("media_id"), "Arquivo")
        if asset.get("status") != "ready" or asset.get("kind") != "video":
            raise EditorError("Escolha um vídeo que já terminou de importar.")
        start = number(data.get("start", 0), 0, asset["duration"])
        end = number(data.get("end", asset["duration"]), 0, asset["duration"])
        if end - start < 0.1:
            raise EditorError("A cena precisa ter pelo menos 0,1 segundo.")
        clip_id = data.get("id", uid())
        if not isinstance(clip_id, str) or not re.fullmatch(r"[a-f0-9]{32}", clip_id):
            raise EditorError("Identificador de cena inválido.")
        if not isinstance(data.get("locked", False), bool):
            raise EditorError("A proteção de cena deve ser verdadeira ou falsa.")
        return {"id": clip_id, "media_id": asset["id"], "start": start, "end": end,
                "label": text(data.get("label", asset["name"]), 160), "title": text(data.get("title", ""), 160),
                "volume": number(data.get("volume", 1), 0, 2), "locked": data.get("locked", False),
                "block_id": text(data.get("block_id", ""), 80)}

    def apply(self, project_id, operation, args, expected_revision, actor="editor"):
        if not isinstance(args, dict):
            raise EditorError("Os argumentos devem ser um objeto.")
        with self.lock:
            p = self._read(project_id)
            if isinstance(expected_revision, bool) or expected_revision != p["revision"]:
                raise EditorError("O projeto mudou. Atualize a página ou leia a revisão atual antes de editar.", 409)
            snapshot = {k: copy.deepcopy(p[k]) for k in self.SNAPSHOT_FIELDS}
            if operation == "script_update":
                p["script"] = text(args.get("script", p["script"]))
                p["name"] = text(args.get("name", p["name"]), 120) or p["name"]
            elif operation == "media_annotate":
                asset = self.find(p["media"], args.get("media_id"), "Arquivo")
                tags = args.get("tags", asset.get("tags", []))
                if not isinstance(tags, list) or len(tags) > 40:
                    raise EditorError("Use até 40 etiquetas.")
                asset["tags"] = [text(t, 80) for t in tags if text(t, 80)]
                asset["note"] = text(args.get("note", asset.get("note", "")), 2000)
            elif operation == "clip_add":
                p["timeline"].append(self.validate_clip(p, args))
            elif operation == "clip_update":
                clip = self.find(p["timeline"], args.get("clip_id"))
                changes = {k: v for k, v in args.items() if k not in ("clip_id", "id")}
                if clip["locked"] and any(k != "locked" and clip.get(k) != v for k, v in changes.items()):
                    raise EditorError("Desproteja esta cena antes de alterar a tomada ou a duração.", 409)
                clip.update(self.validate_clip(p, {**clip, **changes}))
            elif operation == "clip_move":
                clip = self.find(p["timeline"], args.get("clip_id"))
                index = args.get("index")
                if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(p["timeline"]):
                    raise EditorError("Posição inválida.")
                p["timeline"].remove(clip)
                p["timeline"].insert(index, clip)
            elif operation == "clip_remove":
                clip = self.find(p["timeline"], args.get("clip_id"))
                if clip["locked"]:
                    raise EditorError("Desproteja a cena antes de removê-la.", 409)
                p["timeline"].remove(clip)
            elif operation == "timeline_replace":
                data = args.get("clips")
                if not isinstance(data, list) or len(data) > 100:
                    raise EditorError("Envie uma lista com até 100 cenas.")
                proposed = [self.validate_clip(p, c) for c in data]
                if len({c["id"] for c in proposed}) != len(proposed):
                    raise EditorError("Cada cena precisa ter um identificador diferente.")
                for old in p["timeline"]:
                    if old["locked"] and old not in proposed:
                        raise EditorError("A nova montagem precisa preservar as cenas protegidas, incluindo seus identificadores.", 409)
                p["timeline"] = proposed
            elif operation == "narration_set":
                media_id = args.get("media_id")
                if media_id is None:
                    p["narration"] = None
                else:
                    asset = self.find(p["media"], media_id, "Arquivo")
                    if asset.get("status") != "ready" or not asset.get("has_audio"):
                        raise EditorError("Escolha um arquivo importado que contenha áudio.")
                    p["narration"] = {"media_id": media_id, "volume": number(args.get("volume", 1), 0, 2),
                                      "offset": number(args.get("offset", 0), 0, 3600)}
            elif operation == "request_add":
                p["requests"].append({"id": uid(), "text": text(args.get("text", ""), 4000),
                                      "status": "pending", "created_at": now(), "revision": p["revision"], "result": ""})
                if not p["requests"][-1]["text"]:
                    raise EditorError("Escreva o ajuste desejado.")
            elif operation == "request_complete":
                request = self.find(p["requests"], args.get("request_id"), "Pedido")
                request.update(status="done", result=text(args.get("result", ""), 4000))
            elif operation == "undo":
                if not p["history"]:
                    raise EditorError("Ainda não há alterações para desfazer.")
                p.update(p["history"].pop())
            else:
                raise EditorError("Operação desconhecida.")
            if operation not in ("undo", "media_annotate", "request_add", "request_complete"):
                p["history"] = (p["history"] + [snapshot])[-30:]
            if len(p["timeline"]) > 100 or duration(p) > 1800:
                raise EditorError("O piloto aceita até 100 cenas e 30 minutos por montagem.")
            self._touch(p, text(actor, 40), operation)
            self._write(p)
            return self.public(p)

    def draft(self, project_id, expected_revision):
        p = self.get(project_id)
        if expected_revision != p["revision"]:
            raise EditorError("O projeto mudou. Atualize antes de montar.", 409)
        if any(c["locked"] for c in p["timeline"]):
            raise EditorError("Há cenas protegidas. Use ajustes individuais ou peça ao Codex uma montagem que as preserve.", 409)
        assets = [m for m in p["media"] if m.get("status") == "ready" and m.get("kind") == "video"]
        blocks = script_blocks(p["script"])
        if not assets or not blocks:
            raise EditorError("Importe pelo menos um vídeo e escreva o roteiro.")
        clips, warnings, usage = [], [], {}
        for block in blocks:
            scored = sorted(assets, key=lambda m: (len(tokens(block["text"]) & tokens(" ".join(m.get("tags", [])) + " " + m["name"])), -usage.get(m["id"], 0)), reverse=True)
            asset = scored[0]
            score = len(tokens(block["text"]) & tokens(" ".join(asset.get("tags", [])) + " " + asset["name"]))
            if not score:
                warnings.append(f"{block['id']}: tomada sugerida sem correspondência de etiquetas; revisar.")
            length = min(asset["duration"], max(1.2, len(block["text"].split()) / 3.0))
            used = usage.get(asset["id"], 0)
            start = min(used * length, max(0, asset["duration"] - length))
            clips.append({"media_id": asset["id"], "start": start, "end": start + length,
                          "label": block["text"][:70], "block_id": block["id"], "volume": 0 if p["narration"] else 1})
            usage[asset["id"]] = used + 1
        result = self.apply(project_id, "timeline_replace", {"clips": clips}, expected_revision, "rascunho por etiquetas")
        return {"project": result, "warnings": warnings, "method": "tags_and_script_length"}
