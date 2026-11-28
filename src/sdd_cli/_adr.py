"""Architecture decision records (ADRs) as files of ``.sdd/decisions/``.

One file per record (``ADR-NNN-<slug>.md``), a small frontmatter, and a generated index
(``README.md``). The numbers come from the same lock and the same ledger that ``seq next`` uses,
so two sessions never receive the same id and a number is never handed out twice. Nothing here
overwrites a file the owner wrote: records are only created, and a record that a new one
supersedes has its *frontmatter* changed (never its body).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from . import _index_checks, _lock, _tracks

DECISIONS_DIR = "decisions"
INDEX_NAME = "README.md"
LEDGER_KEY = "adr"

PROPOSED, ACCEPTED, IMPLEMENTED, SUPERSEDED, OBSOLETE = (
    "proposta", "aceita", "implementada", "substituída", "obsoleta")
STATUSES = (PROPOSED, ACCEPTED, IMPLEMENTED, SUPERSEDED, OBSOLETE)
# Spellings that mean the same status: matched without accents and in lower case.
_STATUS_ALIASES = {"substituida": SUPERSEDED}

FIELDS = ("id", "status", "date", "stage", "decision", "supersedes", "superseded_by",
          "implemented_in", "reconstructed", "source")
LIST_FIELDS = ("supersedes", "superseded_by")

_LIST_ITEM_RE = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'|[^,]+")
_ID_RE = re.compile(r"ADR-(\d+)")
_FILE_RE = re.compile(r"ADR-(\d+)(?:-[a-z0-9-]*)?\.md\Z")
_DECISION_RE = re.compile(r"D-\d+\Z")
_TITLE_RE = re.compile(r"(?m)^#\s+(?:ADR-\d+\s*[—–:-]\s*)?(.+?)\s*$")

_BUNDLED_TEMPLATE = Path(__file__).parent / "content" / "sdd" / "templates" / "adr.template.md"
_FALLBACK_TEMPLATE = """# {{ID}} — {{TITLE}}

## Context

{{CONTEXT}}

## Decision

{{DECISION}}

## Alternatives considered

{{ALTERNATIVES}}

## Consequences

