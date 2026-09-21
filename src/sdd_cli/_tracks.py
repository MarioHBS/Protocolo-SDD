"""Declarative safety checks and atomic bookkeeping for shared-tree tracks.

Parallel tracks share one working tree, so nothing physical keeps two sessions
apart. This module makes the separation *checkable*: every track declares a
footprint (paths, exclusive runtime resources, shared numeric sequences) in
``tracks/<slug>/claims.json``, ``check`` refuses overlapping footprints,
``verify`` compares the real Git changes with the claims, ``reserve_sequence``
and ``incorporate`` hand out shared numbers under a lock so two sessions can
never take the same one.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from . import _lock, _user_files

LOCK_NAME = ".lock"
LEDGER_NAME = ".reservations.json"
_WILDCARDS = "*?["


# ------------------------------------------------------------------ claims

def claims_path(root: Path, slug: str) -> Path:
    return root / ".sdd" / "tracks" / slug / "claims.json"


def load(root: Path, slug: str) -> dict:
    path = claims_path(root, slug)
    if not path.is_file():
        return {"version": 1, "track": slug, "claims": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid claims for track {slug}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ValueError(f"invalid claims for track {slug}: claims must be a list")
    return data


def _write_json(path: Path, data: dict) -> None:
    """Write atomically so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def save(root: Path, slug: str, data: dict) -> None:
    _write_json(claims_path(root, slug), data)


def active_tracks(root: Path) -> list[str]:
    """Tracks whose footprint still counts: on disk and, when the constitution
    lists active tracks, present in that table (concluded tracks are dropped)."""
    directory = root / ".sdd" / "tracks"
    if not directory.is_dir():
        return []
    on_disk = sorted(p.name for p in directory.iterdir() if p.is_dir() and not p.name.startswith("."))
    listed = _user_files.active_track_slugs(root / ".sdd")
    return [name for name in on_disk if listed is None or name in listed]


# ---------------------------------------------------------- glob overlap

