"""Plain SRT and an independent, non-overlapping subtitle lane."""
import re
from .core import EditorError, number, uid


def validate_captions(values):
    if not isinstance(values,list) or len(values)>500:
        raise EditorError("Use até 500 legendas por projeto.")
    result=[]
    for value in values:
        if not isinstance(value,dict):raise EditorError("Legenda inválida.")
        start=number(value.get("start"),0,1800);end=number(value.get("end"),0,1800)
        content=value.get("text")
        if end-start<.09999 or not isinstance(content,str) or not content.strip() or len(content)>160:
            raise EditorError("Cada legenda precisa de texto (até 160 caracteres) e duração de pelo menos 0,1 s.")
        identity=value.get("id",uid())
        if not isinstance(identity,str) or re.fullmatch(r"[a-f0-9]{32}",identity) is None:raise EditorError("Identificador de legenda inválido.")
        style={}
        for key,options,default in (("title_font",("sans","serif","mono"),"sans"),("title_size",("small","medium","large"),"medium"),("title_position",("top","center","bottom"),"bottom")):
            option=value.get(key,default)
            if option not in options:raise EditorError("Estilo da legenda inválido.")
            style[key]=option
        result.append({"id":identity,"start":start,"end":end,"text":content.strip(),**style})
    result.sort(key=lambda c:(c["start"],c["end"]))
    if len({c['id'] for c in result})!=len(result):raise EditorError("Cada legenda precisa de um identificador diferente.")
    if any(b['start']<a['end']-.00001 for a,b in zip(result,result[1:])):
        raise EditorError("As legendas da mesma faixa não podem se sobrepor.")
    return result


def parse_srt(value):
    if not isinstance(value,str) or not value.strip() or len(value.encode('utf-8'))>1000000:
        raise EditorError("Envie um SRT de texto com até 1 MB.")
    blocks=re.split(r"\n[ \t]*\n",value.lstrip('\ufeff').replace('\r\n','\n').replace('\r','\n').strip())
    if len(blocks)>500:raise EditorError("Use até 500 legendas por projeto.")
    result=[]
    def seconds(stamp):
        hour,minute,second,millis=map(int,re.split(r'[:,]',stamp))
        if minute>59 or second>59:raise EditorError("Tempo inválido no SRT.")
        return hour*3600+minute*60+second+millis/1000
    for block in blocks:
        lines=block.split('\n')
        if lines and lines[0].strip().isdigit():lines=lines[1:]
        if len(lines)<2:raise EditorError("Bloco SRT incompleto.")
        match=re.fullmatch(r"(\d{1,3}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{1,3}:\d{2}:\d{2},\d{3})",lines[0].strip())
        if not match:raise EditorError("Use o formato de tempo HH:MM:SS,mmm no SRT.")
        result.append({'start':seconds(match[1]),'end':seconds(match[2]),'text':'\n'.join(lines[1:])})
    return validate_captions(result)


def to_srt(captions):
    def stamp(value):
        millis=round(value*1000);seconds,millis=divmod(millis,1000);minutes,seconds=divmod(seconds,60);hours,minutes=divmod(minutes,60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"
    return '\n\n'.join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['text']}" for i,c in enumerate(captions,1))+('\n' if captions else '')