[What gets easier, what gets harder.]
"""
CONTEXT_PLACEHOLDER = "[Why this decision was needed: the forces at play.]"
DECISION_PLACEHOLDER = "[What was decided, in one or two sentences.]"
ALTERNATIVES_PLACEHOLDER = "- [Option A: why it was rejected]"


# ------------------------------------------------------------ frontmatter

def normalize_status(value: object) -> str | None:
    """The canonical status for ``value``, or ``None`` when it is outside the cycle."""
    if not isinstance(value, str):
        return None
    key = value.strip().casefold()
    for status in STATUSES:
        if key == status:
            return status
    plain = key.replace("í", "i").replace("é", "e").replace("ã", "a").replace("ç", "c")
    return _STATUS_ALIASES.get(plain) or next(
        (s for s in STATUSES if s.replace("í", "i") == plain), None)


def _scalar(value: str) -> object:
    value = value.strip()
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        return value[1:-1].replace("''", "'")
    if value.startswith("["):
        # a flow list: items may be quoted and may hold commas; a trailing comment is dropped
        closing = value.rfind("]")
        inner = value[1:closing].strip() if closing > 0 else value[1:].strip()
        items = _LIST_ITEM_RE.findall(inner)
        return [str(_scalar(part)) for part in items if part.strip()]
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()  # `aceita  # note` is `aceita`
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    return value


def _format(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_format(str(v)) for v in value) + "]"
    text = str(value)
    if text == "":
        return ""
    if (text != text.strip() or text[0] in "\"'[#&*!|>%@`" or ": " in text or " #" in text
            or text.lower() in ("true", "false")):
        return json.dumps(text, ensure_ascii=False)
    return text


def split(text: str) -> tuple[dict, str, str] | None:
    """``(meta, frontmatter_block, body)`` of an ADR text (LF), or ``None`` when it has no frontmatter."""
    match = re.match(r"---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", text, re.S)
    if not match:
        return None
    meta: dict = {}
    for line in match.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep and key.strip():
            meta[key.strip()] = _scalar(value)
    return meta, match.group(0), text[match.end():]


def render_frontmatter(meta: dict) -> str:
    keys = [k for k in FIELDS if k in meta] + [k for k in meta if k not in FIELDS]
    lines = [f"{k}: {_format(meta[k])}".rstrip() for k in keys]
    return "---\n" + "\n".join(lines) + "\n---\n"


def set_meta(text: str, updates: dict) -> str:
    """``text`` with ``updates`` merged into its frontmatter and the body left exactly as it was."""
    parsed = split(text)
    if not parsed:
        raise ValueError("record has no frontmatter")
    meta, block, body = parsed
    meta = {**meta, **updates}
    return render_frontmatter(meta) + body


def update_frontmatter(text: str, updates: dict) -> str:
    """``text`` (LF) with only the lines of ``updates`` changed inside the frontmatter: every other
    line, comment and the whole body stay as the owner wrote them. A key that is missing is added
    before the closing ``---``."""
    match = re.match(r"(---[ \t]*\n)(.*?)(\n---[ \t]*(?:\n|\Z))", text, re.S)
    if not match:
        raise ValueError("record has no frontmatter")
    lines = match.group(2).split("\n")
    for key, value in updates.items():
        new = f"{key}: {_format(value)}".rstrip()
        for index, line in enumerate(lines):
            if re.match(rf"{re.escape(key)}\s*:", line):
                lines[index] = new
                break
        else:
            lines.append(new)
    return match.group(1) + "\n".join(lines) + match.group(3) + text[match.end():]


# ------------------------------------------------------------------ files

@dataclass
class Adr:
    path: Path
    number: int | None
    meta: dict = field(default_factory=dict)
    body: str = ""
    error: str | None = None

    @property
    def id(self) -> str:
        declared = self.meta.get("id")
        if isinstance(declared, str) and declared.strip():
            return declared.strip()
        return f"ADR-{self.number:03d}" if self.number is not None else self.path.stem

    @property
    def title(self) -> str:
        match = _TITLE_RE.search(self.body)
        return match.group(1).strip() if match else self.path.stem

    @property
    def status(self) -> str:
        return str(self.meta.get("status", "")).strip()


def decisions_dir(root: Path) -> Path:
    return root / ".sdd" / DECISIONS_DIR


def _read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig", errors="replace").replace("\r\n", "\n")  # a BOM is not content


def list_adrs(root: Path) -> list[Adr]:
    """Every ``ADR-*.md`` of ``.sdd/decisions/`` in number order (the index is not one)."""
    directory = decisions_dir(root)
    if not directory.is_dir():
        return []
    found = []
    for path in directory.glob("ADR-*.md"):
        match = _FILE_RE.match(path.name)
        number = int(match.group(1)) if match else None
        record = Adr(path=path, number=number)
        parsed = split(_read_text(path))
        if parsed:
            record.meta, _, record.body = parsed
        else:
            record.error = "no frontmatter"
            record.body = _read_text(path)
        found.append(record)
    return sorted(found, key=lambda r: (r.number is None, r.number or 0, r.path.name))


def slugify(title: str) -> str:
    plain = (title.casefold().replace("ç", "c").replace("ã", "a").replace("õ", "o")
             .replace("á", "a").replace("à", "a").replace("â", "a").replace("é", "e")
             .replace("ê", "e").replace("í", "i").replace("ó", "o").replace("ô", "o")
             .replace("ú", "u"))
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")[:60].strip("-") or "decision"


def adr_id(number: int) -> str:
    return f"ADR-{number:03d}"


# -------------------------------------------------------------- numbering

def _used_numbers(root: Path) -> list[int]:
    used = []
    directory = decisions_dir(root)
    if directory.is_dir():
        for path in directory.glob("ADR-*.md"):
            match = _FILE_RE.match(path.name)
            if match:
                used.append(int(match.group(1)))
    for item in _tracks._read_ledger(root).get("sequences", {}).get(LEDGER_KEY, []):
        if str(item.get("number", "")).isdigit():
            used.append(int(item["number"]))
    return used


def peek_number(root: Path) -> int:
    """The number ``reserve_number`` would hand out now; nothing is recorded."""
    return max(_used_numbers(root), default=0) + 1


def reserve_number(root: Path) -> int:
    """Hand out the next number under the shared lock and record it, so it is never reused."""
    with _lock.file_lock(root / ".sdd" / _tracks.LOCK_NAME):
        ledger = _tracks._read_ledger(root)
        number = max(_used_numbers(root), default=0) + 1
        ledger.setdefault("sequences", {}).setdefault(LEDGER_KEY, []).append(
            {"number": f"{number:03d}", "track": None})
        _tracks._write_json(root / ".sdd" / _tracks.LEDGER_NAME, ledger)
    return number


# ------------------------------------------------------------------ index

def render_index(root: Path) -> str:
    """The generated ``README.md`` of ``.sdd/decisions/``: id, title, status, decision, stage, date."""
    lines = ["# Decision records", "",
             "<!-- Generated by `sddkit adr index` from the frontmatter of the files in this folder. "
             "Do not edit by hand: the next run overwrites it. -->", ""]
    records = list_adrs(root)
    if not records:
        lines.append("No records yet. `sddkit adr new \"<title>\"` creates the first one.")
    else:
        lines += ["| ID | Title | Status | Decision | Stage | Date |",
                  "|----|-------|--------|----------|-------|------|"]
        for r in records:
            meta = r.meta
            cell = _index_checks.cell_text
            lines.append(f"| [{r.id}]({r.path.name}) | {cell(r.title)} | {cell(r.status)} | "
                         f"{cell(str(meta.get('decision', '')))} | {cell(str(meta.get('stage', '')))} | "
                         f"{cell(str(meta.get('date', '')))} |")
    return "\n".join(lines) + "\n"


def index_is_stale(root: Path) -> bool:
    """``True`` when ``README.md`` differs from what the frontmatter says (a missing index counts)."""
    path = decisions_dir(root) / INDEX_NAME
    if not path.is_file():
        return bool(list_adrs(root))
    return _read_text(path) != render_index(root)


def write_index(root: Path) -> bool:
    """Regenerate the index; returns ``False`` (and writes nothing) when it is already current."""
    path = decisions_dir(root) / INDEX_NAME
    text = render_index(root)
    if path.is_file() and _read_text(path) == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return True


# ----------------------------------------------------------------- create

def _template(root: Path) -> str:
    for candidate in (root / ".sdd" / "templates" / "adr.template.md", _BUNDLED_TEMPLATE):
        if candidate.is_file():
            return _read_text(candidate)
    return _FALLBACK_TEMPLATE


def render_body(root: Path, record_id: str, title: str, context: str, alternatives: list[str],
                decision_text: str = "") -> str:
    """The body of a new record from the project's template (or the bundled one)."""
    text = re.sub(r"\A(?:\s*<!--.*?-->)+\s*", "", _template(root), flags=re.S)
    options = "\n".join(a if a.lstrip().startswith(("-", "*")) else f"- {a}" for a in alternatives)
    for key, value in (("{{ID}}", record_id), ("{{TITLE}}", title),
                       ("{{DECISION}}", decision_text.strip() or DECISION_PLACEHOLDER),
                       ("{{CONTEXT}}", context.strip() or CONTEXT_PLACEHOLDER),
                       ("{{ALTERNATIVES}}", options or ALTERNATIVES_PLACEHOLDER)):
        text = text.replace(key, value)
    return text.rstrip("\n") + "\n"


