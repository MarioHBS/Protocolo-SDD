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

from sdd_cli.cli import _doctor_payload, cmd_doctor


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
    assert "sdd migrate --to v4" in out
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


# ------------------------------------------------------- parallel tracks -----

def test_modern_without_tracks_dir_produces_no_track_output(capsys, tmp_path):
    """Backward compatibility: a project scaffolded before the tracks feature
    (no `.sdd/tracks/` at all) must produce ZERO track-related doctor output."""
    root = _make_modern(tmp_path)
    out, _ = _run(capsys, root)
    assert "track hygiene" not in out


def test_modern_with_empty_tracks_dir_produces_no_track_output(capsys, tmp_path):
    """A freshly-`sdd init`'d project (post-feature) has an empty tracks/ dir
    -- still zero track output until a track is actually opened."""
    root = _make_modern(tmp_path)
    (root / ".sdd" / "tracks").mkdir()
    (root / ".sdd" / "tracks" / ".gitkeep").touch()
    out, _ = _run(capsys, root)
    assert "track hygiene" not in out


def test_opened_but_empty_track_is_flagged(capsys, tmp_path):
    root = _make_modern(tmp_path)
    (root / ".sdd" / "tracks" / "login").mkdir(parents=True)
    (root / ".sdd" / "tracks" / "login" / "state.md").write_text(
        "# Track login\n", encoding="utf-8")
    out, _ = _run(capsys, root)
    assert "track hygiene" in out
    assert "login" in out
    assert "empty" in out


def test_completed_track_stage_not_incorporated_is_flagged(capsys, tmp_path):
    root = _make_modern(tmp_path)
    stage = root / ".sdd" / "tracks" / "billing" / "stages" / "001-invoice"
    stage.mkdir(parents=True)
    (stage / "report.md").write_text("# Report\n", encoding="utf-8")
    (root / ".sdd" / "tracks" / "billing" / "state.md").write_text(
        "# Track billing\n", encoding="utf-8")
    out, _ = _run(capsys, root)
    assert "track hygiene" in out
    assert "billing" in out
    assert "not_incorporated" in out


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


def test_closed_edd_stage_requires_every_eval_id_in_evidence(tmp_path):
    root = _make_modern(tmp_path)
    manifest_path = root / ".sdd" / ".sdd-manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["features"]["edd"] = True
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    stage = root / ".sdd" / "stages" / "001-example"
    stage.mkdir()
    (stage / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (stage / "evals.md").write_text("- [ ] E-001\n- [ ] E-002\n", encoding="utf-8")
    (stage / "checklist.md").write_text("# Checklist\n\nE-001\n", encoding="utf-8")
    (stage / "report.md").write_text("# Report\n", encoding="utf-8")

    findings = _doctor_payload(root)["findings"]
    assert {item["eval"] for item in findings if item["code"] == "edd_eval_uncovered"} == {"E-002"}


def test_doctor_reports_overlapping_track_claims_and_nested_worktrees(tmp_path):
    root = _make_modern(tmp_path)
    for slug, path in (("api", "src/**"), ("web", "src/app.py")):
        directory = root / ".sdd" / "tracks" / slug
        directory.mkdir(parents=True)
        (directory / "claims.json").write_text(json.dumps({"version": 1, "track": slug, "claims": [{"paths": [path]}]}), encoding="utf-8")
    (root / ".kilo" / "worktrees" / "copy" / ".sdd").mkdir(parents=True)

    findings = _doctor_payload(root)["findings"]
    assert any(item["code"] == "track_overlap" and item["severity"] == "error" for item in findings)
    assert any(item["code"] == "nested_worktree_copies" for item in findings)


def test_track_dropped_from_active_table_is_not_reported_as_not_started(tmp_path):
    from sdd_cli import _user_files

    sdd = tmp_path / ".sdd"
    (sdd / "tracks" / "done-track").mkdir(parents=True)
    (sdd / "tracks" / "waiting-track").mkdir(parents=True)
    (sdd / "constitution.md").write_text(
        "## Current state\n\n### Active tracks\n\n"
        "| Track | State |\n| --- | --- |\n| `waiting-track` | open |\n\n## 1. Vision\n",
        encoding="utf-8")

    slugs = {d.track for d in _user_files.scan_hygiene(sdd).track_divergences}
    assert slugs == {"waiting-track"}


def test_active_track_slugs_ignores_template_comment_rows(tmp_path):
    from sdd_cli import _user_files

    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(
        "### Active tracks\n\n<!--\n| `login` | x |\n-->\n\n| Track | State |\n| --- | --- |\n\n## 1. V\n",
        encoding="utf-8")
    assert _user_files.active_track_slugs(sdd) is None


def test_human_report_lists_every_finding_the_json_report_carries(tmp_path, capsys):
    """`sdd doctor` used to say "clean." while `--json` listed problems (KNN IP-004/IP-009)."""
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(
        "## Settings\n\n- **Estimation tracking:** on\n\n## Current state\n\n- **State:** SPECIFYING\n\n"
        "## 1. Vision\n\nSee [spec](file:///old/checkout/.sdd/stages/001-x/spec.md).\n", encoding="utf-8")
    (sdd / ".sdd-manifest.json").write_text(json.dumps(
        {"kit_version": "v4.1.0", "features": {"estimation": False}, "providers": []}), encoding="utf-8")
    payload_codes = {f["code"] for f in _doctor_payload(tmp_path)["findings"]}
    assert {"feature_mismatch", "abs_file_links"} <= payload_codes

    cmd_doctor(types.SimpleNamespace(path=str(tmp_path), json=False))
    out = capsys.readouterr().out
    assert "feature_mismatch" in out and "sdd fix --features" in out
    assert "abs_file_links" in out and "sdd fix --links" in out
    assert "\nclean." not in out


def test_human_report_exits_nonzero_on_an_error_finding(tmp_path):
    import pytest

    sdd = tmp_path / ".sdd"
    for slug in ("a", "b"):
        (sdd / "tracks" / slug).mkdir(parents=True)
        (sdd / "tracks" / slug / "claims.json").write_text(
            json.dumps({"version": 1, "claims": [{"stage": "001", "paths": ["src/**"]}]}), encoding="utf-8")
    (sdd / "constitution.md").write_text("## Settings\n\n## Current state\n\n## 1. V\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        cmd_doctor(types.SimpleNamespace(path=str(tmp_path), json=False))
    assert error.value.code == 1
