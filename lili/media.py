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
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .text_render import text_filters, escape_path
from .profiles import render_profile
from .visuals import color_filter, tempo_filters
from .stills import IMAGE_SUFFIXES, prepare_still
from .delivery import export_name, job_delivery
from .core import EditorError, clip_duration, duration, now, number, uid

ALLOWED = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".wav", ".mp3", ".m4a", ".aac"} | IMAGE_SUFFIXES


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
        # Windows can temporarily deny replacement while another reader/scanner
        # has the destination open. Keep the old complete file until it succeeds.
        for attempt in range(5):
            try:
                temp.replace(self.jobs_file)
                break
            except PermissionError:
                if attempt == 4:raise
                time.sleep(.01 * 2**attempt)

    def job_update(self, job_id, **changes):
        with self.lock:
            self.jobs[job_id].update(changes)
            self._save_jobs()

    def job(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise EditorError("Trabalho não encontrado.", 404)
            job=copy.deepcopy(self.jobs[job_id])
        return job_delivery(job,self.store)

    def list_jobs(self, project_id):
        with self.lock:
            jobs=[copy.deepcopy(j) for j in self.jobs.values() if j["project_id"] == project_id]
        return [job_delivery(job,self.store) for job in jobs]

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

    def visual_source(self, project_id, asset):
        if asset.get("is_still"):
            return self.store.folder(project_id) / "media" / asset["still"]
        return self.source(project_id, asset)

    def _prepare(self, job_id, project_id, media_id):
        asset = self.store.media(project_id, media_id)
        source = self.source(project_id, asset)
        folder = source.parent
        try:
            details = (prepare_still(source, folder / f"{media_id}.still.png")
                       if source.suffix.lower() in IMAGE_SUFFIXES else probe(source))
            if details["kind"] == "video":
                thumb = f"{media_id}.thumb.jpg"
                proxy = f"{media_id}.proxy.mp4"
                visual_source = folder / details["still"] if details.get("is_still") else source
                run(["-i", visual_source, "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "3", folder / thumb])
                self.job_update(job_id, progress=15)
                still_args = ["-loop", "1", "-framerate", "30"] if details.get("is_still") else []
                duration_args = ["-t", details["duration"]] if still_args else []
                run([*still_args, "-i", visual_source, *duration_args, "-map", "0:v:0", "-map", "0:a:0?", "-vf", "scale=540:960:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
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
            raise EditorError("Escolha um vídeo, áudio ou foto JPG/PNG/WebP compatível.")
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
                source = folder / asset["proxy"] if asset.get("is_still") else self.source(project_id, asset)
                run(["-i", source, "-vf", f"fps=1/{step},scale=180:320:force_original_aspect_ratio=decrease,pad=180:320:(ow-iw)/2:(oh-ih)/2,tile=4x3", "-frames:v", "1", output])
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
                seek_args = [] if asset.get("is_still") else ["-ss", at]
                run([*seek_args, "-i", self.visual_source(project_id, asset), "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "3", output])
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
        render_profile(project["settings"], quality)
        # Reject unavailable sources before reserving the single export worker.
        used = {clip["media_id"] for clip in project["timeline"]}
        used.update(track["media_id"] for track in (project.get("narration"), project.get("music")) if track)
        used.update(a["media_id"] for a in project.get("audio_clips",[]))
        assets = {asset["id"]: asset for asset in project["media"]}
        for media_id in used:
            asset = assets.get(media_id)
            if not asset or asset.get("deleted_at") or asset.get("status") != "ready":
                raise EditorError("Um arquivo usado na montagem ainda não está pronto ou foi removido. Confira a biblioteca antes de exportar.", 409)
            if not self.source(project_id, asset).is_file() or (asset.get("is_still") and not self.visual_source(project_id, asset).is_file()):
                raise EditorError("Um arquivo usado na montagem não foi encontrado no armazenamento local. Restaure o arquivo ou ajuste a montagem antes de exportar.", 409)
        with self.lock:
            if any(j["kind"] in ("export", "transition_preview") and j["status"] in ("queued", "running") for j in self.jobs.values()):
                raise EditorError("Já existe uma exportação em andamento.", 409)
            return self.submit(project_id, "export", self._render, project, quality)

    def transition_preview(self, project_id, expected_revision, values):
        project = self.store.get(project_id)
        if project["revision"] != expected_revision:
            raise EditorError("O projeto mudou. Reabra a transição.", 409)
        # Store.apply on a copy is unnecessary: validate the explicit adjacent pair.
        from .transitions import KINDS
        from .core import number
        left = self.store.find(project["timeline"], values.get("left"))
        right = self.store.find(project["timeline"], values.get("right"))
        at = project["timeline"].index(left)
        if at+1 >= len(project["timeline"]) or project["timeline"][at+1]["id"] != right["id"]:
            raise EditorError("Escolha duas cenas vizinhas.", 409)
        kind = values.get("kind")
        if not isinstance(kind,str) or kind not in KINDS | {"none"}:raise EditorError("Transição inválida.")
        value = number(values.get("duration", .5), .1, min(3,clip_duration(left),clip_duration(right)))
        project["timeline"] = [left, right]
        # Cropping a clip with an existing fade would restart/move that envelope.
        # Keep that pair intact and seek near the join in the rendered preview.
        fades = ("fade_in","fade_out","audio_fade_in","audio_fade_out")
        if not any(c.get(k,0) for c in (left,right) for k in fades):
            left["start"] = max(left["start"],left["end"]-max(value,1.5)*left.get("speed",1))
            right["end"] = min(right["end"],right["start"]+max(value,1.5)*right.get("speed",1))
        project["preview_seek"] = max(0,clip_duration(left)-max(value,1.5))
        project["preview_stop"] = clip_duration(left)+min(clip_duration(right),max(value,1.5))
        project.update(narration=None,music=None,captions=[],audio_clips=[],transitions=[] if kind=="none" else [{"left":left["id"],"right":right["id"],"kind":kind,"duration":value}])
        with self.lock:
            if any(j["kind"] in ("export","transition_preview") and j["status"] in ("queued","running") for j in self.jobs.values()):
                raise EditorError("Aguarde a prévia/exportação em andamento.",409)
            return self.submit(project_id,"transition_preview",self._render,project,"preview")

    def _render(self, job_id, project, quality):
        with self.export_lock:
            self.job_update(job_id,source_revision=project["revision"],quality=quality)
            project_id = project["id"]
            folder = self.store.folder(project_id) / "exports" / job_id
            folder.mkdir(parents=True, exist_ok=True)
            profile = render_profile(project["settings"], quality)
            width, height = profile["width"], profile["height"]
            font = Path(os.environ.get("LILI_FONT", "C:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
            watermark = project["settings"].get("watermark")
            if watermark:
                watermark_file = folder / "watermark.txt"
                watermark_file.write_text(watermark["text"], encoding="utf-8")
            timeline_offset = 0
            for index, clip in enumerate(project["timeline"]):
                asset = self.store.find(project["media"], clip["media_id"], "Arquivo")
                args = (["-loop", "1", "-framerate", "30", "-i", self.visual_source(project_id, asset)]
                        if asset.get("is_still") else ["-ss", clip["start"], "-i", self.source(project_id, asset)])
                if not asset["has_audio"]:
                    args += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
                speed = clip.get("speed", 1)
                raw_duration = clip["end"] - clip["start"]
                output_duration = clip_duration(clip)
                pan_x, pan_y = clip.get("pan_x", .5), clip.get("pan_y", .5)
                if clip.get("framing", "contain") == "cover":
                    filters = f"scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2,crop={width}:{height}:(iw-ow)*{pan_x}:(ih-oh)*{pan_y}"
                else:
                    filters = f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)*{pan_x}:(oh-ih)*{pan_y}"
                filters = f"trim=duration={raw_duration},setpts=(PTS-STARTPTS)/{speed}," + filters
                filters += ",setsar=1,fps=30"
                if clip.get("mirror", False): filters += ",hflip"
                grading = color_filter(clip)
                if grading: filters += "," + grading
                if clip["title"]:
                    filters += text_filters(clip, folder, f"title-{index:04d}", width, height, font)
                if clip.get("fade_in", 0):
                    filters += f",fade=t=in:st=0:d={clip['fade_in']}"
                if clip.get("fade_out", 0):
                    filters += f",fade=t=out:st={output_duration-clip['fade_out']}:d={clip['fade_out']}"
                from .transitions import clip_transition_filters
                transition_filters = clip_transition_filters(project, index)
                if transition_filters: filters += "," + transition_filters
                for caption in project.get("captions", []):
                    start = max(0, caption["start"]-timeline_offset)
                    end = min(output_duration, caption["end"]-timeline_offset)
                    if end > start:
                        filters += text_filters(caption, folder, f"subtitle-{index:04d}-{caption['id']}", width, height, font, f"gte(t,{start})*lt(t,{end})")
                if watermark:
                    right = watermark["position"].endswith("right")
                    bottom = watermark["position"].startswith("bottom")
                    mark_x = "w-text_w-w*0.04" if right else "w*0.04"
                    mark_y = "h-text_h-h*0.04" if bottom else "h*0.04"
                    filters += f",drawtext=fontfile='{escape_path(font)}':textfile='{escape_path(watermark_file)}':expansion=none:fontsize={max(8, round(width*.025))}:fontcolor=white@{watermark['opacity']}:shadowcolor=black@0.5:shadowx=1:shadowy=1:x={mark_x}:y={mark_y}"
                audio_filters = [f"atrim=duration={raw_duration}", "asetpts=PTS-STARTPTS", *tempo_filters(speed), f"volume={0 if clip.get('audio_detached') else clip['volume']}"]
                if clip.get("audio_fade_in", 0):
                    audio_filters.append(f"afade=t=in:st=0:d={clip['audio_fade_in']}")
                if clip.get("audio_fade_out", 0):
                    audio_filters.append(f"afade=t=out:st={output_duration-clip['audio_fade_out']}:d={clip['audio_fade_out']}")
                audio_filters += ["apad", "alimiter=limit=0.95:level=0:latency=1"]
                args += ["-t", output_duration, "-map", "0:v:0", "-map", "0:a:0" if asset["has_audio"] else "1:a:0",
                         "-vf", filters, "-af", ",".join(audio_filters), "-c:v", "libx264", "-preset", "veryfast", "-crf", str(profile["crf"]),
                         "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "160k", "-video_track_timescale", "90000", folder / f"{index:04d}.mp4"]
                run(args)
                timeline_offset += output_duration
                self.job_update(job_id, progress=round((index + 1) / len(project["timeline"]) * 85))
            playlist = folder / "segments.txt"
            playlist.write_text("\n".join(f"file '{i:04d}.mp4'" for i in range(len(project["timeline"]))), encoding="utf-8")
            base = folder / "base.mp4"
            run(["-f", "concat", "-safe", "1", "-i", playlist, "-c", "copy", "-movflags", "+faststart", base])
            from .transitions import dissolve_graph
            graph = dissolve_graph(project)
            if graph:
                self.job_update(job_id, stage="Compondo transições entre cenas", progress=88)
                blended = folder / "blended.mp4"
                blend_inputs = ["-i", base]
                for i in range(len(project["timeline"])):blend_inputs += ["-i", folder / f"{i:04d}.mp4"]
                run([*blend_inputs,"-filter_complex_threads","1","-filter_complex",graph,
                     "-map","[blended]","-map","0:a:0","-c:v","libx264","-preset","veryfast","-crf",profile["crf"],
                     "-c:a","copy","-t",duration(project),"-movflags","+faststart",blended])
                base = blended
            output = folder / "video.mp4"
            narration = project["narration"]
            music = project.get("music")
            inputs, filters, labels = ["-i", base], [], ["[0:a]"]
            if narration:
                asset = self.store.find(project["media"], narration["media_id"], "Arquivo")
                delay = round(narration["offset"] * 1000)
                voice_start = narration.get("start", 0)
                voice_end = narration.get("end", asset["duration"])
                voice_length = voice_end - voice_start
                voice_filters = [f"atrim=start={voice_start}:end={voice_end}", "asetpts=PTS-STARTPTS", f"volume={narration['volume']}"]
                if narration.get("fade_in", 0):
                    voice_filters.append(f"afade=t=in:st=0:d={narration['fade_in']}")
                if narration.get("fade_out", 0):
                    voice_filters.append(f"afade=t=out:st={max(0, voice_length - narration['fade_out'])}:d={narration['fade_out']}")
                # Count the inserted silence too, so mixing retains the requested offset.
                voice_filters.extend([f"adelay={delay}:all=1", "asetpts=N/SR/TB"])
                voice_filter = ",".join(voice_filters)
                inputs += ["-i", self.source(project_id, asset)]
                filters.append(f"[1:a]{voice_filter},apad,atrim=duration={duration(project)}[voice]")
                labels.append("[voice]")
            if music:
                asset = self.store.find(project["media"], music["media_id"], "Arquivo")
                source_index = len(inputs)//2
                inputs += ["-i", self.source(project_id, asset)]
                gain = str(music["volume"])
                if narration and music.get("duck", True):
                    voice_asset = self.store.find(project["media"], narration["media_id"], "Arquivo")
                    gain += f"*if(gte(t+{music['offset']},{narration['offset']})*lt(t+{music['offset']},{narration['offset']+narration.get('end',voice_asset['duration'])-narration.get('start',0)}),0.25,1)"
                length = music["end"] - music["start"]
                chain = [f"atrim=start={music['start']}:end={music['end']}", "asetpts=PTS-STARTPTS", f"volume='{gain}':eval=frame"]
                if music.get("fade_in", 0):
                    chain.append(f"afade=t=in:st=0:d={music['fade_in']}")
                if music.get("fade_out", 0):
                    chain.append(f"afade=t=out:st={length-music['fade_out']}:d={music['fade_out']}")
                chain += [f"adelay={round(music['offset']*1000)}:all=1", "asetpts=N/SR/TB", "apad", f"atrim=duration={duration(project)}"]
                filters.append(f"[{source_index}:a]{','.join(chain)}[music]")
                labels.append("[music]")
            for sound in project.get("audio_clips",[]):
                asset=self.store.find(project["media"],sound["media_id"],"Arquivo")
                source_index=len(inputs)//2;inputs += ["-i",self.source(project_id,asset)]
                length=(sound["end"]-sound["start"])/sound["speed"]
                chain=[f"atrim=start={sound['start']}:end={sound['end']}","asetpts=PTS-STARTPTS",*tempo_filters(sound["speed"]),f"volume={sound['volume']}"]
                if sound.get("fade_in",0):chain.append(f"afade=t=in:st=0:d={sound['fade_in']}")
                if sound.get("fade_out",0):chain.append(f"afade=t=out:st={length-sound['fade_out']}:d={sound['fade_out']}")
                chain += [f"adelay={round(sound['offset']*1000)}:all=1","asetpts=N/SR/TB","apad",f"atrim=duration={duration(project)}"]
                label=f"source{source_index}";filters.append(f"[{source_index}:a]{','.join(chain)}[{label}]");labels.append(f"[{label}]")
            if len(labels) > 1:
                filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=0.95:level=0:latency=1[a]")
                run([*inputs, "-filter_complex", ";".join(filters),
                     "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", output])
            else:
                base.replace(output)
            details = probe(output)
            return {"project_name": project["name"], "download_name": export_name(project["name"],project["revision"],quality,width,height,job_id),
                    "revision": project["revision"], "duration": details["duration"], "width": width, "height": height,
                    "preview_seek":project.get("preview_seek",0), "preview_stop":project.get("preview_stop"),
                    "preview_scope": "transition" if self.job(job_id)["kind"] == "transition_preview" else "montage",
                    "quality": quality, "crf": profile["crf"], "bytes": output.stat().st_size, "container": "mp4", "codec": details["codec"],
                    "url": f"/api/projects/{project_id}/exports/{job_id}/video.mp4", "filename": "video.mp4"}
