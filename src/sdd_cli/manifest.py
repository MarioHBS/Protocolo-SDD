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


def hash_variants(path: Path) -> set[str]:
    """Hashes of a file as it is, with every line ending LF, and with every line ending CRLF.

    Git (autocrlf) and editors rewrite line endings without changing what a file says, so a
    recorded hash may belong to any of these forms.
    """
    data = path.read_bytes()
    lf = data.replace(b"\r\n", b"\n")
    return {hashlib.sha256(x).hexdigest()[:16] for x in (data, lf, lf.replace(b"\n", b"\r\n"))}


def matches_recorded(path: Path, recorded: str) -> bool:
    """True when ``path`` still holds what was recorded, ignoring line-ending rewrites."""
    return recorded in hash_variants(path)


def parse_version(v: str) -> tuple[int, int, int]:
    """Parse 'v3.0.2' or '3.0.2' into (3, 0, 2).

    Raises ValueError on a non-semver string (e.g. 'v1 (no manifest)').
    """
    v = v.strip().lstrip("vV")
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"not a semver string: {v!r}")
    major, minor, patch = (int(p) for p in parts)
    return (major, minor, patch)


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
