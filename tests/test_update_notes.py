"""`sddkit update` explains what changed (U-02) and refreshes the global skill (U-05).

The release notes live in `content/RELEASE-NOTES.md`; `update` prints the sections between the
installed kit and the bundled one, `update --notes` reads them without touching the project, and
the doctor notes a global Claude Code skill that predates the kit.
"""
from __future__ import annotations

import types
from pathlib import Path

from test_update import _seed_project

from sdd_cli import cli, manifest
from sdd_cli.cli import _doctor_payload, _release_notes, cmd_update
from sdd_cli.content import CONTENT_DIR, KIT_VERSION


def _run(capsys, path: Path, **flags) -> str:
    values = {"path": str(path), "dry_run": False, "notes": False, "global_skill": False}
    values.update(flags)
    try:
        cmd_update(types.SimpleNamespace(**values))
    except SystemExit:
        pass
    captured = capsys.readouterr()
    return captured.out + captured.err


def _global_skill(home: Path) -> Path:
    return home / ".claude" / "skills" / "sdd" / "SKILL.md"


# ------------------------------------------------------------------ U-02 ---

def test_release_notes_cover_the_range_and_flag_manual_actions():
    notes = _release_notes((4, 5, 0), manifest.parse_version(KIT_VERSION))
    versions = [v for v, _ in notes]
    assert (4, 6, 0) in versions and (4, 5, 0) not in versions
    assert manifest.parse_version(KIT_VERSION) in versions
    assert any(line.startswith("Manual action:") for _, lines in notes for line in lines)


def test_release_notes_are_ordered_newest_first_and_never_empty():
    sections = _release_notes((0, 0, 0), (99, 0, 0))
    assert sections and all(lines for _, lines in sections)
    versions = [v for v, _ in sections]
    assert versions == sorted(versions, reverse=True)


def test_update_prints_the_notes_after_the_sync(capsys, tmp_path):
    root = _seed_project(tmp_path, "v4.5.0")
    out = _run(capsys, root)
    assert "What changed" in out and "\n  v4.6.0\n" in out and "\n  v4.5.0\n" not in out
    assert "! Manual action:" in out
    assert manifest.load(root)["kit_version"] == KIT_VERSION


def test_dry_run_prints_the_notes_and_writes_nothing(capsys, tmp_path):
    root = _seed_project(tmp_path, "v4.5.0")
    before = (root / ".sdd" / ".sdd-manifest.json").read_bytes()
    out = _run(capsys, root, dry_run=True)
    assert "What changed" in out and "DRY RUN" in out
    assert (root / ".sdd" / ".sdd-manifest.json").read_bytes() == before


def test_notes_flag_is_read_only_and_shows_the_range(capsys, tmp_path):
    root = _seed_project(tmp_path, "v4.5.0")
    before = (root / ".sdd" / ".sdd-manifest.json").read_bytes()
    out = _run(capsys, root, notes=True)
    assert "v4.6.0" in out and "Updating" not in out
    assert (root / ".sdd" / ".sdd-manifest.json").read_bytes() == before


def test_notes_flag_on_a_current_project_shows_this_versions_notes(capsys, tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    out = _run(capsys, root, notes=True)
    assert f"v{KIT_VERSION.lstrip('v')}" in out


def test_up_to_date_project_prints_no_notes(capsys, tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    out = _run(capsys, root)
    assert "Already up to date" in out and "What changed" not in out


def test_release_notes_file_is_bundled_and_readable():
    assert (CONTENT_DIR / "RELEASE-NOTES.md").is_file()
    assert _release_notes(None, (4, 7, 0))


# ------------------------------------------------------------------ U-05 ---

def test_doctor_is_silent_without_a_global_skill(tmp_path):
    root = _seed_project(tmp_path, KIT_VERSION)
    codes = {f["code"] for f in _doctor_payload(root)["findings"]}
    assert "global_skill_stale" not in codes


def test_doctor_notes_a_global_skill_without_the_marker(tmp_path, _isolated_home):
    root = _seed_project(tmp_path, KIT_VERSION)
    skill = _global_skill(_isolated_home)
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: sdd\n---\n# SDD (v3)\n", encoding="utf-8")
    finding = next(f for f in _doctor_payload(root)["findings"] if f["code"] == "global_skill_stale")
    assert finding["severity"] == "note" and _doctor_payload(root)["status"] == 0


def test_doctor_accepts_the_bundled_global_skill(tmp_path, _isolated_home):
    root = _seed_project(tmp_path, KIT_VERSION)
    skill = _global_skill(_isolated_home)
    skill.parent.mkdir(parents=True)
    skill.write_bytes((CONTENT_DIR / "shims" / "claude-global-skill.md").read_bytes())
    assert "global_skill_stale" not in {f["code"] for f in _doctor_payload(root)["findings"]}


def test_global_skill_flag_rewrites_with_a_backup(capsys, tmp_path, _isolated_home):
    root = _seed_project(tmp_path, KIT_VERSION)
    skill = _global_skill(_isolated_home)
    skill.parent.mkdir(parents=True)
    skill.write_text("# SDD (v3)\n", encoding="utf-8")
    out = _run(capsys, root, global_skill=True)
    assert "global skill" in out
    assert skill.read_bytes() == (CONTENT_DIR / "shims" / "claude-global-skill.md").read_bytes()
    backups = list(skill.parent.glob("SKILL.md.bak-*"))
    assert len(backups) == 1 and backups[0].read_text(encoding="utf-8") == "# SDD (v3)\n"
    assert not cli._global_skill_stale()


def test_global_skill_flag_dry_run_and_default_never_write(capsys, tmp_path, _isolated_home):
    root = _seed_project(tmp_path, "v4.5.0")
    skill = _global_skill(_isolated_home)
    skill.parent.mkdir(parents=True)
    skill.write_text("# SDD (v3)\n", encoding="utf-8")
    _run(capsys, root)  # a plain update never writes outside the project
    assert skill.read_text(encoding="utf-8") == "# SDD (v3)\n"
    _run(capsys, root, global_skill=True, dry_run=True)
    assert skill.read_text(encoding="utf-8") == "# SDD (v3)\n"
    assert not list(skill.parent.glob("SKILL.md.bak-*"))


def test_global_skill_flag_creates_a_missing_skill(capsys, tmp_path, _isolated_home):
    root = _seed_project(tmp_path, KIT_VERSION)
    _run(capsys, root, global_skill=True)
    assert _global_skill(_isolated_home).is_file()
