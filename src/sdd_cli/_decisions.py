"""The constitution's decision table (§3) and decision-records field (§7).

Everything here works on LF text and returns new text; ``edit_constitution`` is the one place
that touches the file: raw bytes in, raw bytes out (the owner's line endings stay), and a copy of
the original in ``.sdd/.pre-fix-backup/<stamp>/`` before anything changes. A §3 table without the
``Record`` column keeps being read: the column is added only on request.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import _index_checks

RECORD_ALIASES = ("record", "registro", "adr")
_PT_LABELS = ("decisão", "decisao", "escolha", "justificativa", "travada em", "travada em:")
_DECISION_ID_RE = re.compile(r"D-\d+\Z")
_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
_NONE_RE = re.compile(
    r"(?i)^(?:not applicable|n/?a|none|no adrs?|nenhum|sem adrs?|n[aã]o se aplica|n[aã]o aplic[aá]vel|"
    r"n[aã]o h[aá] adrs?)(?![\w])")

MODE_INTERNAL, MODE_EXTERNAL, MODE_NONE, MODE_UNSET, MODE_LEGACY = (
    "internal", "external", "none", "unset", "legacy")


# --------------------------------------------------------------------- §3

def _section_body(text: str, number: int) -> tuple[int, int] | None:
    """Offsets of the body of ``## <number>. ...`` up to the next ``##`` heading."""
    heading = re.search(rf"(?m)^##\s+{number}\.[^\n]*$", text)
    if not heading:
        return None
    rest = text[heading.end():]
    following = re.search(r"(?m)^#{1,2}\s", rest)
    return heading.end(), heading.end() + (following.start() if following else len(rest))


def _find_table(lines: list[str]) -> tuple[int, int, int] | None:
    """``(header, first_row, end)`` line indexes of the first table outside HTML comments."""
    in_comment = False
    for i, line in enumerate(lines):
        was = in_comment
        for token in re.findall(r"<!--|-->", line):
            in_comment = token == "<!--"
        if (not was and not in_comment and line.lstrip().startswith("|")
                and i + 1 < len(lines) and _index_checks._SEPARATOR_RE.match(lines[i + 1])):
            end = i + 2
            while end < len(lines) and lines[end].lstrip().startswith("|"):
                end += 1
            return i, i + 2, end
    return None


def _record_column(header: list[str]) -> int | None:
    for index, label in enumerate(header):
        label = label.strip().casefold()
        if any(label == name or label.startswith(name + " ") for name in RECORD_ALIASES):
            return index
    return None


def rows(text: str) -> list[dict] | None:
    """The §3 rows (``id``, ``cells``, ``record``, ``placeholder``), or ``None`` without a §3 table."""
    span = _section_body(text, 3)
    if not span:
        return None
    lines = text[span[0]:span[1]].splitlines()
    found = _find_table(lines)
    if not found:
        return None
    header_at, first, end = found
    header = _index_checks._cells(lines[header_at])
    record_at = _record_column(header)
    result = []
    for line in lines[first:end]:
        cells = _index_checks._cells(line)
        if not cells or not _DECISION_ID_RE.match(cells[0]):
            continue
        result.append({"id": cells[0], "cells": cells,
                       # by header label (English or Portuguese), so a reordered table reads right
                       "fields": {h.casefold(): cells[i] for i, h in enumerate(header) if i < len(cells)},
                       "record": cells[record_at] if record_at is not None and record_at < len(cells) else "",
                       "placeholder": len(cells) > 1 and cells[1].startswith("[")})
    return result


def real_ids(text: str) -> list[str]:
    """Ids of the §3 rows that record a decision (the template's ``[e.g. ...]`` row is not one)."""
    return [r["id"] for r in rows(text) or [] if not r["placeholder"]]


def has_record_column(text: str) -> bool | None:
    span = _section_body(text, 3)
    if not span:
        return None
    lines = text[span[0]:span[1]].splitlines()
    found = _find_table(lines)
    if not found:
        return None
    return _record_column(_index_checks._cells(lines[found[0]])) is not None


def add_record_column(text: str) -> tuple[str, bool]:
    """Append an empty ``Record`` column to the §3 table when it has none; a second run changes nothing."""
    span = _section_body(text, 3)
    if not span:
        return text, False
    start, end = span
    lines = text[start:end].splitlines(keepends=True)
    found = _find_table(lines)
    if not found:
        return text, False
    header_at, first, stop = found
    header = _index_checks._cells(lines[header_at])
    if _record_column(header) is not None:
        return text, False
    # A table the agent wrote in Portuguese gets the Portuguese label (`Registro` is an accepted alias).
    portuguese = any(label.casefold() in _PT_LABELS for label in header)
    lines[header_at] = _index_checks._with_cell(lines[header_at], "Registro" if portuguese else "Record",
                                                len(header))
    sep = lines[header_at + 1]
    body = sep.rstrip("\r\n")
    lines[header_at + 1] = body.rstrip() + "--------|" + sep[len(body):]
    for i in range(first, stop):
        lines[i] = _index_checks._with_cell(lines[i], "", len(header))
    return text[:start] + "".join(lines) + text[end:], True