def link_for(record: Adr) -> str:
    """The §3 ``Record`` cell for a record: a link relative to the constitution."""
    return f"[{record.id}]({DECISIONS_DIR}/{record.path.name})"


def _check_new(root: Path, *, title: str, status: str | None, decision: str,
               supersedes: list[str]) -> str:
    if not title.strip():
        raise ValueError("an ADR needs a title")
    canonical = normalize_status(status)
    if canonical is None:
        raise ValueError(f"status {status!r} is outside the cycle: " + ", ".join(STATUSES))
    if decision and not _DECISION_RE.match(decision):
        raise ValueError(f"--decision must look like D-001, not {decision!r}")
    known = {r.id: r for r in list_adrs(root)}
    for old in supersedes:
        if not _ID_RE.fullmatch(old):
            raise ValueError(f"--supersedes must look like ADR-001, not {old!r}")
        if old not in known:
            raise ValueError(f"{old} does not exist in .sdd/decisions/")
        # checked before a number is reserved: the old record is rewritten, so it must be readable
        try:
            text = known[old].path.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValueError(f"{known[old].path.name} is not valid UTF-8; convert it before superseding it") from None
        if not split(text.replace("\r\n", "\n")):
            raise ValueError(f"{known[old].path.name} has no frontmatter; add `status:` and `superseded_by:` first")
    return canonical


