"""Collect improvement proposals from several projects into one local inbox.

Each project keeps its own ``.sdd/improvement-proposals.md``; nothing in the kit
reads them across projects. ``collect`` copies every ``## IP-NNN`` entry into a
user-level inbox, one file per entry, and never writes to the source project.
Entry ids restart at ``IP-001`` in every project, so identity is the pair
(project, id); the content hash only tells whether an entry was edited.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path

PROPOSALS_FILE = Path(".sdd") / "improvement-proposals.md"
INBOX_ENV = "SDD_PROPOSALS_INBOX"
_APP_DIR = Path("sdd-cli") / "proposals"
_SKIP_DIRS = {"node_modules", "__pycache__"}

# Any level-2 heading ends an entry (``## Resolvidas`` is not one); ``###`` stays in the body.
_HEADING_RE = re.compile(r"(?m)^##(?!#)[ \t]*(.*)$")
_ENTRY_RE = re.compile(r"^(IP-\d+)\s*[—–-]*\s*(.*)$")
_FIELDS = {"date": "Data", "status": "Status", "phase": "Fase afetada"}
_HASH_RE = re.compile(r"(?m)^sha256:\s*([0-9a-f]+)\s*$")
CODES_FILE = ".codes.json"


# ------------------------------------------------------------------ parse

def _field(body: str, label: str) -> str | None:
    """Value of ``- **label:** ...``, joined with its indented continuation lines."""
    match = re.search(rf"(?m)^-\s*\*\*{re.escape(label)}:\*\*[ \t]*(.*(?:\n[ \t]+\S.*)*)", body)
    if not match:
        return None
    return " ".join(part.strip() for part in match.group(1).splitlines()) or None


def parse(text: str) -> list[dict]:
    """Entries in file order. Only the ``## IP-NNN`` heading is required."""
    text = text.replace("\r\n", "\n")
    headings = list(_HEADING_RE.finditer(text))
    entries: list[dict] = []
    for index, heading in enumerate(headings):
        match = _ENTRY_RE.match(heading.group(1).strip())
        if not match:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.start():end].rstrip() + "\n"
        entry = {"id": match.group(1), "title": match.group(2).strip(), "body": body,
                 "hash": hashlib.sha256(body.encode("utf-8")).hexdigest()}
        for key, label in _FIELDS.items():
            entry[key] = _field(body, label)
        entries.append(entry)
    return entries


# ------------------------------------------------------------------ inbox

def inbox_dir(env: Mapping[str, str] | None = None, platform: str | None = None) -> Path:
    """Where collected proposals live: the environment override, else the user's
    data folder. Standard library only (the kit has no ``platformdirs``)."""
    env = os.environ if env is None else env
    platform = sys.platform if platform is None else platform
    if env.get(INBOX_ENV):
        return Path(env[INBOX_ENV])
    if platform == "win32":
        base = Path(env["APPDATA"]) if env.get("APPDATA") else Path.home() / "AppData" / "Roaming"
    elif platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(env["XDG_DATA_HOME"]) if env.get("XDG_DATA_HOME") else Path.home() / ".local" / "share"
    return base / _APP_DIR


def _stored_hash(path: Path) -> str | None:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:400]
    except OSError:
        return None
    match = _HASH_RE.search(head)
    return match.group(1) if match else None


def _render(code: str, entry: dict) -> str:
    return f"---\nproject: {code}\nid: {entry['id']}\nsha256: {entry['hash']}\n---\n\n{entry['body']}"


