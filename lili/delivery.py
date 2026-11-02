"""Export presentation metadata. Names are suggestions, never filesystem paths."""
import copy
import re
import unicodedata
from urllib.parse import quote


def safe_stem(value, byte_limit=96):
    value=unicodedata.normalize("NFKC",value if isinstance(value,str) else "")
    value="".join(c if unicodedata.category(c)[0] in ("L","N","M") or c in "_-" else "-" for c in value)
    value=re.sub("-+","-",value).strip("-_")
    while len(value.encode("utf-8"))>byte_limit:value=value[:-1]
    value=value.rstrip("-_") or "lili"
    if value.upper() in {"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}:value="lili-"+value
    return value


def export_name(project_name,revision,quality,width,height,job_id):
    def integer(value):return value if type(value) is int and 0<value<1000000000 else 0
    quality={"preview":"previa","balanced":"equilibrada","full":"final","high":"alta"}.get(quality,"mp4")
    suffix=re.sub("[^a-f0-9]","",str(job_id))[:12] or "export"
    return f"{safe_stem(project_name)}-v{integer(revision)}-{quality}-{integer(width)}x{integer(height)}-{suffix}.mp4"


def content_disposition(filename):
    name=filename[:-4] if isinstance(filename,str) and filename.lower().endswith(".mp4") else filename
    stem=safe_stem(name,200)
    fallback=safe_stem(unicodedata.normalize("NFKD",stem).encode("ascii","ignore").decode("ascii"),200)
    return f'attachment; filename="{fallback}.mp4"; filename*=UTF-8\'\'{quote(stem+".mp4",safe="")}'


def job_delivery(job,store):
    result=copy.deepcopy(job)
    if result.get("kind") not in ("export","transition_preview") or result.get("status")!="done":return result
    data=result.get("result")
    if not isinstance(data,dict):data={};result["result"]=data
    if not isinstance(data.get("download_name"),str):
        data["download_name"]=export_name(data.get("project_name","lili"),data.get("revision"),data.get("quality"),data.get("width"),data.get("height"),result["id"]) if type(data.get("revision")) is int else f"lili-exportacao-{safe_stem(result['id'])[:12]}.mp4"
    path=store.folder(result["project_id"])/"exports"/result["id"]/"video.mp4"
    try:
        size=path.stat().st_size if path.is_file() else None
        expected=data.get("bytes")
        state="missing" if size is None else "empty" if size==0 else "changed" if type(expected) is int and expected>0 and size!=expected else "available"
    except OSError:state="unavailable"
    data.update(download_available=state=="available",artifact_state=state)
    return result
