"""Doctor checks for decision records: the link between a ``D-NNN`` row, its record and the index.

Read-only, like ``_index_checks``. A project that keeps no ADRs by choice ("not applicable", or
nothing yet) never fails here: only a record that exists and contradicts itself, or two records
with one id, is worse than a note. Severity: ``adr_duplicate_id`` is an error; everything else is a
warning, except ``decisions_dir_missing``, which is a note.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from . import _adr, _decisions

_RECORD_LINK_RE = re.compile(r"\bADR-(\d+)\b")
_URL_RE = re.compile(r"(?i)^[a-z][a-z0-9+.-]*://")


def _constitution_text(root: Path) -> str:
    path = root / ".sdd" / "constitution.md"
    if not path.is_file():
        return ""
    return path.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n")


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def findings(root: Path) -> list[dict]:
    text = _constitution_text(root)
    field = _decisions.decision_records(text)
    mode = field["mode"]
    table = _decisions.rows(text)
    decision_ids = {r["id"] for r in table or [] if not r["placeholder"]}
    records = _adr.list_adrs(root)
    out: list[dict] = []

    # --- section 7 says where the records are
    if mode == _decisions.MODE_EXTERNAL:
        target = field["path"]
        if not target:
            out.append({"severity": "warn", "code": "adr_external_path_missing", "path": "",
                        "detail": "section 7 says `external` but names no folder or document"})
        elif not _URL_RE.match(target) and not (root / target).exists():
            out.append({"severity": "warn", "code": "adr_external_path_missing", "path": target,
                        "detail": f"{target} does not exist"})

    # --- records that exist
    by_id: dict[str, list[_adr.Adr]] = defaultdict(list)
    by_number: dict[int, list[_adr.Adr]] = defaultdict(list)
    for record in records:
        by_id[record.id].append(record)
        if record.number is not None:
            by_number[record.number].append(record)
    reported: set[str] = set()
    for key, group in sorted(by_id.items()):
        if len(group) > 1:
            reported.add(key)
            out.append({"severity": "error", "code": "adr_duplicate_id", "adr": key,
                        "path": _rel(root, group[0].path),
                        "paths": [_rel(root, r.path) for r in group]})
    for number, group in sorted(by_number.items()):
        key = _adr.adr_id(number)
        if len(group) > 1 and key not in reported:
            out.append({"severity": "error", "code": "adr_duplicate_id", "adr": key,
                        "path": _rel(root, group[0].path),
                        "paths": [_rel(root, r.path) for r in group]})

    known_ids = set(by_id)
    for record in records:
        path = _rel(root, record.path)
        meta = record.meta
        if record.error:
            out.append({"severity": "warn", "code": "adr_status_invalid", "adr": record.id, "path": path,
                        "detail": record.error})
            continue
        status = _adr.normalize_status(meta.get("status"))
        if status is None:
            out.append({"severity": "warn", "code": "adr_status_invalid", "adr": record.id, "path": path,
                        "detail": f"status {record.status or '(empty)'!r} is outside the cycle: "
                                  + ", ".join(_adr.STATUSES)})
        decision = str(meta.get("decision", "")).strip()
        if table is not None:
            if not decision:
                out.append({"severity": "warn", "code": "adr_without_decision", "adr": record.id, "path": path,
                            "detail": "its frontmatter names no D-NNN"})
            elif decision not in decision_ids:
                out.append({"severity": "warn", "code": "adr_without_decision", "adr": record.id, "path": path,
                            "detail": f"{decision} is not a row of section 3"})
        if status == _adr.IMPLEMENTED and not str(meta.get("implemented_in", "")).strip():
            out.append({"severity": "warn", "code": "adr_implemented_without_ref", "adr": record.id,
                        "path": path})
        if status == _adr.SUPERSEDED:
            successors = meta.get("superseded_by") or []
            successors = successors if isinstance(successors, list) else [successors]
            missing = [s for s in successors if s not in known_ids]
            if not successors:
                out.append({"severity": "warn", "code": "adr_superseded_without_successor",
                            "adr": record.id, "path": path, "detail": "superseded_by is empty"})
            elif missing:
                out.append({"severity": "warn", "code": "adr_superseded_without_successor",
                            "adr": record.id, "path": path,
                            "detail": "successor not found: " + ", ".join(missing)})

    # --- section 3 rows that point at a record that is not there
    if table is not None and mode != _decisions.MODE_EXTERNAL:
        for row in table:
            for number in sorted(set(_RECORD_LINK_RE.findall(row["record"]))):  # a link names the id twice
                if _adr.adr_id(int(number)) not in known_ids:
                    out.append({"severity": "warn", "code": "decision_row_adr_missing",
                                "decision": row["id"], "adr": _adr.adr_id(int(number)),
                                "path": ".sdd/constitution.md"})

    # --- the index and the folder itself
    if records and _adr.index_is_stale(root):
        out.append({"severity": "warn", "code": "adr_index_stale",
                    "path": f".sdd/{_adr.DECISIONS_DIR}/{_adr.INDEX_NAME}"})
    if (not _adr.decisions_dir(root).is_dir() and decision_ids
            and mode in (_decisions.MODE_INTERNAL, _decisions.MODE_UNSET, _decisions.MODE_LEGACY)):
        out.append({"severity": "note", "code": "decisions_dir_missing", "count": len(decision_ids),
                    "legacy": mode == _decisions.MODE_LEGACY})
    return out
