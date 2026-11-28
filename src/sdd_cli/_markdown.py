"""Which parts of a Markdown file are code, so a detector can leave them alone.

Only what is certainly code is hidden: a fenced block that is closed, and an inline span whose
backticks pair up inside one block of text. In doubt (an open fence, a lone backtick) nothing is
hidden and the finding is reported.
"""

from __future__ import annotations

import re

_FENCE_RE = re.compile(r"[ \t]*(`{3,}|~{3,})([^\n]*)")
# A line that starts a new block (list item, quote), and one that is a block on its own (table row,
# heading): an inline span never runs across them.
_STARTS_BLOCK_RE = re.compile(r"[ \t]*(?:[-*+] |\d+[.)] |>)")
_OWN_BLOCK_RE = re.compile(r"[ \t]*(?:\||#{1,6} )")
_TICKS_RE = re.compile(r"`+")


def _blank(text: str) -> str:
    return re.sub(r"[^\n]", " ", text)


def _mask_spans(block: str) -> str:
    runs = list(_TICKS_RE.finditer(block))
    out, done, i = [], 0, 0
    while i < len(runs):
        opener = runs[i]
        escaped = (opener.start() - len(block[:opener.start()].rstrip("\\"))) % 2 == 1
        closer = None if escaped else next(
            (j for j in range(i + 1, len(runs)) if len(runs[j].group()) == len(opener.group())), None)
        if closer is None:
            i += 1
            continue
        end = runs[closer].end()
        out += [block[done:opener.start()], _blank(block[opener.start():end])]
        done, i = end, closer + 1
    out.append(block[done:])
    return "".join(out)


def mask_code(text: str) -> str:
    """``text`` with code replaced by spaces: same length, same newlines, so offsets and line
    numbers still point at the original. Lines are split on ``\\n`` only, so a caller may pass
    bytes decoded as Latin-1 to keep byte offsets."""
    lines = text.split("\n")
    out: list[str] = []
    block: list[str] = []

    def flush() -> None:
        if block:
            out.extend(_mask_spans("\n".join(block)).split("\n"))
            block.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        fence = _FENCE_RE.match(line)
        # A backtick fence cannot have a backtick after it: that line is an inline span.
        if fence and not (fence.group(1)[0] == "`" and "`" in fence.group(2)):
            mark = fence.group(1)
            closing = re.compile(rf"[ \t]*{mark[0]}{{{len(mark)},}}[ \t\r]*\Z")
            end = next((j for j in range(i + 1, len(lines)) if closing.match(lines[j])), None)
            if end is not None:
                flush()
                out.extend(_blank(x) for x in lines[i:end + 1])
                i = end + 1
                continue
        if not line.strip(" \t\r"):
            flush()
            out.append(line)
        elif _OWN_BLOCK_RE.match(line):
            flush()
            block.append(line)
            flush()
        else:
            if _STARTS_BLOCK_RE.match(line):
                flush()
            block.append(line)
        i += 1
    flush()
    return "\n".join(out)
