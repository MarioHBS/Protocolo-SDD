"""Exact English and Portuguese constitution headings used by CLI detectors."""

from __future__ import annotations

import re

HEADING_ALIASES = {
    "active_tracks": ("Active tracks", "Trilhas ativas"),
    "provisional_queue": ("Provisional queue", "Fila provisória"),
    "stage_index": ("Stage index", "Índice de etapas"),
}


def find_heading(text: str, key: str, level: int) -> re.Match[str] | None:
    """Match one complete heading, allowing its parenthesized template note."""
    names = "|".join(re.escape(name) for name in HEADING_ALIASES[key])
    number = r"5\.\s*" if key == "stage_index" else ""
    return re.search(rf"(?im)^#{{{level}}}\s+{number}(?:{names})"
                     r"(?:\s+\([^\n)]*\))?\s*$", text)
