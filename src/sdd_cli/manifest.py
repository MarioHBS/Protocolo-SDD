"""The manifest is what makes `sdd migrate` safe.

It records, per project: kit version, language, feature flags, installed
providers, and a hash of every MANAGED file at install time.

Managed files (owned by the CLI, replaced on migrate):
    .sdd/README.md, .sdd/skills/**, .sdd/templates/**, provider shims
User files (owned by you, NEVER touched by the CLI):
    .sdd/constitution.md, .sdd/roadmap.md, .sdd/CHANGELOG.md, .sdd/stages/**,
    estimates

If a managed file's current hash differs from the recorded one, you edited it
by hand -- migrate will back it up instead of silently discarding your change.
"""

import hashlib
import json
from datetime import date
from pathlib import Path

MANIFEST_NAME = ".sdd-manifest.json"


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def manifest_path(root: Path) -> Path:
    return root / ".sdd" / MANIFEST_NAME


def load(root: Path) -> dict | None:
    p = manifest_path(root)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save(root: Path, data: dict) -> None:
    data["updated_at"] = date.today().isoformat()
    manifest_path(root).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )


def build(version: str, language: str, providers: list[str],
          features: dict, managed: dict[str, str]) -> dict:
    return {
        "kit_version": version,
        "language": language,
        "providers": providers,
        "features": features,
        "managed_files": managed,
        "created_at": date.today().isoformat(),
    }
