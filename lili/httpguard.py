"""Reject ambiguous HTTP framing before reading or forwarding a request body."""

import re

from .core import EditorError


def validate_headers(headers):
    if len(headers.get_all("Host", [])) > 1:
        raise EditorError("Cabeçalho de endereço duplicado.")
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
