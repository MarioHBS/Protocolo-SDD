"""Validation and persistence for the user-owned documentation plan."""

from __future__ import annotations

import json
from pathlib import Path


def load_answers(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid documentation answers file: {exc}") from exc
    return validate(data)


def validate(data: dict) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get("documents"), list):
        raise ValueError("documentation plan must contain a documents list")
    base = data.get("base_path", "docs")
    if not isinstance(base, str) or not base or Path(base).is_absolute() or ".." in Path(base).parts:
        raise ValueError("base_path must be a non-empty relative path without '..'")
    documents = []
    for item in data["documents"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("each document needs a relative path")
        path = Path(item["path"])
        if path.is_absolute() or ".." in path.parts or path.name in {"", "."}:
            raise ValueError(f"unsafe document path: {item.get('path')!r}")
        documents.append({"path": path.as_posix(), "purpose": str(item.get("purpose", "")),
                          "owner_stage": str(item.get("owner_stage", "")), "format": str(item.get("format", "md")),
                          "covers": list(item.get("covers", []))})
    return {"schema_version": 1, "base_path": base, "audience": str(data.get("audience", "owner")),
            "language": str(data.get("language", "")), "documents": documents,
            "reviewer": str(data.get("reviewer", "owner"))}


def save(root: Path, plan: dict) -> Path:
    path = root / ".sdd" / "documentation.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
