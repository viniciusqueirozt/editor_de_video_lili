"""Shared drawtext layout for scene titles and timed subtitles."""
import os
from pathlib import Path
from .captions import SIZES, caption_lines


def escape_path(path):
    return path.resolve().as_posix().replace(":", "\\:").replace("'", "'\\''")


def text_filters(value, folder, prefix, width, height, default_font, enable=None):
    ratio,_=SIZES[value.get("title_size","medium")]
    lines=caption_lines(value.get("title",value.get("text","")),value.get("title_size","medium"))
    font_size=max(1,min(round(width*ratio),int(height*.6/(len(lines)*1.2))))
    candidates=({"serif":Path("C:/Windows/Fonts/georgia.ttf"),"mono":Path("C:/Windows/Fonts/consola.ttf")} if os.name=="nt" else {"serif":Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),"mono":Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")})
    candidate=candidates.get(value.get("title_font","sans"),default_font)
    font=candidate if candidate.is_file() else default_font
    line_height=font_size*1.2;block_height=len(lines)*line_height
    y={"legacy":height*.32,"top":height*.1,"center":height*.5-block_height/2,"bottom":height*.82-block_height}[value.get("title_position","legacy")]
    filters=""
    for i,line in enumerate(lines):
        file=folder/f"{prefix}-{i:02d}.txt";file.write_text(line,encoding='utf-8')
        filters+=f",drawtext=fontfile='{escape_path(font)}':textfile='{escape_path(file)}':expansion=none:fontsize={font_size}:fontcolor=white:borderw=1:bordercolor=black@0.7:shadowcolor=black@0.5:shadowx=1:shadowy=1:x=(w-text_w)/2:y={y+i*line_height}"
        if enable:filters+=f":enable='{enable}'"
    return filters
