"""Deterministic caption wrapping shared by export and the browser algorithm."""
SIZES = {"small": (.035, 38), "medium": (.044, 30), "large": (.06, 22)}


def caption_lines(value, size="medium"):
    limit = SIZES[size][1]
    result = []
    for paragraph in value.split("\n"):
        lines, line = [], ""
        for word in paragraph.split():
            if line and len(line) + 1 + len(word) <= limit:
                line += " " + word
                continue
            if line:
                lines.append(line)
                line = ""
            while len(word) > limit:
                lines.append(word[:limit])
                word = word[limit:]
            line = word
        if line or not lines:
            lines.append(line)
        result.extend(lines)
    return result
