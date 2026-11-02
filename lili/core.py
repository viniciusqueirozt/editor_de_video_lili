"""Estado de projeto, revisões e operações independentes do motor de vídeo."""

import copy
import json
import math
import os
import re
import shutil
import stat
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
    except (TypeError, ValueError, OverflowError):
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


def clip_duration(clip):
    return (clip["end"] - clip["start"]) / clip.get("speed", 1)


def duration(project):
    return round(sum(clip_duration(c) for c in project["timeline"]), 4)


class Store:
    SNAPSHOT_FIELDS = ("name", "description", "script", "timeline", "narration", "settings", "captions", "music", "transitions", "audio_clips")

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def folder(self, project_id):
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise EditorError("Projeto não encontrado.", 404)
        return self.root / project_id

    @staticmethod
    def _decode_project(path, project_id):
        project = json.loads(path.read_text(encoding="utf-8"))
        required = {"id": str, "name": str, "description": str, "script": str,
                    "revision": int, "updated_at": str, "media": list, "timeline": list,
                    "narration": (dict, type(None)), "requests": list, "history": list,
                    "settings": dict, "last_change": dict}
        if (not isinstance(project, dict) or project.get("id") != project_id
                or any(not isinstance(project.get(k), kind) for k, kind in required.items())
                or isinstance(project["revision"], bool) or project["revision"] < 1):
            raise ValueError("Estrutura de projeto inválida")
        return project

    def _read(self, project_id):
        folder = self.folder(project_id)
        target, backup = folder / "project.json", folder / "project.json.bak"
        try:
            return self._decode_project(target, project_id)
        except (FileNotFoundError, ValueError, UnicodeError):
            missing = not target.exists()
        try:
            project = self._decode_project(backup, project_id)
        except (FileNotFoundError, ValueError, UnicodeError):
            if missing and not backup.exists():
                raise EditorError("Projeto não encontrado.", 404) from None
            raise EditorError("O projeto está ilegível e não há uma cópia de segurança válida. Os arquivos de mídia foram preservados.", 422) from None
        project["recovery_notice"] = (
            "Projeto aberto pela cópia de segurança. Confira os últimos ajustes antes de continuar; "
            "a cópia pode estar uma gravação atrás se o salvamento foi interrompido. "
            "Uma nova alteração salva o estado recuperado.")
        return project

    @staticmethod
    def _atomic_save(path, payload):
        temp = path.with_name(path.name + ".tmp")
        try:
            with temp.open("w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)

    def _write(self, project):
        folder = self.folder(project["id"])
        folder.mkdir(parents=True, exist_ok=True)
        project.pop("recovery_notice", None)
        payload = json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False)
        self._atomic_save(folder / "project.json", payload)
        # The mirror contains the latest complete save, including imported media.
        # A crash before this second replacement leaves the previous valid mirror.
        self._atomic_save(folder / "project.json.bak", payload)

    @staticmethod
    def public(project):
        result = copy.deepcopy(project)
        result.setdefault("captions", [])
        result.setdefault("music", None)
        result.setdefault("audio_clips", [])
        from .transitions import clean_transitions
        result["transitions"] = clean_transitions(result)
        result.pop("access", None)  # Sharing metadata has a separate owner-only API.
        result["undo_available"] = bool(result.pop("history", []))
        result["redo_available"] = bool(result.pop("future", []))
        result["duration"] = duration(result)
        result["blocks"] = script_blocks(result["script"])
        result["trash"] = [m for m in result["media"] if m.get("deleted_at")]
        result["media"] = [m for m in result["media"] if not m.get("deleted_at")]
        return result

    def get(self, project_id):
        with self.lock:
            p = self._read(project_id)
            if p.get("deleted_at"):
                raise EditorError("Projeto na Lixeira. Restaure pela página inicial.", 404)
            return self.public(p)

    def list(self, trash=False):
        with self.lock:
            result = []
            folders = {p.parent for pattern in ("*/project.json", "*/project.json.bak") for p in self.root.glob(pattern)}
            for folder in folders:
                p = self._read(folder.name)
                if bool(p.get("deleted_at")) != trash:
                    continue
                item = {k: p[k] for k in ("id", "name", "revision", "updated_at", "description")}
                active = [m for m in p["media"] if not m.get("deleted_at")]
                item.update(media_count=len(active), duration=duration(p),
                            thumbnail_id=next((m["id"] for m in active if m.get("kind")=="video" and m.get("status")=="ready"), None))
                result.append(item)
            return sorted(result, key=lambda p: p["updated_at"], reverse=True)

    def project_trash(self, project_id, expected_revision, restore=False):
        with self.lock:
            p = self._read(project_id)
            if isinstance(expected_revision, bool) or expected_revision != p["revision"]:
                raise EditorError("O projeto mudou. Atualize e confirme novamente.", 409)
            if bool(p.get("deleted_at")) == (not restore):
                raise EditorError("O estado do projeto mudou. Atualize a lista.", 409)
            if not restore and any(m.get("status") not in ("ready", "error") for m in p["media"]):
                raise EditorError("Aguarde a preparação dos arquivos antes de excluir o projeto.", 409)
            if restore:
                p.pop("deleted_at", None)
            else:
                p["deleted_at"] = now()
            self._touch(p, "editor", "project_restore" if restore else "project_remove")
            self._write(p)
            return {"id": p["id"], "revision": p["revision"]}

    def purge_project(self, project_id, expected_revision, confirmation):
        """Remove only an explicitly confirmed, trashed project inside this store."""
        with self.lock:
            folder = self.folder(project_id)
            if folder.parent != self.root or folder.resolve().parent != self.root:
                raise EditorError("Caminho do projeto inseguro. Nenhum arquivo foi excluído.", 409)
            # Refuse symlinks, junctions and other reparse points before reading
            # project metadata or recursively deleting anything.
            def inventory(path):
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                    raise EditorError("O projeto contém links de arquivos. A exclusão foi bloqueada para proteger outros locais.", 409)
                if stat.S_ISDIR(info.st_mode):
                    return sum(inventory(child) for child in path.iterdir())
                return info.st_size
            try:
                size = inventory(folder)
            except OSError:
                raise EditorError("Não foi possível verificar os arquivos do projeto. Atualize a Lixeira.", 409) from None
            p = self._read(project_id)
            if not p.get("deleted_at"):
                raise EditorError("Mova o projeto para a Lixeira antes de excluir permanentemente.", 409)
            if isinstance(expected_revision, bool) or expected_revision != p["revision"]:
                raise EditorError("O projeto mudou. Atualize e confirme novamente.", 409)
            if confirmation != "EXCLUIR":
                raise EditorError("Digite EXCLUIR para confirmar a exclusão permanente.")
            try:
                shutil.rmtree(folder)
            except OSError:
                raise EditorError("Não foi possível remover todos os arquivos. Feche os arquivos abertos e atualize a Lixeira; a exclusão pode ter sido parcial.", 409) from None
            return {"id": project_id, "removed_bytes": size, "permanent": True}

    def create(self, name, script="", description="", *, owner_id=None):
        with self.lock:
            p = {"id": uid(), "name": text(name, 120) or "Novo projeto", "script": text(script),
                 "description": text(description, 1000), "revision": 1, "updated_at": now(),
                 "media": [], "timeline": [], "narration": None, "requests": [], "history": [],
                 "settings": {"width": 1080, "height": 1920, "fps": 30},
                 "last_change": {"actor": "editor", "operation": "create"}}
            if owner_id is not None:
                from .access import valid_subject
                if not valid_subject(owner_id):raise EditorError("Proprietário inválido.")
                p["access"] = {"owner_id": owner_id, "grants": {}}
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
        if asset.get("deleted_at") or asset.get("status") != "ready" or asset.get("kind") != "video":
            raise EditorError("Escolha um vídeo que já terminou de importar.")
        start = number(data.get("start", 0), 0, asset["duration"])
        end = number(data.get("end", asset["duration"]), 0, asset["duration"])
        speed = number(data.get("speed", 1), .25, 4)
        length = (end-start) / speed
        if round(length, 4) < 0.1:
            raise EditorError("A cena precisa ter pelo menos 0,1 segundo.")
        clip_id = data.get("id", uid())
        if not isinstance(clip_id, str) or not re.fullmatch(r"[a-f0-9]{32}", clip_id):
            raise EditorError("Identificador de cena inválido.")
        if not isinstance(data.get("locked", False), bool):
            raise EditorError("A proteção de cena deve ser verdadeira ou falsa.")
        framing = data.get("framing", "contain")
        if framing not in ("contain", "cover") or not isinstance(data.get("mirror", False), bool):
            raise EditorError("Enquadramento inválido.")
        pan_x = number(data.get("pan_x", .5), 0, 1)
        pan_y = number(data.get("pan_y", .5), 0, 1)
        title_style = {}
        for key, choices, default in (("title_font", ("sans", "serif", "mono"), "sans"),
                                       ("title_size", ("small", "medium", "large"), "medium"),
                                       ("title_position", ("legacy", "top", "center", "bottom"), "legacy")):
            value = data.get(key, default)
            if value not in choices: raise EditorError("Estilo de texto inválido.")
            title_style[key] = value
        fade_in = number(data.get("fade_in", 0), 0, length)
        fade_out = number(data.get("fade_out", 0), 0, length)
        if fade_in + fade_out > length + 0.00001:
            raise EditorError("As entradas e saídas suaves não podem ultrapassar a duração da cena.")
        audio_fade_in = number(data.get("audio_fade_in", 0), 0, length)
        audio_fade_out = number(data.get("audio_fade_out", 0), 0, length)
        if audio_fade_in + audio_fade_out > length + .00001:
            raise EditorError("Os fades de áudio não podem ultrapassar a duração da cena.")
        if not isinstance(data.get("audio_detached",False),bool):raise EditorError("Separação de áudio inválida.")
        return {**({"audio_detached":True} if data.get("audio_detached") else {}), "id": clip_id, "media_id": asset["id"], "start": start, "end": end,
                "fade_in": fade_in, "fade_out": fade_out, "speed": speed, **title_style,
                "audio_fade_in": audio_fade_in, "audio_fade_out": audio_fade_out,
                "framing": framing, "mirror": data.get("mirror", False), "pan_x": pan_x, "pan_y": pan_y,
                "brightness": number(data.get("brightness", 1), .5, 1.5),
                "contrast": number(data.get("contrast", 1), .5, 1.5),
                "saturation": number(data.get("saturation", 1), 0, 2),
                "label": text(data.get("label", asset["name"]), 160), "title": text(data.get("title", ""), 160),
                "volume": number(data.get("volume", 1), 0, 2), "locked": data.get("locked", False),
                "block_id": text(data.get("block_id", ""), 80)}

    def apply(self, project_id, operation, args, expected_revision, actor="editor"):
        if not isinstance(args, dict):
            raise EditorError("Os argumentos devem ser um objeto.")
        with self.lock:
            p = self._read(project_id)
            if p.get("deleted_at"):
                raise EditorError("Restaure o projeto antes de editar.", 404)
            if isinstance(expected_revision, bool) or expected_revision != p["revision"]:
                raise EditorError("O projeto mudou. Atualize a página ou leia a revisão atual antes de editar.", 409)
            p.setdefault("captions", [])
            p.setdefault("music", None)
            p.setdefault("future", [])
            p.setdefault("transitions", [])
            p.setdefault("audio_clips", [])
            snapshot = {k: copy.deepcopy(p[k]) for k in self.SNAPSHOT_FIELDS}
            snapshot["media_visibility"] = {m["id"]: m.get("deleted_at") for m in p["media"]}
            if operation == "script_update":
                p["script"] = text(args.get("script", p["script"]))
                p["name"] = text(args.get("name", p["name"]), 120) or p["name"]
                p["description"] = text(args.get("description", p["description"]), 1000)
            elif operation in ("caption_add", "caption_update", "caption_remove", "captions_replace", "captions_import"):
                from .subtitles import parse_srt, validate_captions
                if operation == "captions_import":
                    p["captions"] = parse_srt(args.get("srt"))
                elif operation == "captions_replace":
                    p["captions"] = validate_captions(args.get("captions"))
                elif operation == "caption_add":
                    p["captions"] = validate_captions(p["captions"] + [args])
                else:
                    caption = self.find(p["captions"], args.get("caption_id"), "Legenda")
                    if operation == "caption_remove":p["captions"].remove(caption)
                    else:
                        changes = {k:v for k,v in args.items() if k not in ("caption_id", "id")}
                        caption.update(changes)
                        p["captions"] = validate_captions(p["captions"])
            elif operation == "settings_update":
                from .profiles import FORMATS
                selected_format = args.get("format")
                if not isinstance(selected_format, str) or selected_format not in FORMATS:
                    raise EditorError("Escolha um formato de vídeo válido.")
                p["settings"].update(zip(("width", "height"), FORMATS[selected_format]))
            elif operation == "watermark_set":
                value = args.get("text", "")
                if not isinstance(value, str) or len(value) > 40:
                    raise EditorError("Use até 40 caracteres na marca d'água.")
                position = args.get("position", "bottom_right")
                if position not in ("top_left", "top_right", "bottom_left", "bottom_right"):
                    raise EditorError("Posição da marca d'água inválida.")
                opacity = number(args.get("opacity", .6), .1, 1)
                value = " ".join(value.split())
                p["settings"]["watermark"] = {"text": value, "position": position, "opacity": opacity} if value else None
            elif operation == "media_annotate":
                asset = self.find(p["media"], args.get("media_id"), "Arquivo")
                if asset.get("deleted_at"):
                    raise EditorError("Restaure o arquivo da Lixeira antes de editar.", 409)
                tags = args.get("tags", asset.get("tags", []))
                if not isinstance(tags, list) or len(tags) > 40:
                    raise EditorError("Use até 40 etiquetas.")
                asset["tags"] = [text(t, 80) for t in tags if text(t, 80)]
                asset["note"] = text(args.get("note", asset.get("note", "")), 2000)
            elif operation in ("media_remove", "media_remove_many"):
                ids = args.get("media_ids") if operation == "media_remove_many" else [args.get("media_id")]
                if (not isinstance(ids, list) or not 1 <= len(ids) <= 1000
                        or any(not isinstance(i, str) for i in ids) or len(set(ids)) != len(ids)):
                    raise EditorError("Selecione de 1 a 1000 arquivos diferentes.")
                assets = [self.find(p["media"], i, "Arquivo") for i in ids]
                if any(a.get("deleted_at") for a in assets):
                    raise EditorError("Há arquivos que já estão na Lixeira.", 409)
                if any(a.get("status") not in ("ready", "error") for a in assets):
                    raise EditorError("Aguarde a importação terminar antes de excluir.", 409)
                clips = [c for c in p["timeline"] if c["media_id"] in ids]
                narration = p["narration"] and p["narration"]["media_id"] in ids
                music = p["music"] and p["music"]["media_id"] in ids
                audio_clips=[a for a in p["audio_clips"] if a["media_id"] in ids]
                if any(a["locked"] for a in audio_clips):raise EditorError("Desproteja os áudios deste arquivo antes de excluir.",409)
                if any(c["locked"] for c in clips):
                    raise EditorError("Desproteja as cenas deste arquivo antes de excluir.", 409)
                if (clips or narration or music or audio_clips) and args.get("remove_usage") is not True:
                    raise EditorError("Confirme também a remoção das cenas e faixas de áudio que usam este arquivo.", 409)
                p["timeline"] = [c for c in p["timeline"] if c["media_id"] not in ids]
                p["audio_clips"] = [a for a in p["audio_clips"] if a["media_id"] not in ids]
                if narration:
                    p["narration"] = None
                if music:
                    p["music"] = None
                stamp = now()
                for asset in assets:
                    asset["deleted_at"] = stamp
            elif operation == "media_restore":
                asset = self.find(p["media"], args.get("media_id"), "Arquivo")
                if not asset.get("deleted_at"):
                    raise EditorError("O arquivo não está na Lixeira.", 409)
                asset.pop("deleted_at")
            elif operation == "transition_set" and args.get("all") is True:
                from .transitions import apply_style
                apply_style(p, args)
            elif operation == "transition_set":
                from .transitions import KINDS
                left = self.find(p["timeline"], args.get("left"))
                right = self.find(p["timeline"], args.get("right"))
                at = p["timeline"].index(left)
                if at + 1 >= len(p["timeline"]) or p["timeline"][at + 1]["id"] != right["id"]:
                    raise EditorError("Escolha duas cenas vizinhas para a transição.", 409)
                if left["locked"] or right["locked"]:
                    raise EditorError("Desproteja as duas cenas antes de alterar a transição.", 409)
                kind = args.get("kind")
                if not isinstance(kind, str) or kind not in KINDS | {"none"}:
                    raise EditorError("Escolha uma transição disponível no catálogo.")
                value = number(args.get("duration", .5), .1, min(3, clip_duration(left), clip_duration(right))) if kind != "none" else 0
                p["transitions"] = [t for t in p["transitions"] if (t["left"], t["right"]) != (left["id"], right["id"])]
                if kind != "none":
                    p["transitions"].append({"left":left["id"], "right":right["id"], "kind":kind, "duration":value})
            elif operation in ("audio_detach","audio_clip_add","audio_clip_update","audio_clip_remove","audio_clip_split","audio_clip_duplicate"):
                from .source_audio import apply_audio_operation
                apply_audio_operation(self,p,operation,args)
            elif operation == "clip_add":
                clip=self.validate_clip(p,args);p["timeline"].append(clip)
                if args.get("separate_audio") is True:
                    from .source_audio import separate_new
                    separate_new(self,p,{clip["id"]})
            elif operation == "clip_update":
                clip = self.find(p["timeline"], args.get("clip_id"))
                changes = {k: v for k, v in args.items() if k not in ("clip_id", "id")}
                if "audio_detached" in changes and changes["audio_detached"]!=clip.get("audio_detached",False):raise EditorError("Use a separação de áudio para alterar a ligação com a cena.")
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
            elif operation == "clip_split":
                clip = self.find(p["timeline"], args.get("clip_id"))
                if clip["locked"]:
                    raise EditorError("Desproteja esta cena antes de dividir.", 409)
                at = number(args.get("at"), clip["start"], clip["end"])
                if min(round((at - clip["start"])/clip.get("speed",1), 4), round((clip["end"] - at)/clip.get("speed",1), 4)) < 0.1:
                    raise EditorError("Deixe pelo menos 0,1 segundo de cada lado do corte.")
                left = self.validate_clip(p, {**clip, "end": at, "fade_out": 0, "audio_fade_out": 0})
                right = self.validate_clip(p, {**clip, "id": uid(), "start": at, "fade_in": 0, "audio_fade_in": 0})
                clip.update(left)
                p["timeline"].insert(p["timeline"].index(clip) + 1, right)
            elif operation == "clip_remove":
                clip = self.find(p["timeline"], args.get("clip_id"))
                if clip["locked"]:
                    raise EditorError("Desproteja a cena antes de removê-la.", 409)
                p["timeline"].remove(clip)
            elif operation == "clip_duplicate":
                clip = self.find(p["timeline"], args.get("clip_id"))
                duplicate = self.validate_clip(p, {**clip, "id": uid(), "locked": False})
                p["timeline"].insert(p["timeline"].index(clip) + 1, duplicate)
            elif operation == "timeline_replace":
                data = args.get("clips")
                if not isinstance(data, list) or len(data) > 100:
                    raise EditorError("Envie uma lista com até 100 cenas.")
                proposed = [self.validate_clip(p, c) for c in data]
                if len({c["id"] for c in proposed}) != len(proposed):
                    raise EditorError("Cada cena precisa ter um identificador diferente.")
                for old in p["timeline"]:
                    replacement=next((c for c in proposed if c["id"]==old["id"]),None)
                    if replacement and replacement.get("audio_detached",False)!=old.get("audio_detached",False):
                        raise EditorError("Mantenha a separação de áudio das cenas existentes.",409)
                    if old["locked"] and self.validate_clip(p, old) not in proposed:
                        raise EditorError("A nova montagem precisa preservar as cenas protegidas, incluindo seus identificadores.", 409)
                old_ids={c["id"] for c in p["timeline"]}
                p["timeline"] = proposed
                if args.get("separate_audio") is True:
                    from .source_audio import separate_new
                    separate_new(self,p,{c["id"] for c in proposed}-old_ids)
                if args.get("original_audio") == "mute":
                    for sound in p["audio_clips"]:
                        if sound.get("source_clip_id") and not sound["locked"]:sound["volume"]=0
                elif args.get("original_audio","keep")!="keep":raise EditorError("Ajuste do som original inválido.")
                if "transition_style" in args:
                    from .transitions import apply_style
                    apply_style(p, args["transition_style"])
            elif operation == "music_set":
                media_id = args.get("media_id", (p["music"] or {}).get("media_id"))
                if media_id is None:
                    p["music"] = None
                else:
                    asset = self.find(p["media"], media_id, "Arquivo")
                    if asset.get("deleted_at") or asset.get("status") != "ready" or not asset.get("has_audio"):
                        raise EditorError("Escolha um arquivo pronto que contenha áudio.")
                    values = {**(p["music"] if p["music"] and p["music"]["media_id"] == media_id else {}), **args}
                    start = number(values.get("start", 0), 0, asset["duration"])
                    end = number(values.get("end", asset["duration"]), start, asset["duration"])
                    length = round(end - start, 4)
                    if length < .1:
                        raise EditorError("Deixe pelo menos 0,1 segundo de música.")
                    fade_in = number(values.get("fade_in", 0), 0, length)
                    fade_out = number(values.get("fade_out", 0), 0, length)
                    duck = values.get("duck", True)
                    if not isinstance(duck, bool) or fade_in + fade_out > length:
                        raise EditorError("Confira a redução de volume e a duração dos fades da música.")
                    p["music"] = {"media_id": media_id, "start": start, "end": end,
                                  "offset": number(values.get("offset", 0), 0, 1800),
                                  "volume": number(values.get("volume", .2), 0, 1),
                                  "fade_in": fade_in, "fade_out": fade_out, "duck": duck}
            elif operation == "narration_set":
                media_id = args.get("media_id", (p["narration"] or {}).get("media_id"))
                if media_id is None:
                    p["narration"] = None
                else:
                    asset = self.find(p["media"], media_id, "Arquivo")
                    if asset.get("deleted_at") or asset.get("status") != "ready" or not asset.get("has_audio"):
                        raise EditorError("Escolha um arquivo importado que contenha áudio.")
                    values = {**(p["narration"] if p["narration"] and p["narration"]["media_id"] == media_id else {}), **args}
                    start = number(values.get("start", 0), 0, asset["duration"])
                    end = number(values.get("end", asset["duration"]), start, asset["duration"])
                    length = round(end - start, 4)
                    if length < .1:
                        raise EditorError("Deixe pelo menos 0,1 segundo de narração.")
                    fade_in = number(values.get("fade_in", 0), 0, length)
                    fade_out = number(values.get("fade_out", 0), 0, length)
                    if fade_in + fade_out > length + .000001:
                        raise EditorError("As suavizações juntas não podem ultrapassar a duração do trecho de narração.")
                    p["narration"] = {"media_id": media_id, "start": start, "end": end, "volume": number(values.get("volume", 1), 0, 2),
                                      "offset": number(values.get("offset", 0), 0, 3600),
                                      "fade_in": fade_in, "fade_out": fade_out}
            elif operation == "request_add":
                p["requests"].append({"id": uid(), "text": text(args.get("text", ""), 4000),
                                      "status": "pending", "created_at": now(), "revision": p["revision"], "result": ""})
                if not p["requests"][-1]["text"]:
                    raise EditorError("Escreva o ajuste desejado.")
            elif operation == "request_complete":
                request = self.find(p["requests"], args.get("request_id"), "Pedido")
                request.update(status="done", result=text(args.get("result", ""), 4000))
            elif operation in ("undo", "redo"):
                source = p["history"] if operation == "undo" else p["future"]
                target = p["future"] if operation == "undo" else p["history"]
                if not source:
                    raise EditorError("Ainda não há alterações para desfazer." if operation == "undo" else "Não há alterações para refazer.")
                previous = source.pop()
                target.append(snapshot)
                del target[:-30]
                visibility = previous.pop("media_visibility", {})
                for asset in p["media"]:
                    if asset["id"] in visibility:
                        if visibility[asset["id"]]:
                            asset["deleted_at"] = visibility[asset["id"]]
                        else:
                            asset.pop("deleted_at", None)
                p["transitions"] = previous.get("transitions", [])
                p["audio_clips"] = previous.get("audio_clips", [])
                p.update(previous)
            else:
                raise EditorError("Operação desconhecida.")
            if operation not in ("undo", "redo", "media_annotate", "request_add", "request_complete"):
                p["history"] = (p["history"] + [snapshot])[-30:]
                p["future"] = []
            if len(p["audio_clips"])>200:raise EditorError("Use até 200 blocos de áudio independente.")
            if len({a["id"] for a in p["audio_clips"]})!=len(p["audio_clips"]):raise EditorError("Cada áudio precisa ter um identificador diferente.")
            if len(p["timeline"]) > 100 or duration(p) > 1800:
                raise EditorError("O piloto aceita até 100 cenas e 30 minutos por montagem.")
            from .transitions import clean_transitions
            p["transitions"] = clean_transitions(p)
            if operation not in ("undo", "redo"):
                protected = {c["id"] for c in snapshot["timeline"] if c.get("locked")}
                current_pairs = {(t["left"], t["right"]):t for t in p["transitions"]}
                for old in snapshot["transitions"]:
                    pair = (old["left"], old["right"])
                    if protected.intersection(pair) and current_pairs.get(pair) != old:
                        raise EditorError("Desproteja as cenas da junção antes de remover ou encurtar sua transição.", 409)
            self._touch(p, text(actor, 160), operation)
            self._write(p)
            return self.public(p)

    def draft(self, project_id, expected_revision, separate_audio=False):
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
        if separate_audio and p.get("audio_clips"):
            for clip in clips:clip["audio_detached"]=True
        result = self.apply(project_id, "timeline_replace", {"clips": clips,"separate_audio":separate_audio is True}, expected_revision, "rascunho por etiquetas")
        return {"project": result, "warnings": warnings, "method": "tags_and_script_length"}
