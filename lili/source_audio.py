"""Independent audio references. Separation never copies or modifies source media."""
import re
from .core import EditorError, clip_duration, number, text, uid


def validate_audio(store, project, data):
    if not isinstance(data, dict):raise EditorError("Informe um bloco de áudio válido.")
    asset=store.find(project["media"],data.get("media_id"),"Arquivo")
    if asset.get("deleted_at") or asset.get("status")!="ready" or not asset.get("has_audio"):
        raise EditorError("Escolha um arquivo pronto que contenha áudio.")
    start=number(data.get("start",0),0,asset["duration"])
    end=number(data.get("end",asset["duration"]),start,asset["duration"])
    speed=number(data.get("speed",1),.25,4);length=(end-start)/speed
    if round(length,4)<.1 or length>1800:raise EditorError("Use de 0,1 segundo a 30 minutos de áudio.")
    fade_in=number(data.get("fade_in",0),0,length);fade_out=number(data.get("fade_out",0),0,length)
    if fade_in+fade_out>length+.00001:raise EditorError("Os fades devem caber no trecho de áudio.")
    audio_id=data.get("id",uid());source=data.get("source_clip_id")
    if not isinstance(audio_id,str) or not re.fullmatch(r"[a-f0-9]{32}",audio_id):raise EditorError("Identificador de áudio inválido.")
    if source is not None and (not isinstance(source,str) or not re.fullmatch(r"[a-f0-9]{32}",source)):raise EditorError("Referência de cena inválida.")
    if not isinstance(data.get("locked",False),bool):raise EditorError("Proteção de áudio inválida.")
    return {"id":audio_id,"media_id":asset["id"],"source_clip_id":source,"start":start,"end":end,"speed":speed,
            "offset":number(data.get("offset",0),0,1800),"volume":number(data.get("volume",1),0,2),
            "fade_in":fade_in,"fade_out":fade_out,"locked":data.get("locked",False),"label":text(data.get("label",asset["name"]),160)}


def detach(store, project, clip, offset, changes=None):
    if clip.get("audio_detached"):raise EditorError("O som desta cena já está separado.",409)
    if clip.get("locked"):raise EditorError("Desproteja a cena antes de separar seu áudio.",409)
    data={"media_id":clip["media_id"],"source_clip_id":clip["id"],"start":clip["start"],"end":clip["end"],
          "speed":clip.get("speed",1),"offset":offset,"volume":clip["volume"],"fade_in":clip.get("audio_fade_in",0),
          "fade_out":clip.get("audio_fade_out",0),"label":clip["label"]}
    data.update({k:v for k,v in (changes or {}).items() if k in ("start","end","speed","offset","volume","fade_in","fade_out","label","locked")})
    sound=validate_audio(store,project,data)
    project["audio_clips"].append(sound);clip["audio_detached"]=True
    # Fades now belong to the independent sound. Dormant image-side fades
    # must not impose an unrelated minimum length when trimming the picture.
    clip["audio_fade_in"]=0;clip["audio_fade_out"]=0
    return sound


def separate_new(store, project, ids):
    offset=0
    for clip in project["timeline"]:
        asset=store.find(project["media"],clip["media_id"],"Arquivo")
        if clip["id"] in ids and not clip.get("audio_detached") and not clip.get("locked") and asset.get("has_audio"):
            detach(store,project,clip,offset)
        offset+=clip_duration(clip)


def apply_audio_operation(store,project,operation,args):
    if operation=="audio_detach":
        clip=store.find(project["timeline"],args.get("clip_id"));offset=0
        for item in project["timeline"]:
            if item["id"]==clip["id"]:break
            offset+=clip_duration(item)
        sound=detach(store,project,clip,offset,args)
        action=args.get("then")
        if action is not None:
            if action not in ("remove","split","duplicate"):raise EditorError("Ação de áudio inválida.")
            apply_audio_operation(store,project,"audio_clip_"+action,{"audio_id":sound["id"],"at":args.get("at")})
        return sound
    if operation=="audio_clip_add":
        sound=validate_audio(store,project,args);project["audio_clips"].append(sound);return
    sound=store.find(project["audio_clips"],args.get("audio_id"),"Áudio")
    if sound["locked"] and (operation!="audio_clip_update" or any(k not in ("audio_id","locked") and sound.get(k)!=v for k,v in args.items())):
        raise EditorError("Desproteja este áudio antes de alterá-lo.",409)
    if operation=="audio_clip_update":
        changes={k:v for k,v in args.items() if k not in ("audio_id","id","source_clip_id")}
        sound.update(validate_audio(store,project,{**sound,**changes}))
    elif operation=="audio_clip_remove":project["audio_clips"].remove(sound)
    elif operation=="audio_clip_duplicate":
        project["audio_clips"].append(validate_audio(store,project,{**sound,"id":uid(),"locked":False,"offset":sound["offset"]+(sound["end"]-sound["start"])/sound["speed"]}))
    elif operation=="audio_clip_split":
        at=number(args.get("at"),sound["start"],sound["end"])
        left=validate_audio(store,project,{**sound,"end":at,"fade_out":0})
        right=validate_audio(store,project,{**sound,"id":uid(),"start":at,"fade_in":0,"offset":sound["offset"]+(at-sound["start"])/sound["speed"]})
        sound.update(left);project["audio_clips"].insert(project["audio_clips"].index(sound)+1,right)
    else:raise EditorError("Operação de áudio desconhecida.")
