"""Color passages at an explicit adjacent pair; montage timing stays unchanged."""
import math
from .core import clip_duration

KINDS = {"black", "white"}

def clean_transitions(project):
    clips = project["timeline"]
    pairs = {(a["id"], b["id"]): (a, b) for a, b in zip(clips, clips[1:])}
    result = []
    seen = set()
    for item in project.get("transitions", []):
        if not isinstance(item, dict): continue
        pair = (item.get("left"), item.get("right"))
        if not all(isinstance(v, str) for v in pair) or pair not in pairs or pair in seen: continue
        kind, value = item.get("kind"), item.get("duration")
        if not isinstance(kind, str) or kind not in KINDS or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value): continue
        maximum = min(3, *(clip_duration(c) for c in pairs[pair]))
        value = round(min(value, maximum), 4)
        if value < .1: continue
        result.append({"left":pair[0], "right":pair[1], "kind":kind, "duration":value})
        seen.add(pair)
    return result

def clip_transition_filters(project, index):
    clip = project["timeline"][index]
    filters = []
    for transition in clean_transitions(project):
        half = transition["duration"] / 2
        if transition["right"] == clip["id"]:
            filters.append(f"fade=t=in:st=0:d={half}:color={transition['kind']}")
        if transition["left"] == clip["id"]:
            start = clip_duration(clip) - half
            filters.append(f"fade=t=out:st={start}:d={half}:color={transition['kind']}")
    return ",".join(filters)
