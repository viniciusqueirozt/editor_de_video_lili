"""Reject ambiguous HTTP framing before reading or forwarding a request body."""

import re
import json
import math

from .core import EditorError


def validate_headers(headers):
    # These fields select the origin, parser or session. Do not let different
    # layers choose different values from an ambiguous duplicate field.
    for name in ("Host", "Origin", "Sec-Fetch-Site", "Content-Type", "Cookie", "Authorization"):
        if len(headers.get_all(name, [])) > 1:
            raise EditorError("Cabeçalho de segurança duplicado.")
    lengths = headers.get_all("Content-Length", [])
    if len(lengths) > 1 or headers.get_all("Transfer-Encoding", []):
        raise EditorError("Formato de envio não permitido.")
    value = lengths[0] if lengths else "0"
    if not re.fullmatch(r"[0-9]{1,12}", value):
        raise EditorError("Tamanho de envio inválido.")
    size = int(value)
    if size > 2 * 1024 ** 3:
        raise EditorError("O envio excede o limite permitido.", 413)
    return size


def json_object(raw):
    """One interpretation of a complete UTF-8 JSON object at the control API."""
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError("Duplicate JSON key")
            result[key]=value
        return result
    def finite_only(value):raise ValueError("Non-finite JSON constant")
    try:
        data=json.loads(raw.decode("utf-8"),object_pairs_hook=unique,parse_constant=finite_only)
        pending=[data]
        while pending:
            item=pending.pop()
            if isinstance(item,dict):pending.extend(item.keys());pending.extend(item.values())
            elif isinstance(item,list):pending.extend(item)
            elif isinstance(item,str):item.encode("utf-8")  # Reject escaped lone surrogates too.
            elif isinstance(item,float) and not math.isfinite(item):raise ValueError("Non-finite JSON number")
    except (ValueError,UnicodeError,RecursionError):
        raise EditorError("JSON inválido. Use campos únicos e valores válidos.") from None
    if not isinstance(data,dict):raise EditorError("Envie um objeto JSON.")
    return data
