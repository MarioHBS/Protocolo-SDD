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


_LOCKED_RE = re.compile(r"(?im)^[-*]?\s*\*\*Status:\*\*\s*locked\b")
_LOCKED_BY_RE = re.compile(r"(?im)^[-*]?\s*\*{0,2}Locked-by-audit:\*{0,2}\s*(.+)$")
_ROUND_RE = re.compile(r"(?m)^##\s+Round\s+(\d+)\b")
_VERDICT_RE = re.compile(r"(?im)^[-*]?\s*\*\*Verdict:\*\*\s*(NOT READY TO LOCK|READY TO LOCK)\b")
_FINDING_RE = re.compile(
    r"(?m)^\|\s*(F-\d+)\s*\|\s*(BLOCKER|MAJOR|MINOR)\s*\|[^|\n]*\|[^|\n]*\|\s*(open|fixed|dismissed)\s*\|")
_TOUCHES_PATHS_RE = re.compile(r"(?im)^\s*[-*]\s*paths:\s*(.+)$")
_BACKTICKED_RE = re.compile(r"`([^`]+)`")


def _glob_regex(glob: str) -> re.Pattern[str]:
    """``**`` crosses folders, ``*`` and ``?`` stay inside one; everything else is literal."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out))


def _static_prefix(glob: str) -> str:
    cut = re.search(r"[*?\[]", glob)
    return (glob[:cut.start()] if cut else glob).rstrip("/")


def _paths_overlap(a: str, b: str) -> bool:
    """Whether two path globs can name the same file: one matches the other, or one's fixed
    folder prefix contains the other's. Deliberately conservative: a doubt is not reported."""
    if _glob_regex(a).fullmatch(b) or _glob_regex(b).fullmatch(a):
        return True
    pa, pb = _static_prefix(a), _static_prefix(b)
    return bool(pa and pb and (pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")))


def audit_triggers(sdd: Path) -> list[str]:
    """Path globs under ``## Triggers`` of ``.sdd/audit-lenses.md`` (backticked, in bullet lines)."""
    path = sdd / "audit-lenses.md"
    if not path.is_file():
        return []
    text = _read(path)
    match = re.search(r"(?im)^##\s+triggers?\b[^\n]*$", text)
    if not match:
        return []
    rest = text[match.end():]
    end = re.search(r"(?m)^##\s", rest)
    body = rest[:end.start()] if end else rest
    triggers: list[str] = []
    for line in body.splitlines():
        if re.match(r"^\s*[-*]\s", line):
            triggers += [t.strip() for t in _BACKTICKED_RE.findall(line) if re.search(r"[/*.]", t)]
    return triggers


def _stage_dirs(sdd: Path) -> list[Path]:
    """Stage folders of the project and of its parallel tracks (never the archived ``_closed``)."""
    found: list[Path] = []
    roots = [sdd / "stages"] + sorted((sdd / "tracks").glob("*/stages")) if (sdd / "tracks").is_dir() \
        else [sdd / "stages"]
    for root in roots:
        if root.is_dir():
            found += [d for d in sorted(root.iterdir())
                      if d.is_dir() and not d.name.startswith((".", "_"))]
    return [d for d in found if "_closed" not in d.parts]


def _audit_record(audit: Path) -> dict:
    """What ``audit.md`` says: last round number, last verdict, and each finding's last state."""
    text = _read(audit)
    rounds = [int(n) for n in _ROUND_RE.findall(text)]
    last = list(_ROUND_RE.finditer(text))
    verdicts = _VERDICT_RE.findall(text[last[-1].start():]) if last else []
    states: dict[str, tuple[str, str]] = {}
    for finding_id, severity, state in _FINDING_RE.findall(text):
        states[finding_id] = (severity, state)
    return {"round": max(rounds) if rounds else 0, "verdict": verdicts[0].upper() if verdicts else "",
            "states": states}


def _lock_mismatch(header: str, record: dict) -> list[str]:
    """Why a ``Locked-by-audit:`` line disagrees with ``audit.md`` (empty when it agrees)."""
    problems: list[str] = []
    claimed_round = re.search(r"(?i)round\s+(\d+)", header)
    fixed = re.search(r"(?i)fixed\s+(\d+)\s*/\s*(\d+)", header)
    dismissed = re.search(r"(?i)dismissed\s+(\d+)", header)
    states = record["states"]
    count = {(sev, st): sum(1 for s, t in states.values() if (s, t) == (sev, st))
             for sev in ("BLOCKER", "MAJOR") for st in ("fixed", "open")}
    if record["verdict"] != "READY TO LOCK":
        problems.append("the last round of audit.md is not READY TO LOCK")
    if claimed_round and int(claimed_round.group(1)) != record["round"]:
        problems.append(f"the line says round {claimed_round.group(1)}, audit.md has {record['round']}")
    if fixed and (int(fixed.group(1)), int(fixed.group(2))) != (
            count[("BLOCKER", "fixed")], count[("MAJOR", "fixed")]):
        problems.append(f"the line says fixed {fixed.group(1)}/{fixed.group(2)}, audit.md has "
                        f"{count[('BLOCKER', 'fixed')]}/{count[('MAJOR', 'fixed')]}")
    if dismissed and int(dismissed.group(1)) != sum(1 for _, t in states.values() if t == "dismissed"):
        problems.append("the dismissed count differs from audit.md")
    if count[("BLOCKER", "open")] or count[("MAJOR", "open")]:
        problems.append("audit.md still has an open BLOCKER or MAJOR")
    return problems


def audit_findings(sdd: Path, weights: dict[str, str]) -> list[dict]:
    """The spec-lock gate, as far as a file can show it. Only stages still open are looked at (a
    closed stage has its ``report.md``), so nothing is ever asked of work already finished.

    * ``lock_without_audit`` (note): a locked ``full`` stage with no ``Locked-by-audit:`` line.
    * ``lock_audit_mismatch`` (warn): that line disagrees with ``audit.md``, or ``audit.md`` is missing.
    * ``light_hits_audit_trigger`` (warn): a ``light`` stage touches a path the project listed under
      ``## Triggers`` in ``.sdd/audit-lenses.md``.
    """
    findings: list[dict] = []
    triggers = audit_triggers(sdd)
    for stage in _stage_dirs(sdd):
        spec = stage / "spec.md"
        if not spec.is_file() or (stage / "report.md").is_file():
            continue
        text = _read(spec)
        slug = stage.name.split("-", 1)[-1]
        weight = weights.get(stage.name) or weights.get(slug) or WEIGHT_FULL
        header = _LOCKED_BY_RE.search(text)
        if _LOCKED_RE.search(text) and weight == WEIGHT_FULL and not header:
            findings.append({"severity": "note", "code": "lock_without_audit", "stage": stage.name})
        if header:
            audit = stage / "audit.md"
            problems = _lock_mismatch(header.group(1), _audit_record(audit)) if audit.is_file() \
                else ["audit.md is missing"]
            if problems:
                findings.append({"severity": "warn", "code": "lock_audit_mismatch", "stage": stage.name,
                                 "detail": "; ".join(problems)})
        if weight == WEIGHT_LIGHT and triggers:
            touched = [p.strip() for line in _TOUCHES_PATHS_RE.findall(text)
                       for p in (_BACKTICKED_RE.findall(line) or line.split(","))
                       if re.search(r"[/*.]", p)]
            hit = next(((p, t) for p in touched for t in triggers if _paths_overlap(p, t)), None)
            if hit:
                findings.append({"severity": "warn", "code": "light_hits_audit_trigger",
                                 "stage": stage.name, "path": hit[0], "trigger": hit[1]})
    return findings


_SEPARATOR_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _stage_index_span(text: str) -> tuple[int, int] | None:
    """Offsets of section 5's body (canonical table and provisional queue) in the raw text."""
    match = _headings.find_heading(text, "stage_index", 2) or re.search(r"(?m)^##\s+5\.[^\n]*$", text)
    if not match:
        return None
    rest = text[match.end():]
    end = re.search(r"(?m)^#{1,2}\s", rest)
    return match.end(), match.end() + (end.start() if end else len(rest))


def _with_cell(raw: str, cell: str, pad_to: int) -> str:
    """``raw`` (a table line) with one more cell appended, padded to ``pad_to`` cells first."""
    body = raw.rstrip("\r\n")
    ending = raw[len(body):]
    body = body.rstrip()
    if not body.endswith("|"):
        body += " |"
    body += " |" * max(0, pad_to - len(_cells(body)))
    return f"{body} {cell} |{ending}" if cell else f"{body} |{ending}"


def add_weight_column(text: str) -> tuple[str, int]:
    """Append an empty ``Weight`` column to every stage table of section 5 that has none.

    Returns ``(new_text, tables_changed)``. Only tables with a ``Slug`` column are touched
    (the canonical index and the provisional queue); a table that already has ``Weight`` or
    ``Peso`` is left alone, so a second run changes nothing. Table-looking lines inside an HTML
    comment are skipped, rows keep their own line ending, and a short row is padded so the new
    cell lands in the new column. An empty cell reads as ``full``: no stage changes behaviour.
    """
    span = _stage_index_span(text)
    if not span:
        return text, 0
    start, end = span
    lines = text[start:end].splitlines(keepends=True)
    out: list[str] = []
    changed = 0
    in_comment = False
    i = 0
    while i < len(lines):
        line = lines[i]
        was_in_comment = in_comment
        for token in re.findall(r"<!--|-->", line):
            in_comment = token == "<!--"
        is_header = (not was_in_comment and not in_comment and line.lstrip().startswith("|")
                     and i + 1 < len(lines) and _SEPARATOR_RE.match(lines[i + 1]))
        header = [h.lower() for h in _cells(line)] if is_header else []
        if not (is_header and "slug" in header and "weight" not in header and "peso" not in header):
            out.append(line)
            i += 1
            continue

        out.append(_with_cell(line, "Weight", len(header)))
        sep = lines[i + 1]
        sep_body = sep.rstrip("\r\n")
        out.append(sep_body.rstrip() + "--------|" + sep[len(sep_body):])
        i += 2
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            out.append(_with_cell(lines[i], "", len(header)))
            i += 1
        changed += 1
    return text[:start] + "".join(out) + text[end:], changed


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
