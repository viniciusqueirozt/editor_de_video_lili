"""Rebuild the approved Ritmo identity as SVG and app icons. No user media."""
from pathlib import Path
import json
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent.parent
WEB=ROOT/"web"
FOREST="#283c30"
LIME="#d6e8ae"
SAGE="#789460"

def symbol(ink,dots=None):
    dots=dots or ink
    return (f'<rect x="18" y="20" width="16" height="72" rx="8" fill="{ink}"/>'
            f'<circle cx="52" cy="40" r="8" fill="{dots}"/>'
            f'<rect x="44" y="58" width="16" height="50" rx="8" fill="{ink}"/>'
            f'<rect x="70" y="20" width="16" height="72" rx="8" fill="{ink}"/>'
            f'<circle cx="104" cy="40" r="8" fill="{dots}"/>'
            f'<rect x="96" y="58" width="16" height="50" rx="8" fill="{ink}"/>')

def logo(ink,dots):
    letters=(f'<path d="M124 22v42q0 12 12 12" fill="none" stroke="{ink}" stroke-width="16" stroke-linecap="round"/>'
             f'<circle cx="157" cy="29" r="8" fill="{ink}"/><path d="M157 53v24" stroke="{ink}" stroke-width="16" stroke-linecap="round"/>'
             f'<path d="M186 22v42q0 12 12 12" fill="none" stroke="{ink}" stroke-width="16" stroke-linecap="round"/>'
             f'<circle cx="219" cy="29" r="8" fill="{ink}"/><path d="M219 53v24" stroke="{ink}" stroke-width="16" stroke-linecap="round"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 242 96" role="img" aria-label="Lili — Ritmo"><g transform="translate(0 0) scale(.75)">{symbol(ink,dots)}</g>{letters}</svg>'

if __name__=="__main__":
    WEB.joinpath("logo-ritmo.svg").write_text(logo(FOREST,SAGE),encoding="utf-8")
    WEB.joinpath("logo-ritmo-inverse.svg").write_text(logo("#f5f5f0",LIME),encoding="utf-8")
    favicon=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><title>Lili — Ritmo</title><rect width="128" height="128" rx="27" fill="{FOREST}"/>{symbol(LIME)}</svg>'
    WEB.joinpath("favicon.svg").write_text(favicon,encoding="utf-8")
    # Full-bleed app background; mark stays inside the central maskable safe zone.
    for size in (192,512):
        scale=size*4/128
        im=Image.new("RGB",(size*4,size*4),FOREST);draw=ImageDraw.Draw(im)
        def coord(value):return (64+(value-64)*.76)*scale
        for x,y,h in ((18,20,72),(44,58,50),(70,20,72),(96,58,50)):
            draw.rounded_rectangle((coord(x),coord(y),coord(x+16),coord(y+h)),radius=8*.76*scale,fill=LIME)
        for x in (52,104):draw.ellipse((coord(x-8),coord(32),coord(x+8),coord(48)),fill=LIME)
        im.resize((size,size),Image.Resampling.LANCZOS).save(WEB/f"icon-{size}.png")
    manifest=json.loads(WEB.joinpath("manifest.webmanifest").read_text(encoding="utf-8"))
    manifest.update(background_color=FOREST,theme_color="#f5f5f0")
    for icon in manifest["icons"]:icon["src"]=icon["src"].split("?")[0]+"?v=ritmo-1"
    WEB.joinpath("manifest.webmanifest").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