def set_record(text: str, decision_id: str, link: str, *, overwrite: bool = False) -> tuple[str, str]:
    """Write ``link`` in the ``Record`` cell of ``decision_id``.

    Returns ``(text, outcome)`` where outcome is ``set``, ``same`` (already that link), ``kept``
    (another value is there and ``overwrite`` is off), ``no_column`` or ``no_row``.
    """
    span = _section_body(text, 3)
    if not span:
        return text, "no_row"
    start, end = span
    lines = text[start:end].splitlines(keepends=True)
    found = _find_table(lines)
    if not found:
        return text, "no_row"
    header_at, first, stop = found
    header = _index_checks._cells(lines[header_at])
    column = _record_column(header)
    if column is None:
        return text, "no_column"
    for i in range(first, stop):
        cells = _index_checks._cells(lines[i])
        if not cells or cells[0] != decision_id:
            continue
        cells += [""] * (len(header) - len(cells))
        if cells[column] == link:
            return text, "same"
        if cells[column] and not overwrite:
            return text, "kept"
        cells[column] = link
        ending = lines[i][len(lines[i].rstrip("\r\n")):]
        lines[i] = "| " + " | ".join(cells) + " |" + ending
        return text[:start] + "".join(lines) + text[end:], "set"
    return text, "no_row"


# --------------------------------------------------------------------- §7

_FIELD_RE = re.compile(r"(?im)^([-*])[ \t]+\*\*Decision records(?:\s*\(ADRs\))?:\*\*([^\n]*(?:\n[ \t]+\S[^\n]*)*)")


def decision_records(text: str) -> dict:
    """``{mode, path, raw}`` read from the §7 ``Decision records`` field.

    ``mode`` is ``internal`` (``.sdd/decisions/``), ``external`` (``path`` says where), ``none``
    ("not applicable"), ``unset`` (the template's placeholder, or no field) or ``legacy`` (free text
    written before this field had a format).
    """
    span = _section_body(text, 7)
    match = _FIELD_RE.search(text[span[0]:span[1]]) if span else None
    if not match:
        return {"mode": MODE_UNSET, "path": "", "raw": ""}
    raw = " ".join(_COMMENT_RE.sub(" ", match.group(2)).split())
    if not raw or raw.startswith("["):
        return {"mode": MODE_UNSET, "path": "", "raw": raw}
    if re.match(r"(?i)(?:internal|interno)\b", raw):
        return {"mode": MODE_INTERNAL, "path": "", "raw": raw}
    if re.match(r"(?i)(?:external|externo)\b", raw):
        rest = re.sub(r"(?i)^(?:external|externo)\b[\s—–:(-]*", "", raw).strip()
        quoted = re.match(r"([`'\"])(.+?)\1", rest)  # a path with spaces is written between backticks
        token = quoted.group(2) if quoted else (rest.split()[0] if rest else "")
        return {"mode": MODE_EXTERNAL, "path": token.strip("`'\"(),;"), "raw": raw}
    if _NONE_RE.match(raw):
        return {"mode": MODE_NONE, "path": "", "raw": raw}
    return {"mode": MODE_LEGACY, "path": "", "raw": raw}


def set_decision_records(text: str, mode: str, path: str = "") -> str:
    """Rewrite the §7 field as ``internal`` or ``external — <path>``; free text it replaces is kept
    after the dash, so nothing the owner wrote is lost."""
    current = decision_records(text)
    shown = f"`{path}`" if re.search(r"\s", path) else path
    value = mode if mode == MODE_INTERNAL else f"{MODE_EXTERNAL} — {shown}".rstrip(" —")
    if current["mode"] in (MODE_LEGACY, MODE_NONE):  # what the owner wrote is never lost
        value += f" — previously: {current['raw']}"
    line = f"- **Decision records:** {value}"
    span = _section_body(text, 7)
    if not span:
        return text
    body = text[span[0]:span[1]]
    match = _FIELD_RE.search(body)
    if match:
        return text[:span[0] + match.start()] + line + text[span[0] + match.end():]
    rest = body.rstrip("\n")
    return text[:span[0]] + rest + "\n" + line + "\n" + body[len(rest):].lstrip("\n") + text[span[1]:]


# ------------------------------------------------------------------- file

def edit_constitution(root: Path, edit: Callable[[str], str], *, dry_run: bool = False) -> bool:
    """Apply ``edit`` (LF text in, LF text out) to ``.sdd/constitution.md``; ``True`` when it changed.

    Raw bytes in and out keep the owner's line endings; the original is copied to
    ``.sdd/.pre-fix-backup/<stamp>/constitution.md`` first. ``dry_run`` only reports.
    """
    path = root / ".sdd" / "constitution.md"
    if not path.is_file():
        return False
    original = path.read_bytes()
    try:
        raw = original.decode("utf-8")
    except UnicodeDecodeError:
        return False
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    updated = edit(text)
    if updated == text:
        return False
    if not dry_run:
        backup = root / ".sdd" / ".pre-fix-backup" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        backup.mkdir(parents=True, exist_ok=True)
        if not (backup / "constitution.md").exists():  # two edits in one second keep the first original
            (backup / "constitution.md").write_bytes(original)
        path.write_bytes((updated.replace("\n", "\r\n") if crlf else updated).encode("utf-8"))
    return True
