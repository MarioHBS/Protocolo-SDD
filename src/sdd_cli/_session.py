"""Structured, local interruption context for SDD projects and tracks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def session_path(root: Path, track: str | None = None) -> Path:
    if track:
        return root / ".sdd" / "tracks" / track / ".session.json"
    return root / ".sdd" / ".session.json"


def load(root: Path, track: str | None = None) -> dict | None:
    path = session_path(root, track)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"invalid": True, "path": str(path)}
    return data if isinstance(data, dict) else {"invalid": True, "path": str(path)}


def save(root: Path, data: dict, track: str | None = None) -> Path:
    path = session_path(root, track)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return path


def clear(root: Path, track: str | None = None) -> bool:
    path = session_path(root, track)
    if not path.exists():
        return False
    path.unlink()
    return True


def new(state: str, active_stage: str | None, *, context: str = "") -> dict:
    return {
        "version": 1,
        "state": state,
        "active_stage": active_stage,
        "active_task": None,
        "stack": [],
        "interrupted_at": None,
        "interruption_reason": None,
        "resume_hints": [context] if context else [],
        "updated_at": now(),
    }


def validate(root: Path, data: dict | None, track: str | None = None) -> list[str]:
    """Return semantic inconsistencies; no time-based staleness is inferred."""
    if data is None:
        return []
    if data.get("invalid"):
        return ["session JSON is invalid"]
    issues: list[str] = []
    if data.get("version") != 1:
        issues.append("unsupported session version")
    stage = data.get("active_stage")
    if stage:
        base = root / ".sdd" / "tracks" / track / "stages" if track else root / ".sdd" / "stages"
        if not (base / stage).is_dir():
            issues.append(f"active_stage does not exist: {stage}")
    task = data.get("active_task")
    if task is not None and (not isinstance(task, dict) or not task.get("id")):
        issues.append("active_task must be null or contain id")
    if data.get("state") not in {"IMPLEMENTING", "PAUSED"}:
        issues.append("session state must be IMPLEMENTING or PAUSED")
    return issues
