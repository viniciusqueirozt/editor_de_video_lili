"""Reject ambiguous HTTP framing before reading or forwarding a request body."""

import re

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