def _write(path: Path, text: str) -> None:
    """Write atomically so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


# ---------------------------------------------------------------- collect

def scan(root: Path) -> list[Path]:
    """Every folder under ``root`` (itself included) that has a ``.sdd/`` directory."""
    found: list[Path] = []
    for current, dirs, _ in os.walk(root):
        if (Path(current) / ".sdd").is_dir():
            found.append(Path(current))
            dirs[:] = []  # a project's own subfolders are not separate projects
            continue
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in _SKIP_DIRS)
    return sorted(found)


def read_codes(inbox: Path) -> dict[str, str]:
    """Anonymous code (``P1``, ``P2``...) of each project, kept only in the inbox."""
    try:
        data = json.loads((inbox / CODES_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _next_code(codes: Mapping[str, str]) -> str:
    used = [int(c[1:]) for c in codes.values() if re.fullmatch(r"P\d+", c)]
    return f"P{max(used, default=0) + 1}"


def aliases(entries: list[dict], inbox: Path) -> dict[str, str]:
    """Anonymous code for every project in ``entries``. Codes already recorded
    in the inbox win; a project it never saw (files copied in by hand) gets the
    next free one, in name order, without writing anything."""
    codes = read_codes(inbox)
    for project in sorted({e["project"] for e in entries}, key=str.lower):
        if project not in codes:
            codes[project] = _next_code(codes)
    return {project: codes[project] for project in {e["project"] for e in entries}}


def collect(projects: list[Path], inbox: Path) -> dict:
    """Copy each project's entries into ``inbox`` as ``<project>-IP-NNN.md``.

    The project code is its folder name. A new entry is created, an edited one
    (different hash) is rewritten, an identical one is left alone, and an entry
    that disappeared from its source is never removed from the inbox.
    """
    codes = [project.name for project in projects]
    clashes = sorted({code for code in codes if codes.count(code) > 1})
    if clashes:
        raise ValueError(f"same project code for different folders: {', '.join(clashes)}")
    result = {"inbox": str(inbox), "projects": [], "created": 0, "updated": 0, "unchanged": 0}
    known = read_codes(inbox)
    anonymous = dict(known)
    for project, code in zip(projects, codes, strict=True):
        source = project / PROPOSALS_FILE
        report = {"project": code, "source": None, "entries": 0,
                  "created": 0, "updated": 0, "unchanged": 0, "warnings": [], "note": None}
        result["projects"].append(report)
        if not source.is_file():
            # A note, never an error: the project may simply have registered no friction. The
            # name is exact on purpose, so a misspelt file (improvements-proposals.md) shows up here.
            report["note"] = f"no {PROPOSALS_FILE.as_posix()} (nothing registered, or a different file name)"
            continue
        report["source"] = PROPOSALS_FILE.as_posix()
        seen: set[str] = set()
        found = parse(source.read_text(encoding="utf-8", errors="replace"))
        if found and code not in anonymous:
            anonymous[code] = _next_code(anonymous)
        for entry in found:
            if entry["id"] in seen:
                report["warnings"].append(f"{entry['id']} appears more than once; kept the first")
                continue
            seen.add(entry["id"])
            report["entries"] += 1
            target = inbox / f"{code}-{entry['id']}.md"
            if not target.is_file():
                outcome = "created"
            elif _stored_hash(target) != entry["hash"]:
                outcome = "updated"
            else:
                outcome = "unchanged"
            if outcome != "unchanged":
                _write(target, _render(code, entry))
            report[outcome] += 1
            result[outcome] += 1
    if anonymous != known:
        _write(inbox / CODES_FILE, json.dumps(anonymous, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return result


# ------------------------------------------------------------ list / show

_FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_PROJECT_RE = re.compile(r"(?m)^project:[ \t]*(.+?)[ \t]*$")
_STATUS_WORDS = ("absorvida pelo kit", "contorno local", "aberta", "proposta")


def status_keyword(status: str | None) -> str:
    """Leading keyword of the free-text ``Status``; any text is accepted."""
    text = (status or "").strip().lower()
    for word in _STATUS_WORDS:
        if text.startswith(word):
            return word
    return text.split()[0].strip("(.,;:") if text else ""


def is_absorbed(entry: dict) -> bool:
    return status_keyword(entry["status"]) == "absorvida pelo kit"


def load(inbox: Path) -> list[dict]:
    """Every entry in ``inbox``, ordered by project then id. Reads only; a file
    that is not one of ours (no front matter or no entry) is skipped."""
    if not inbox.is_dir():
        return []
    loaded: list[dict] = []
    for path in inbox.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        except OSError:
            continue
        front = _FRONT_RE.match(text)
        project = _PROJECT_RE.search(front.group(1)) if front else None
        entries = parse(text[front.end():]) if front else []
        if not project or not entries:
            continue
        entry = entries[0]
        entry["project"] = project.group(1)
        entry["key"] = f"{entry['project']}-{entry['id']}"
        loaded.append(entry)
    loaded.sort(key=lambda e: (e["project"].lower(), int(e["id"][3:])))
    return loaded


def find(entries: list[dict], token: str) -> list[dict]:
    """Entries named by ``token``: the qualified ``P1-IP-001`` (one match at
    most), or a bare ``IP-001``, which matches once per project that has it."""
    wanted = token.strip().lower()
    exact = [e for e in entries if e["key"].lower() == wanted]
    return exact or [e for e in entries if e["id"].lower() == wanted]
