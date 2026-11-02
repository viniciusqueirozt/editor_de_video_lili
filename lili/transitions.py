"""Color passages at an explicit adjacent pair; montage timing stays unchanged."""
import math
from .core import clip_duration

# Public IDs are mapped to documented FFmpeg filter names, never interpolated
# from a client-supplied expression. This compositor is Lili's own implementation.
COMPOSITED = {"dissolve":"fade", "wipe_left":"wipeleft", "wipe_right":"wiperight", "slide_left":"slideleft", "slide_right":"slideright"}
KINDS = {"black", "white"} | set(COMPOSITED)

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
        if transition["kind"] in COMPOSITED: continue
        half = transition["duration"] / 2
        if transition["right"] == clip["id"]:
            filters.append(f"fade=t=in:st=0:d={half}:color={transition['kind']}")
        if transition["left"] == clip["id"]:
            start = clip_duration(clip) - half
            filters.append(f"fade=t=out:st={start}:d={half}:color={transition['kind']}")
    return ",".join(filters)


def apply_style(project, style):
    """One atomic bulk edit; protected junctions and montage clocks stay intact."""
    from .core import EditorError, number
    if not isinstance(style, dict) or not isinstance(style.get("kind"), str) or style["kind"] not in KINDS | {"keep", "none"}:
        raise EditorError("Escolha uma transição válida.")
    kind = style["kind"]
    if kind == "keep": return
    value = number(style.get("duration", .5), .1, 3)
    old = {(t["left"], t["right"]): t for t in clean_transitions(project)}
    result = []
    for left, right in zip(project["timeline"], project["timeline"][1:]):
        pair = (left["id"], right["id"])
        if left["locked"] or right["locked"]:
            if pair in old: result.append(old[pair])
        elif kind != "none":
            result.append({"left":pair[0], "right":pair[1], "kind":kind,
                           "duration":min(value, clip_duration(left), clip_duration(right))})
    project["transitions"] = result


def dissolve_graph(project):
    """Composite endpoint holds across cuts, preserving narration/subtitle clocks.

    Half of the transition is before the cut and half after it. Padding holds
    only the adjacent endpoint frame, rather than shortening the montage.
    Input 0 supplies the untouched concatenated audio; clips start at input 1.
    """
    clips = project["timeline"]
    transitions = {(t["left"],t["right"]):t for t in clean_transitions(project) if t["kind"] in COMPOSITED}
    if not transitions:return None
    filters = [f"[{i+1}:v]setpts=PTS-STARTPTS,fps=30,settb=AVTB,format=yuv420p[c{i}]" for i in range(len(clips))]
    previous="c0";at=clip_duration(clips[0])
    for i, clip in enumerate(clips[1:],1):
        item=transitions.get((clips[i-1]["id"],clip["id"]))
        if item:
            value=item["duration"];half=value/2
            filters += [f"[{previous}]tpad=stop_mode=clone:stop_duration={half},fps=30,settb=AVTB[l{i}]",
                        f"[c{i}]tpad=start_mode=clone:start_duration={half},fps=30,settb=AVTB[r{i}]",
                        f"[l{i}][r{i}]xfade=transition={COMPOSITED[item['kind']]}:duration={value}:offset={at-half},format=yuv420p,fps=30,settb=AVTB[v{i}]"]
        else:filters.append(f"[{previous}][c{i}]concat=n=2:v=1:a=0,fps=30,settb=AVTB[v{i}]")
        previous=f"v{i}";at+=clip_duration(clip)
    filters.append(f"[{previous}]trim=duration={at},setpts=PTS-STARTPTS,fps=30,format=yuv420p[blended]")
    return ";".join(filters)
