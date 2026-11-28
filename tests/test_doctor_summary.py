"""K-11: the closing line of `doctor` counts every kind of warning shown above it.

P11 (IP-004): with `accent-loss` and `abs_file_links` on screen the report said "1 kind(s)". The
warnings printed in their own sections were left out of the number, and a warning of a track alone
even ended in "clean.".
"""

from __future__ import annotations

import types
from pathlib import Path

from sdd_cli.cli import cmd_doctor, cmd_init


def _project(tmp_path: Path) -> Path:
    cmd_init(types.SimpleNamespace(
        path=str(tmp_path), provider=["generic"], language=None, estimation=False, docs=False, tracks=False,
        edd=False, dashboard_ui="static", force=False, yes=True, discovery=None))
    return tmp_path


def _doctor(root: Path, capsys) -> str:
    capsys.readouterr()
    try:
        cmd_doctor(types.SimpleNamespace(path=str(root), json=False, slim=False, all=False))
    except SystemExit:
        pass
    return capsys.readouterr().out


def _stage(root: Path, spec: str, todo: str | None = None, report: bool = False) -> None:
    stage = root / ".sdd" / "stages" / "001-first"
    stage.mkdir(parents=True)
    (stage / "spec.md").write_text(spec, encoding="utf-8", newline="\n")
    if todo is not None:
        (stage / "todo.md").write_text(todo, encoding="utf-8", newline="\n")
    if report:
        (stage / "report.md").write_text("# Report\n", encoding="utf-8", newline="\n")


def test_a_new_project_is_clean(tmp_path, capsys):
    assert _doctor(_project(tmp_path), capsys).rstrip().endswith("clean.")


def test_a_warning_printed_in_its_own_section_is_counted_with_the_others(tmp_path, capsys):
    root = _project(tmp_path)
    _stage(root, "# Spec\n\nA decis?o.\n", todo="- [x] done\n")
    path = root / ".sdd" / "constitution.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nSee file:///C:/x/y\n", encoding="utf-8", newline="\n")
    out = _doctor(root, capsys)
    assert "accent-loss" in out and "abs_file_links" in out
    assert "2 kind(s) of finding to review" in out


def test_accent_loss_alone_is_not_clean(tmp_path, capsys):
    root = _project(tmp_path)
    _stage(root, "# Spec\n\nA decis?o.\n", todo="- [x] done\n")
    out = _doctor(root, capsys)
    assert "1 kind(s) of finding to review" in out and "clean." not in out


def test_stage_hygiene_alone_is_not_reported_as_zero_kinds(tmp_path, capsys):
    root = _project(tmp_path)
    _stage(root, "# Spec\n")
    assert "1 kind(s) of finding to review" in _doctor(root, capsys)


def test_a_track_warning_alone_is_counted(tmp_path, capsys):
    root = _project(tmp_path)
    track = root / ".sdd" / "tracks" / "idle"
    track.mkdir(parents=True)
    (track / "state.md").write_text("- **State:** SPECIFYING\n", encoding="utf-8", newline="\n")
    out = _doctor(root, capsys)
    assert "WARN track hygiene" in out
    assert "kind(s) of finding to review" in out and "clean." not in out


def test_a_closed_track_left_in_place_is_a_note_on_screen_too(tmp_path, capsys):
    root = _project(tmp_path)
    track = root / ".sdd" / "tracks" / "done"
    track.mkdir(parents=True)
    (track / "state.md").write_text("- **Status:** closed\n", encoding="utf-8", newline="\n")
    out = _doctor(root, capsys)
    assert "note  track hygiene" in out and "WARN track hygiene" not in out
    assert out.rstrip().endswith("clean.")