def decision_section(choice: str, rationale: str) -> str:
    """The Decision section of a record made from a §3 row or a discovery decision: what the
    row says, and nothing else (empty when it says nothing)."""
    text = choice.strip()
    if rationale.strip():
        text += ("\n\n" if text else "") + f"Rationale: {rationale.strip()}"
    return text


def render_record(meta: dict, body: str) -> str:
    return render_frontmatter(meta) + "\n" + body.lstrip("\n")


def claim_numbers(root: Path, numbers: list[int]) -> None:
    """Record numbers in the ledger so they are never handed out again. The caller holds the lock."""
    ledger = _tracks._read_ledger(root)
    entries = ledger.setdefault("sequences", {}).setdefault(LEDGER_KEY, [])
    known = {int(e["number"]) for e in entries if str(e.get("number", "")).isdigit()}
    added = [n for n in sorted(set(numbers)) if n not in known]
    entries.extend({"number": f"{n:03d}", "track": None} for n in added)
    if added:
        _tracks._write_json(root / ".sdd" / _tracks.LEDGER_NAME, ledger)


def write_new_file(path: Path, content: str) -> bool:
    """Create ``path`` with LF endings; ``False`` (nothing written) when it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError:
        return False
    return True


def new_adr(root: Path, title: str, *, decision: str = "", stage: str = "", status: str = PROPOSED,
            supersedes: list[str] | None = None, context: str = "",
            alternatives: list[str] | None = None, reconstructed: bool = False, source: str = "",
            implemented_in: str = "", date: str | None = None, decision_text: str = "",
            dry_run: bool = False) -> dict:
    """Create one record (and regenerate the index). With ``dry_run`` nothing is reserved or written.

    A record that this one ``supersedes`` gets ``status: substituída`` and ``superseded_by``
    in its frontmatter; its body is not touched.
    """
    supersedes = list(supersedes or [])
    status = _check_new(root, title=title, status=status, decision=decision, supersedes=supersedes)
    number = peek_number(root) if dry_run else reserve_number(root)
    record_id = adr_id(number)
    meta = {"id": record_id, "status": status, "date": date or datetime.now(UTC).date().isoformat(),
            "stage": stage, "decision": decision, "supersedes": supersedes, "superseded_by": [],
            "implemented_in": implemented_in, "reconstructed": reconstructed, "source": source}
    content = render_record(meta, render_body(root, record_id, title.strip(), context, alternatives or [],
                                              decision_text))
    path = decisions_dir(root) / f"{record_id}-{slugify(title)}.md"
    result = {"id": record_id, "path": path.relative_to(root).as_posix(), "status": status,
              "superseded": supersedes, "dry_run": dry_run, "content": content,
              "created_directory": not decisions_dir(root).is_dir()}
    if dry_run:
        return result
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    for old_id in supersedes:
        old = next(r for r in list_adrs(root) if r.id == old_id)
        original = old.path.read_bytes()
        backup = root / ".sdd" / ".pre-fix-backup" / stamp / DECISIONS_DIR / old.path.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_bytes(original)
        raw = original.decode("utf-8")
        bom = "﻿" if raw.startswith("﻿") else ""
        raw = raw.removeprefix("﻿")
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        current = split(text)[0].get("superseded_by", [])
        successors = [*(current if isinstance(current, list) else [current]), record_id]
        updated = update_frontmatter(text, {"status": SUPERSEDED, "superseded_by": successors})
        old.path.write_bytes((bom + (updated.replace("\n", "\r\n") if crlf else updated)).encode("utf-8"))
    write_index(root)
    return result
