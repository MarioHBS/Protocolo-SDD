"""Audit-only checks that cross-reference the stage index with backlog and milestones.

Like ``_user_files``: read disk, write nothing, never trust a file's own claim
about itself. Three families of findings:

* ``backlog_orphan`` / ``queue_row_without_section`` -- ``backlog.md`` keeps one
  section per stage still in the Provisional queue; a section nobody points at,
  or a queue row that cites the backlog without having a section, is drift.
* ``milestone_not_contiguous`` -- stages of one milestone must be a contiguous
  slice of the queue (Eval Driven Development).
* ``edd_milestone_without_evaluation`` -- every stage of a milestone is done but
  the milestone has no evaluation file.
* ``weight_light_without_reason`` -- a stage marked ``light`` carries no one-sentence reason.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import _headings

_HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")
_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_PENDING_RE = re.compile(r"(?i)pending|pendente|em andamento|in progress")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _tables(block: str) -> list[list[dict[str, str]]]:
    """Every markdown table in ``block`` as a list of rows keyed by lowercase header."""
    tables: list[list[dict[str, str]]] = []
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) \
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [h.lower() for h in _cells(lines[i])]
            rows: list[dict[str, str]] = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = _cells(lines[i])
                rows.append({h: (cells[k] if k < len(cells) else "") for k, h in enumerate(header)})
                i += 1
            tables.append(rows)
            continue
        i += 1
    return tables


def _section(text: str, heading: str) -> str:
    """Body under the first heading that matches ``heading`` up to the next heading
    of the same or a higher level."""
    level = 2 if heading == "stage_index" else 3
    match = _headings.find_heading(text, heading, level)
    if not match and heading == "stage_index":
        match = re.search(r"(?m)^##\s+5\.[^\n]*$", text)
    if not match:
        return ""
    rest = text[match.end():]
    end = re.search(rf"(?m)^#{{1,{level}}}\s", rest)
    return rest[:end.start()] if end else rest


def _first_slug(cell: str) -> str:
    return _slugify(cell.replace("`", ""))


def _read(path: Path) -> str:
    return _HTML_COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))


def _canonical_rows(text: str) -> list[dict[str, str]]:
    body = _section(text, "stage_index")
    provisional = _headings.find_heading(body, "provisional_queue", 3)
    if provisional:
        body = body[:provisional.start()]
    rows: list[dict[str, str]] = []
    for table in _tables(body):
        rows.extend(table)
    return rows


def _queue_rows(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for table in _tables(_section(text, "provisional_queue")):
        rows.extend(table)
    return rows


def stage_slugs(sdd: Path) -> dict[str, str]:
    """Every stage slug the project knows -> where it lives (canonical index or provisional queue)."""
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        return {}
    text = _read(constitution)
    found: dict[str, str] = {}
    for row in _canonical_rows(text):
        if row.get("slug"):
            found[_first_slug(row["slug"])] = f"canonical {row.get('stage') or row.get('etapa') or ''}".strip()
    for row in _queue_rows(text):
        if row.get("slug"):
            found.setdefault(_first_slug(row["slug"]), "provisional queue")
    return found


def _stage_name(row: dict[str, str]) -> str:
    number = row.get("stage") or row.get("etapa") or ""
    return f"{number}-{_first_slug(row.get('slug', ''))}".strip("-")


def backlog_findings(sdd: Path) -> list[dict]:
    backlog, constitution = sdd / "backlog.md", sdd / "constitution.md"
    if not backlog.is_file() or not constitution.is_file():
        return []
    text = _read(constitution)
    queue = {_first_slug(r.get("slug", "")): r for r in _queue_rows(text) if r.get("slug")}
    pending = {_first_slug(r.get("slug", "")) for r in _canonical_rows(text)
               if _PENDING_RE.search(r.get("status", ""))}
    known = set(queue) | pending
    findings: list[dict] = []
    sections: dict[str, str] = {}
    for match in re.finditer(r"(?m)^##\s+(.+?)\s*$", _read(backlog)):
        heading = match.group(1)
        token = _slugify(re.split(r"\s+[—–-]+\s+", heading)[-1].replace("`", ""))
        if not _SLUG_RE.fullmatch(token):
            continue
        if token in known or "-" in token or re.search(r"\s[—–]\s", heading):
            sections[token] = heading
    for token in sorted(set(sections) - known):
        findings.append({"severity": "warn", "code": "backlog_orphan", "section": sections[token]})
    for slug, row in sorted(queue.items()):
        if "backlog" in row.get("notes", "").lower() and slug not in sections:
            findings.append({"severity": "warn", "code": "queue_row_without_section", "slug": slug})
    return findings


WEIGHT_LIGHT, WEIGHT_FULL = "light", "full"
# Accepted spellings of the light weight (the Portuguese ones follow the `Stage`/`Etapa` precedent).
_LIGHT_WORDS = {"light", "leve"}
_WEIGHT_RE = re.compile(r"([A-Za-zÀ-ÿ]+)[\s:—–-]*(.*)$")


def parse_weight(cell: str) -> tuple[str, str]:
    """(weight, reason) of a `Weight` cell such as ``light: fixes a typo``.

    Anything that is not a light spelling -- an empty cell, ``full``, a typo -- is ``full``:
    the safe direction, since only ``light`` relaxes anything.
    """
    match = _WEIGHT_RE.match(cell.replace("`", "").strip())
    if not match:
        return WEIGHT_FULL, ""
    weight = WEIGHT_LIGHT if match.group(1).lower() in _LIGHT_WORDS else WEIGHT_FULL
    return weight, match.group(2).strip() if weight == WEIGHT_LIGHT else ""


def _row_weight(row: dict[str, str]) -> tuple[str, str]:
    return parse_weight(row.get("weight") or row.get("peso") or "")


def _weighted_rows(text: str) -> list[tuple[str, str, str]]:
    """(stage name, weight, reason) for every canonical row and every queue row."""
    rows = [(_stage_name(row), *_row_weight(row)) for row in _canonical_rows(text) if row.get("slug")]
    rows += [(_first_slug(row["slug"]), *_row_weight(row)) for row in _queue_rows(text) if row.get("slug")]
    return rows


def stage_weights(sdd: Path) -> dict[str, str]:
    """Weight by stage name (``NNN-slug`` for a canonical row, the bare slug for a queue row).

    A stage the index does not list, or an index without a `Weight` column, is simply absent:
    callers treat a missing name as ``full``.
    """
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        return {}
    return {name: weight for name, weight, _ in _weighted_rows(_read(constitution))}


def weight_findings(sdd: Path) -> list[dict]:
    """A `light` stage must say why in one sentence; otherwise marking it is a silent shortcut."""
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        return []
    return [{"severity": "warn", "code": "weight_light_without_reason", "stage": name}
            for name, weight, reason in _weighted_rows(_read(constitution))
            if weight == WEIGHT_LIGHT and not reason]


def milestone_findings(sdd: Path) -> list[dict]:
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        return []
    text = _read(constitution)
    ordered: list[tuple[str, str, bool]] = []  # (milestone, stage, done)
    for row in _canonical_rows(text):
        milestone = row.get("milestone", "").strip()
        if milestone:
            name = _stage_name(row)
            ordered.append((milestone, name, (sdd / "stages" / name / "report.md").is_file()
                            or bool(re.search(r"(?i)done|conclu", row.get("status", "")))))
    for row in _queue_rows(text):
        milestone = row.get("milestone", "").strip()
        if milestone:
            ordered.append((milestone, _first_slug(row.get("slug", "")), False))
    findings: list[dict] = []
    seen: list[str] = []
    for milestone, _, _ in ordered:
        if not seen or seen[-1] != milestone:
            seen.append(milestone)
    for milestone in sorted({m for m in seen if seen.count(m) > 1}):
        findings.append({"severity": "warn", "code": "milestone_not_contiguous", "milestone": milestone})
    directory = sdd / "milestones"
    for milestone in dict.fromkeys(m for m, _, _ in ordered):
        members = [done for m, _, done in ordered if m == milestone]
        if not members or not all(members) or not directory.is_dir():
            continue
        slug = _slugify(milestone)
        folders = [d for d in directory.iterdir()
                   if d.is_dir() and (d.name == slug or d.name.startswith(slug + "-"))]
        if not any(any(f.glob("*.md")) for f in folders):
            findings.append({"severity": "note", "code": "edd_milestone_without_evaluation",
                             "milestone": milestone})
    return findings
