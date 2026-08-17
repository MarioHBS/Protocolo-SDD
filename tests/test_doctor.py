"""Tests for `sdd doctor` — the SDD presence/version + mojibake/hygiene audit.

Covers the three paths introduced by the presence/version gate:

1. **No `.sdd/`** -- the directory is not an SDD project. The doctor reports
   this and exits 0 (absence is not an error, so scripts scanning many dirs
   don't trip).
2. **Legacy v1 (`.sdd/` present, no `.sdd-manifest.json`)** -- reports
   ``v1 (no manifest)`` (the same literal ``cmd_migrate`` uses) and continues
   to the mojibake/hygiene audit rather than aborting.
3. **Modern install (manifest present)** -- reports the manifest's
   ``kit_version`` and proceeds to the audit.

Pattern follows ``test_mojibake.py``: direct ``sdd_cli`` imports (``conftest``
already puts ``src/`` on ``sys.path``), no install needed. ``cmd_doctor`` is
driven directly with a ``SimpleNamespace`` args stub -- it only reads
``args.path``.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

from sdd_cli.cli import cmd_doctor


def _args(path: Path) -> types.SimpleNamespace:
    return types.SimpleNamespace(path=str(path))


def _run(capsys, path: Path) -> tuple[str, int | None]:
    """Run cmd_doctor, returning (stdout, exit_code-or-None).

    cmd_doctor raises SystemExit(0) only when .sdd/ is missing, and
    SystemExit(1) only when mojibake v2 / non-UTF-8 is found. On a clean
    legacy/modern project it returns normally, so exit_code is None there --
    that's not a failure, it's the contract.
    """
    try:
        cmd_doctor(_args(path))
    except SystemExit as exc:
        out = capsys.readouterr().out
        return out, exc.code
    out = capsys.readouterr().out
    return out, None


# --------------------------------------------------------------- no .sdd/ ---

def test_no_sdd_exits_zero(capsys, tmp_path):
    out, code = _run(capsys, tmp_path)
    assert code == 0
    assert "no .sdd/ here" in out
    assert "not an SDD project" in out
    # The version/manifest block must NOT run -- there is no .sdd/ to inspect.
    assert "sdd    " not in out  # the version line the SDD-present path prints


def test_no_sdd_suggests_init(capsys, tmp_path):
    out, _ = _run(capsys, tmp_path)
    assert "sdd init" in out


def test_no_sdd_does_not_audits_mojibake(capsys, tmp_path):
    """With no .sdd/ the mojibake/hygiene audit must be skipped entirely."""
    out, _ = _run(capsys, tmp_path)
    assert "mojibake" not in out
    assert "hygiene" not in out


# ------------------------------------------------------- v1 legacy (no man) -

def _make_legacy(tmp_path: Path) -> Path:
    """A .sdd/ from a v1 install: stages dir + gitkeep, but no manifest."""
    sdd = tmp_path / ".sdd"
    stages = sdd / "stages"
    stages.mkdir(parents=True)
    (stages / ".gitkeep").touch()
    return tmp_path


def test_legacy_reports_v1_no_manifest(capsys, tmp_path):
    root = _make_legacy(tmp_path)
    out, code = _run(capsys, root)
    assert "v1 (no manifest)" in out
    # And it points the owner at migrate to upgrade.
    assert "sdd migrate --to v2" in out
    # Empty stages => no mojibake, no hygiene divergence => the audit is clean.
    # cmd_doctor returns normally on a clean run (no SystemExit raised), so
    # code is None; a clean legacy dir must NOT exit non-zero.
    assert code in (None, 0)


def test_legacy_runs_hygiene_audit(capsys, tmp_path):
    """A v1 legacy .sdd/ still gets the hygiene audit -- the audit is not
    gated on having a manifest, only on having .sdd/."""
    root = _make_legacy(tmp_path)
    out, _ = _run(capsys, root)
    assert "hygiene" in out
    assert "CHANGELOG.md" in out  # the changelog-present note always prints


# ------------------------------------------------------- modern (manifest) ---

def _make_modern(tmp_path: Path, kit_version: str = "v2.1.0") -> Path:
    """A .sdd/ with a manifest recording a kit version."""
    sdd = tmp_path / ".sdd"
    stages = sdd / "stages"
    stages.mkdir(parents=True)
    (stages / ".gitkeep").touch()
    manifest = {
        "kit_version": kit_version,
        "language": "pt-BR",
        "providers": ["generic"],
        "features": {"estimation": False, "documentation": False},
        "managed_files": {},
        "created_at": "2026-01-01",
    }
    (sdd / ".sdd-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8")
    return tmp_path


def test_modern_reports_manifest_kit_version(capsys, tmp_path):
    root = _make_modern(tmp_path, kit_version="v2.1.0")
    out, code = _run(capsys, root)
    assert "v2.1.0" in out
    # The v1-only literal must NOT appear when a manifest exists.
    assert "v1 (no manifest)" not in out
    # Clean modern dir -> cmd_doctor returns normally (code is None).
    assert code in (None, 0)


def test_modern_clean_reports_no_mojibake(capsys, tmp_path):
    root = _make_modern(tmp_path)
    out, _ = _run(capsys, root)
    assert "no mojibake detected" in out


def test_modern_without_kit_version_falls_back_to_unknown(capsys, tmp_path):
    """A manifest missing the `kit_version` key is reported as 'unknown'
    rather than crashing -- the doctor is a diagnostic, not a gate."""
    sdd = tmp_path / ".sdd"
    stages = sdd / "stages"
    stages.mkdir(parents=True)
    (stages / ".gitkeep").touch()
    # manifest with no kit_version
    (sdd / ".sdd-manifest.json").write_text(
        json.dumps({"language": "en", "providers": [], "features": {},
                    "managed_files": {}}, ensure_ascii=False) + "\n",
        encoding="utf-8")
    out, _ = _run(capsys, tmp_path)
    assert "unknown" in out
    assert "v1 (no manifest)" not in out  # manifest existed, just sparse
