"""Importação e exportação locais. Os arquivos originais nunca são alterados."""

import copy
import array
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .core import EditorError, duration, now, number, uid

ALLOWED = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".wav", ".mp3", ".m4a", ".aac"}


def executable():
    configured = os.environ.get("LILI_FFMPEG")
    if configured:
        return configured
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise EditorError("FFmpeg indisponível. Instale requirements.txt ou configure LILI_FFMPEG.", 503) from None


def run(args, timeout=1800):
    result = subprocess.run([executable(), "-hide_banner", "-nostdin", "-y", *map(str, args)],
                            capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        # Guardar os detalhes técnicos no log do servidor, sem caminhos locais no navegador.
        print(result.stderr[-6000:], flush=True)
        raise EditorError("Não foi possível processar este arquivo. Consulte o terminal do servidor.", 422)
    return result


def probe(path):
    p = subprocess.run([executable(), "-hide_banner", "-nostdin", "-i", str(path)], capture_output=True,
                       encoding="utf-8", errors="replace", timeout=30)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not match:
        raise EditorError("Não foi possível ler a duração. Verifique se o arquivo está completo.", 422)
    seconds = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    if seconds < 0.1:
        raise EditorError("O arquivo precisa ter pelo menos 0,1 segundo.")
    video = re.search(r"Video: ([^,\s]+).*?(\d{2,5})x(\d{2,5})", p.stderr)
    audio = "Audio:" in p.stderr
    if not video and not audio:
        raise EditorError("Este arquivo não contém vídeo ou áudio utilizável.")
    result = {"duration": seconds, "kind": "video" if video else "audio", "has_audio": audio,
              "width": int(video[2]) if video else 0, "height": int(video[3]) if video else 0,
              "codec": video[1] if video else "audio"}
    if video and re.search(r"rotation of -?90(?:\.0+)? degrees", p.stderr):
        result["width"], result["height"] = result["height"], result["width"]
    return result


class MediaService:
    def __init__(self, store):
        self.store = store
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="lili-media")
        self.jobs = {}
        self.lock = threading.RLock()
        self.export_lock = threading.Lock()
        self.jobs_file = store.root / "jobs.json"
        if self.jobs_file.exists():
            self.jobs = json.loads(self.jobs_file.read_text(encoding="utf-8"))
            for job in self.jobs.values():
                if job["status"] in ("queued", "running"):
                    job.update(status="error", error="O servidor foi reiniciado. Inicie esta operação novamente.")
            self._save_jobs()
        # Recuperação de importações interrompidas antes de salvar o trabalho.
        for summary in store.list():
            for asset in store.get(summary["id"])["media"]:
                if asset.get("status") == "processing":
                    store.update_media(summary["id"], asset["id"], {"status": "error", "error": "Importação interrompida. Importe o arquivo novamente."})

    def _save_jobs(self):
        temp = self.jobs_file.with_suffix(".tmp")
        temp.write_text(json.dumps(self.jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.jobs_file)

    def job_update(self, job_id, **changes):
        with self.lock:
            self.jobs[job_id].update(changes)
            self._save_jobs()

    def job(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise EditorError("Trabalho não encontrado.", 404)
            return copy.deepcopy(self.jobs[job_id])

    def list_jobs(self, project_id):
        with self.lock:
            return [copy.deepcopy(j) for j in self.jobs.values() if j["project_id"] == project_id]

    def submit(self, project_id, kind, function, *args):
        job_id = uid()
        job = {"id": job_id, "project_id": project_id, "kind": kind, "status": "queued",
               "progress": 0, "created_at": now(), "error": None}
        with self.lock:
            # Do not enqueue a stale snapshot after a project was trashed/purged.
            self.store.get(project_id)
            self.jobs[job_id] = job
            self._save_jobs()

        def perform():
            self.job_update(job_id, status="running")
            try:
                result = function(job_id, *args)
                self.job_update(job_id, status="done", progress=100, result=result)
            except Exception as exc:
                self.job_update(job_id, status="error", error=str(exc))

        self.pool.submit(perform)
        return self.job(job_id)

    def register(self, project_id, path, name, media_id=None):
        media_id = media_id or uid()
        asset = {"id": media_id, "name": name, "filename": Path(path).name, "status": "processing", "tags": [], "note": ""}
        self.store.add_media(project_id, asset)
        job = self.submit(project_id, "import", self._prepare, project_id, media_id)
        return {"media_id": media_id, "job": job}

    def source(self, project_id, asset):
        return self.store.folder(project_id) / "media" / asset["filename"]

    def _prepare(self, job_id, project_id, media_id):
        asset = self.store.media(project_id, media_id)
        source = self.source(project_id, asset)
        folder = source.parent
        try:
            details = probe(source)
            if details["kind"] == "video":
                thumb = f"{media_id}.jpg"
                proxy = f"{media_id}.proxy.mp4"
                run(["-i", source, "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "3", folder / thumb])
                self.job_update(job_id, progress=15)
                run(["-i", source, "-map", "0:v:0", "-map", "0:a:0?", "-vf", "scale=540:960:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", folder / proxy])
                details.update(thumbnail=thumb, proxy=proxy)
            else:
                proxy = f"{media_id}.proxy.m4a"
                run(["-i", source, "-vn", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", folder / proxy])
                details["proxy"] = proxy
            self.store.update_media(project_id, media_id, {**details, "status": "ready"})
            return {"media_id": media_id}
        except Exception as exc:
            self.store.update_media(project_id, media_id, {"status": "error", "error": str(exc)})
            raise

    def import_file(self, project_id, source):
        """Importação do próprio processo (CLI), nunca aceita caminhos enviados pela página."""
        source = Path(source).resolve()
        if source.suffix.lower() not in ALLOWED or not source.is_file():
            raise EditorError("Escolha um arquivo local de vídeo ou áudio compatível.")
        self.store.get(project_id)
        media_id = uid()
        folder = self.store.folder(project_id) / "media"
        folder.mkdir(exist_ok=True)
        target = folder / (media_id + source.suffix.lower())
        shutil.copy2(source, target)
        return self.register(project_id, target, source.name, media_id)

    def sheet(self, project_id, media_id):
        from PIL import Image, ImageDraw
        asset = self.store.media(project_id, media_id)
        if asset.get("status") != "ready" or asset.get("kind") != "video":
            raise EditorError("O vídeo ainda não está disponível.")
        folder = self.store.folder(project_id) / "media"
        output = folder / f"{media_id}.sheet.jpg"
        with self.lock:
            if not output.exists():
                step = max(0.1, asset["duration"] / 12)
                run(["-i", self.source(project_id, asset), "-vf", f"fps=1/{step},scale=180:320:force_original_aspect_ratio=decrease,pad=180:320:(ow-iw)/2:(oh-ih)/2,tile=4x3", "-frames:v", "1", output])
                with Image.open(output) as im:
                    canvas = im.convert("RGB")
                draw = ImageDraw.Draw(canvas)
                for i in range(12):
                    t = (i + 0.5) * step
                    x, y = (i % 4) * 180, (i // 4) * 320
                    draw.rectangle((x, y, x + 179, y + 19), fill="black")
                    draw.text((x + 4, y + 2), f"~{t:.1f}s", fill="white")
                canvas.save(output, quality=90)
        return output

    def frame(self, project_id, media_id, at):
        asset = self.store.media(project_id, media_id)
        if asset.get("status") != "ready" or asset.get("kind") != "video":
            raise EditorError("O vídeo ainda não está disponível.")
        at = number(at, 0, max(0, asset["duration"] - 0.04))
        output = self.store.folder(project_id) / "media" / f"{media_id}.frame-{round(at*1000)}.jpg"
        with self.lock:
            if not output.exists():
                run(["-ss", at, "-i", self.source(project_id, asset), "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "3", output])
        return output

    def waveform(self, project_id, media_id):
        asset = self.store.media(project_id, media_id)
        if asset.get("status") != "ready" or not asset.get("has_audio"):
            raise EditorError("Escolha um arquivo pronto que contenha áudio.")
        output = self.store.folder(project_id) / "media" / f"{media_id}.waveform.json"
        with self.lock:
            if output.exists():
                return json.loads(output.read_text(encoding="utf-8"))
            # Decode in small chunks so a long recording cannot fill memory.
            process = subprocess.Popen([executable(), "-hide_banner", "-loglevel", "error", "-nostdin",
                                        "-i", str(self.source(project_id, asset)), "-vn", "-ac", "1", "-ar", "8000",
                                        "-f", "s16le", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            window = max(1, int(asset["duration"] * 8000 / 2048))
            peaks = []
            try:
                while raw := process.stdout.read(window * 2):
                    samples = array.array("h", raw)
                    if sys.byteorder != "little":
                        samples.byteswap()
                    peaks.append(round(max(map(abs, samples), default=0) / 32768, 5))
                if process.wait(timeout=30):
                    raise EditorError("Não foi possível ler a forma de onda do áudio.", 422)
            finally:
                process.stdout.close()
                if process.poll() is None:
                    process.kill()
                    process.wait()
            result = {"duration": asset["duration"], "peaks": peaks}
            output.write_text(json.dumps(result), encoding="utf-8")
            return result

    def export(self, project_id, expected_revision, quality="full"):
        project = self.store.get(project_id)
        if project["revision"] != expected_revision:
            raise EditorError("O projeto mudou. Atualize antes de exportar.", 409)
        if not project["timeline"]:
            raise EditorError("Adicione cenas à montagem antes de exportar.")
        if quality not in ("full", "preview"):
            raise EditorError("Qualidade inválida.")
        with self.lock:
            if any(j["kind"] == "export" and j["status"] in ("queued", "running") for j in self.jobs.values()):
                raise EditorError("Já existe uma exportação em andamento.", 409)
            return self.submit(project_id, "export", self._render, project, quality)

    def _render(self, job_id, project, quality):
        with self.export_lock:
            project_id = project["id"]
            folder = self.store.folder(project_id) / "exports" / job_id
            folder.mkdir(parents=True, exist_ok=True)
            width, height = (540, 960) if quality == "preview" else (project["settings"]["width"], project["settings"]["height"])
            font = Path(os.environ.get("LILI_FONT", "C:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
            for index, clip in enumerate(project["timeline"]):
                asset = self.store.find(project["media"], clip["media_id"], "Arquivo")
                args = ["-ss", clip["start"], "-i", self.source(project_id, asset)]
                if not asset["has_audio"]:
                    args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                filters = f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
                if clip["title"]:
                    import textwrap
                    escape_path = lambda p: p.resolve().as_posix().replace(":", "\\:").replace("'", "'\\''")
                    lines = [line for paragraph in clip["title"].splitlines() for line in (textwrap.wrap(paragraph, 30) or [""])]
                    font_size = round(width * .044)
                    for line_index, line in enumerate(lines):
                        title_file = folder / f"title-{index:04d}-{line_index:02d}.txt"
                        title_file.write_text(line, encoding="utf-8")
                        filters += f",drawtext=fontfile='{escape_path(font)}':textfile='{escape_path(title_file)}':expansion=none:fontsize={font_size}:fontcolor=white:borderw=1:bordercolor=black@0.7:shadowcolor=black@0.5:shadowx=1:shadowy=1:x=(w-text_w)/2:y=h*0.32+{line_index*font_size*1.2}"
                if clip.get("fade_in", 0):
                    filters += f",fade=t=in:st=0:d={clip['fade_in']}"
                if clip.get("fade_out", 0):
                    filters += f",fade=t=out:st={clip['end']-clip['start']-clip['fade_out']}:d={clip['fade_out']}"
                args += ["-t", clip["end"] - clip["start"], "-map", "0:v:0", "-map", "0:a:0" if asset["has_audio"] else "1:a:0",
                         "-vf", filters, "-af", f"volume={clip['volume']},apad", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                         "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k", "-video_track_timescale", "90000", folder / f"{index:04d}.mp4"]
                run(args)
                self.job_update(job_id, progress=round((index + 1) / len(project["timeline"]) * 85))
            playlist = folder / "segments.txt"
            playlist.write_text("\n".join(f"file '{i:04d}.mp4'" for i in range(len(project["timeline"]))), encoding="utf-8")
            base = folder / "base.mp4"
            run(["-f", "concat", "-safe", "1", "-i", playlist, "-c", "copy", "-movflags", "+faststart", base])
            output = folder / "video.mp4"
            narration = project["narration"]
            if narration:
                asset = self.store.find(project["media"], narration["media_id"], "Arquivo")
                delay = round(narration["offset"] * 1000)
                voice_filters = [f"volume={narration['volume']}"]
                if narration.get("fade_in", 0):
                    voice_filters.append(f"afade=t=in:st=0:d={narration['fade_in']}")
                if narration.get("fade_out", 0):
                    voice_filters.append(f"afade=t=out:st={max(0, asset['duration'] - narration['fade_out'])}:d={narration['fade_out']}")
                voice_filters.append(f"adelay={delay}:all=1")
                voice_filter = ",".join(voice_filters)
                run(["-i", base, "-i", self.source(project_id, asset), "-filter_complex",
                     f"[1:a]{voice_filter},apad,atrim=duration={duration(project)}[voice];[0:a][voice]amix=inputs=2:duration=first:normalize=0[a]",
                     "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", output])
            else:
                base.replace(output)
            details = probe(output)
            return {"revision": project["revision"], "duration": details["duration"], "width": width, "height": height,
                    "url": f"/api/projects/{project_id}/exports/{job_id}/video.mp4", "filename": "video.mp4"}