def _normal(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _has_glob(text: str) -> bool:
    return any(char in text for char in _WILDCARDS)


def _glob_regex(glob: str) -> re.Pattern[str]:
    """``**`` crosses directories, ``*`` and ``?`` do not."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
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
    return re.compile("".join(out) + r"\Z")


def _matches(path: str, glob: str) -> bool:
    return bool(_glob_regex(glob).match(path))


def _segment_compatible(left: str, right: str) -> bool:
    """Could two single path segments (either may be a wildcard) name the same entry?"""
    if not _has_glob(left) and not _has_glob(right):
        return left == right
    if not _has_glob(left):
        return fnmatch.fnmatchcase(left, right)
    if not _has_glob(right):
        return fnmatch.fnmatchcase(right, left)
    return True  # two wildcard segments: assume they can meet


def _can_start(prefix: list[str], glob: list[str]) -> bool:
    """Can ``glob`` match some path that begins with the segments in ``prefix``?"""
    if not prefix:
        return True
    if not glob:
        return False
    if glob[0] == "**":
        return len(glob) == 1 or _can_start(prefix, glob[1:]) or _can_start(prefix[1:], glob)
    return fnmatch.fnmatchcase(prefix[0], glob[0]) and _can_start(prefix[1:], glob[1:])


def _looks_like_file(path: str) -> bool:
    return "." in path.rsplit("/", 1)[-1]


def _overlap(left: str, right: str) -> bool:
    """Conservative: may report an overlap that is not real, never hides one.

    Two literal paths overlap when they are equal or one is a directory above
    the other. A literal and a glob overlap when the literal matches the glob or
    (for a directory) the glob can match something beneath it. Two globs overlap
    unless their segments already disagree before any ``**``.
    """
    left, right = _normal(left), _normal(right)
    if left == right:
        return True
    left_glob, right_glob = _has_glob(left), _has_glob(right)
    if not left_glob and not right_glob:
        return left.startswith(right + "/") or right.startswith(left + "/")
    if not left_glob or not right_glob:
        literal, glob = (left, right) if not left_glob else (right, left)
        if _matches(literal, glob):
            return True
        return not _looks_like_file(literal) and _can_start(literal.split("/"), glob.split("/"))
    lsegs, rsegs = left.split("/"), right.split("/")
    for lseg, rseg in zip(lsegs, rsegs, strict=False):
        if lseg == "**" or rseg == "**":
            return _segment_compatible(lsegs[-1], rsegs[-1])
        if not _segment_compatible(lseg, rseg):
            return False
    return True


def check(root: Path) -> list[dict]:
    claims: list[tuple[str, dict]] = []
    for slug in active_tracks(root):
        for claim in load(root, slug)["claims"]:
            claims.append((slug, claim))
    conflicts: list[dict] = []
    for index, (left_slug, left) in enumerate(claims):
        for right_slug, right in claims[index + 1:]:
            if left_slug == right_slug:
                continue
            for path_a in left.get("paths", []):
                for path_b in right.get("paths", []):
                    if _overlap(path_a, path_b):
                        conflicts.append({"kind": "path", "tracks": [left_slug, right_slug],
                                          "paths": [path_a, path_b]})
            for value in sorted(set(left.get("sequences", [])) & set(right.get("sequences", []))):
                conflicts.append({"kind": "sequence", "tracks": [left_slug, right_slug], "value": value})
            for value in sorted(set(left.get("runtime", [])) & set(right.get("runtime", []))):
                conflicts.append({"kind": "runtime", "tracks": [left_slug, right_slug], "value": value})
            if (left.get("stability_sensitive") or right.get("stability_sensitive")) \
                    and (left.get("paths") or right.get("paths")):
                conflicts.append({"kind": "stability", "tracks": [left_slug, right_slug]})
    return conflicts


def claimed_paths(root: Path, slug: str) -> list[str]:
    paths: list[str] = []
    for claim in load(root, slug)["claims"]:
        paths.extend(_normal(path) for path in claim.get("paths", []))
    return paths


# ------------------------------------------------------------------- git

def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True,
                              check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot run git {' '.join(args)}: {exc}") from exc


def current_branch(root: Path) -> str | None:
    """Current branch name, or ``None`` outside a repo / on a detached HEAD."""
    try:
        name = _git(root, "branch", "--show-current").strip()
    except ValueError:
        return None
    return name or None


def changed_files(root: Path, since: str | None = None) -> list[str]:
    """Files changed in the working tree (or since a revision), untracked included."""
    if since:
        names = _git(root, "diff", "--name-only", since).splitlines()
        names += _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
        return sorted({_normal(name) for name in names if name})
    entries = _git(root, "status", "--porcelain", "-z", "-uall").split("\0")
    names: list[str] = []
    skip = False
    for entry in entries:
        if skip:  # second half of a rename/copy: the original path
            skip = False
            continue
        if len(entry) < 4:
            continue
        if entry[0] in "RC" or entry[1] in "RC":
            skip = True
        names.append(_normal(entry[3:]))
    return sorted(set(names))


def verify(root: Path, slug: str, since: str | None = None) -> list[dict]:
    """Compare real changes with every active track's claims.

    * a changed file that no track claims is ``track_unclaimed_touch``;
    * a changed file claimed by two tracks is ``track_shared_touch`` (error).
    A file claimed only by *another* track is that track's work and is ignored.
    SDD bookkeeping under ``.sdd/`` is always allowed.
    """
    claims = {name: claimed_paths(root, name) for name in active_tracks(root)}
    if not claims.get(slug):
        return [{"kind": "track_unclaimed_touch", "path": "*", "track": slug,
                 "detail": "track has no path claims"}]
    findings: list[dict] = []
    for name in changed_files(root, since):
        if name == ".sdd" or name.startswith(".sdd/"):
            continue
        owners = sorted(t for t, patterns in claims.items()
                        if any(_matches(name, p) or name.startswith(p + "/") for p in patterns))
        if not owners:
            findings.append({"kind": "track_unclaimed_touch", "path": name, "track": slug})
        elif len(owners) > 1:
            findings.append({"kind": "track_shared_touch", "path": name, "tracks": owners})
    return findings


# ------------------------------------------------------------- sequences

_DEFAULT_SEQUENCES = {"migration": "supabase/migrations/NNNN_*.sql"}
_DECLARED_RE = re.compile(r"`([A-Za-z][\w-]*)`\s*=\s*`([^`\n]*N{2,}[^`\n]*)`")


def sequences(root: Path) -> dict[str, str]:
    """Shared numeric sequences: declared in the constitution as
    ``` `name` = `dir/NNNN_*.ext` ``` or, failing that, the default migration
    layout when ``supabase/migrations`` exists."""
    declared: dict[str, str] = {}
    constitution = root / ".sdd" / "constitution.md"
    if constitution.is_file():
        text = constitution.read_text(encoding="utf-8", errors="replace")
        declared = {name: pattern for name, pattern in _DECLARED_RE.findall(text)}
    if not declared and (root / "supabase" / "migrations").is_dir():
        declared = dict(_DEFAULT_SEQUENCES)
    return declared


def _sequence_files(root: Path, pattern: str) -> list[tuple[int, int, Path]]:
    """(number, width, file) for every file that matches the sequence pattern."""
    directory_part, _, file_part = pattern.rpartition("/")
    marker = re.search(r"N{2,}", file_part)
    if not marker:
        return []
    regex = re.compile(
        re.escape(file_part[:marker.start()]) + r"(\d+)"
        + re.escape(file_part[marker.end():]).replace(r"\*", ".*") + r"\Z")
    directory = root / directory_part if directory_part else root
    found = []
    for path in sorted(directory.glob("*")) if directory.is_dir() else []:
        match = regex.match(path.name)
        if match and path.is_file():
            found.append((int(match.group(1)), len(match.group(1)), path))
    return found


def duplicate_numbers(root: Path) -> list[dict]:
    """Numbers used by more than one file in a declared sequence."""
    findings = []
    for name, pattern in sequences(root).items():
        files = _sequence_files(root, pattern)
        counts = Counter(number for number, _, _ in files)
        for number, count in sorted(counts.items()):
            if count > 1:
                findings.append({"sequence": name, "number": number,
                                 "files": [str(p.relative_to(root)).replace("\\", "/")
                                           for n, _, p in files if n == number]})
    return findings


def _read_ledger(root: Path) -> dict:
    path = root / ".sdd" / LEDGER_NAME
    if not path.is_file():
        return {"version": 1, "sequences": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid reservation ledger: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("invalid reservation ledger: expected an object")
    return data


def reserve_sequence(root: Path, name: str, track: str | None = None) -> dict:
    """Reserve the next number of a shared sequence in a user-owned ledger."""
    declared = sequences(root)
    if name not in declared:
        known = ", ".join(sorted(declared)) or "none declared"
        raise ValueError(f"unknown sequence: {name} (known: {known})")
    files = _sequence_files(root, declared[name])
    width = max([w for _, w, _ in files], default=4)
    with _lock.file_lock(root / ".sdd" / LOCK_NAME):
        ledger = _read_ledger(root)
        entries = ledger.setdefault("sequences", {}).setdefault(name, [])
        reserved = [int(item["number"]) for item in entries if str(item.get("number", "")).isdigit()]
        number = max([n for n, _, _ in files] + reserved, default=0) + 1
        record = {"number": f"{number:0{width}d}", "track": track or None}
        entries.append(record)
        _write_json(root / ".sdd" / LEDGER_NAME, ledger)
    return record


# ---------------------------------------------------------- incorporation

_ROW_NUMBER_RE = re.compile(r"(?m)^\|\s*(\d{3,})(?:-[A-Za-z])?\s*\|")
_LOCAL_PREFIX_RE = re.compile(r"^\d+(?:-[A-Za-z])?-")


def _stage_index_span(text: str) -> tuple[int, int] | None:
    """Character span of the canonical stage table's last row (insertion point)."""
    heading = re.search(r"(?m)^##\s+5\.[^\n]*$", text)
    if not heading:
        return None
    rest = text[heading.end():]
    end = re.search(r"(?m)^(?:###\s+Provisional|##\s)", rest)
    region_end = heading.end() + (end.start() if end else len(rest))
    last = None
    for row in re.finditer(r"(?m)^\|.*\|[ \t]*$", text[heading.end():region_end]):
        last = row
    if not last:
        return None
    return heading.end() + last.start(), heading.end() + last.end()


def next_stage_number(root: Path) -> int:
    """Next free canonical ``NNN``: highest on disk, in §5 or in the ledger, plus one."""
    sdd = root / ".sdd"
    used = [int(m.group(1)) for p in (sdd / "stages").glob("*")
            if p.is_dir() and (m := re.match(r"(\d+)", p.name))] if (sdd / "stages").is_dir() else []
    constitution = sdd / "constitution.md"
    if constitution.is_file():
        used += [int(n) for n in _ROW_NUMBER_RE.findall(constitution.read_text(encoding="utf-8", errors="replace"))]
    for item in _read_ledger(root).get("sequences", {}).get("stage", []):
        if str(item.get("number", "")).isdigit():
            used.append(int(item["number"]))
    return max(used, default=0) + 1


def _index_row(header: str, existing: str, number: int, slug: str, folder: str) -> str:
    cells = [c.strip() for c in header.strip().strip("|").split("|")]
    done = Counter(m.group(0) for m in re.finditer(r"(?i)\b(?:done|conclu[ií]d[ao])\b", existing))
    status = done.most_common(1)[0][0] if done else "done"
    values = []
    for cell in cells:
        low = cell.lower()
        if low.startswith(("stage", "etapa")):
            values.append(f"{number:03d}")
        elif low.startswith("slug"):
            values.append(slug)
        elif low.startswith("status"):
            values.append(status)
        elif low.startswith("spec"):
            values.append(f"[spec](stages/{folder}/spec.md)")
        elif low.startswith(("report", "relat")):
            values.append(f"[report](stages/{folder}/report.md)")
        else:
            values.append("")
    return "| " + " | ".join(values) + " |"


def incorporate(root: Path, slug: str, stage_dir: Path, *, dry_run: bool = False) -> dict:
    """Move a closed track stage into the canonical queue atomically.

    Under one lock: pick the next free ``NNN``, rename the folder, append the
    row to §5, release the stage's claims and record the number.
    """
    sdd = root / ".sdd"
    constitution = sdd / "constitution.md"
    local = stage_dir.name
    if not (stage_dir / "report.md").is_file():
        raise ValueError(f"stage {local} has no report.md; close it before incorporating")
    if not constitution.is_file():
        raise ValueError("no .sdd/constitution.md found")
    stage_slug = _LOCAL_PREFIX_RE.sub("", local)
    with _lock.file_lock(sdd / LOCK_NAME):
        number = next_stage_number(root)
        folder = f"{number:03d}-{stage_slug}"
        target = sdd / "stages" / folder
        if target.exists():
            raise ValueError(f"target already exists: stages/{folder}")
        raw = constitution.read_bytes().decode("utf-8")
        crlf = "\r\n" in raw
        text = raw.replace("\r\n", "\n")
        span = _stage_index_span(text)
        if span is None:
            raise ValueError("no stage table found in constitution section 5")
        table_start = text.rfind("\n\n", 0, span[0]) + 2
        header = text[table_start:text.index("\n", table_start)]
        row = _index_row(header, text[table_start:span[1]], number, stage_slug, folder)
        result = {"track": slug, "from": f".sdd/tracks/{slug}/stages/{local}",
                  "to": f".sdd/stages/{folder}", "number": f"{number:03d}", "row": row,
                  "dry_run": dry_run}
        if dry_run:
            return result
        (sdd / "stages").mkdir(exist_ok=True)
        shutil.move(str(stage_dir), str(target))
        updated = text[:span[1]] + "\n" + row + text[span[1]:]
        if crlf:
            updated = updated.replace("\n", "\r\n")
        tmp = constitution.with_name(constitution.name + ".tmp")
        tmp.write_bytes(updated.encode("utf-8"))
        os.replace(tmp, constitution)
        data = load(root, slug)
        data["claims"] = [c for c in data["claims"] if c.get("stage") not in {local, stage_dir.name}]
        if claims_path(root, slug).is_file():
            save(root, slug, data)
        ledger = _read_ledger(root)
        ledger.setdefault("sequences", {}).setdefault("stage", []).append(
            {"number": f"{number:03d}", "track": slug})
        _write_json(sdd / LEDGER_NAME, ledger)
    return result
