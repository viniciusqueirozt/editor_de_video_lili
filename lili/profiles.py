"""Local MP4/H.264 export profiles; dimensions preserve the project ratio."""
from .core import EditorError
FORMATS = {"vertical": (1080, 1920), "square": (1080, 1080), "landscape": (1920, 1080)}
PROFILES = {"preview": (.5, 25), "balanced": (2/3, 23), "full": (1, 21), "high": (1, 18)}


def render_profile(settings, quality):
    if not isinstance(quality, str) or quality not in PROFILES:
        raise EditorError("Qualidade inválida.")
    width, height = settings.get("width"), settings.get("height")
    if any(type(v) is not int or not 2 <= v <= 3840 or v % 2 for v in (width, height)):
        raise EditorError("Dimensões de exportação inválidas.")
    scale, crf = PROFILES[quality]
    return {"width": max(2, round(width*scale/2)*2), "height": max(2, round(height*scale/2)*2), "crf": crf, "quality": quality}
