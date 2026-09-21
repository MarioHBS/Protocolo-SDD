"""Declarative, read-mostly safety checks for shared-tree parallel tracks."""

from __future__ import annotations

import fnmatch
import json
import subprocess
from pathlib import Path


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
    if not isinstance(data.get("claims"), list):
        raise ValueError(f"invalid claims for track {slug}: claims must be a list")
    return data


def save(root: Path, slug: str, data: dict) -> None:
    path = claims_path(root, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def active_tracks(root: Path) -> list[str]:
    directory = root / ".sdd" / "tracks"
    return sorted(p.name for p in directory.iterdir() if p.is_dir() and not p.name.startswith(".")) if directory.is_dir() else []


def _normal(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _overlap(left: str, right: str) -> bool:
    """Conservative glob overlap: equal roots or a recursive glob sharing root."""
    left, right = _normal(left), _normal(right)
    if left == right:
        return True
    lroot, rroot = left.split("**", 1)[0].rstrip("/"), right.split("**", 1)[0].rstrip("/")
    return bool(lroot and rroot and (lroot.startswith(rroot) or rroot.startswith(lroot)))


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
            for value in set(left.get("sequences", [])) & set(right.get("sequences", [])):
                conflicts.append({"kind": "sequence", "tracks": [left_slug, right_slug], "value": value})
            for value in set(left.get("runtime", [])) & set(right.get("runtime", [])):
                conflicts.append({"kind": "runtime", "tracks": [left_slug, right_slug], "value": value})
            if (left.get("stability_sensitive") or right.get("stability_sensitive")) and (left.get("paths") or right.get("paths")):
                conflicts.append({"kind": "stability", "tracks": [left_slug, right_slug]})
    return conflicts


def claimed_paths(root: Path, slug: str) -> list[str]:
    paths: list[str] = []
    for claim in load(root, slug)["claims"]:
        paths.extend(_normal(path) for path in claim.get("paths", []))
    return paths


def verify(root: Path, slug: str, since: str | None = None) -> list[dict]:
    """Return changed files outside the track's declared path claims."""
    patterns = claimed_paths(root, slug)
    if not patterns:
        return [{"kind": "track_unclaimed_touch", "path": "*", "detail": "track has no path claims"}]
    command = ["git", "diff", "--name-only"]
    if since:
        command.append(since)
    try:
        output = subprocess.run(command, cwd=root, text=True, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"cannot read git diff for track verification: {exc}") from exc
    findings = []
    for name in filter(None, output.splitlines()):
        normalized = _normal(name)
        if not any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns):
            findings.append({"kind": "track_unclaimed_touch", "path": normalized, "track": slug})
    return findings


def reserve_sequence(root: Path, name: str, track: str | None = None) -> dict:
    """Reserve the next numeric migration identifier in a user-owned ledger."""
    if name != "migration":
        raise ValueError(f"unknown sequence: {name}")
    directory = root / "supabase" / "migrations"
    used = [int(match.group(1)) for path in directory.glob("*.sql") if (match := __import__("re").match(r"(\d+)_", path.name))]
    ledger_path = root / ".sdd" / ".reservations.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else {"version": 1, "sequences": {}}
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid reservation ledger: {exc}") from exc
    entries = ledger.setdefault("sequences", {}).setdefault(name, [])
    reserved = [int(item["number"]) for item in entries if str(item.get("number", "")).isdigit()]
    number = max(used + reserved, default=0) + 1
    record = {"number": f"{number:04d}", "track": track or None}
    entries.append(record)
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record
