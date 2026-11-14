"""K-03: `lock_without_audit` never asks for an audit of a spec that is already implemented.

P1 (KNN) locked stage 009 before the gate existed and had moved it to CLOSING when the kit was
updated; the note asked for an audit of finished work. The kit cannot tell when a spec was locked,
so it reads what the project says about the stage: its state, and whether its todo is all done.
"""
from __future__ import annotations

from pathlib import Path

from test_audit import _codes, _project, _stage


def _pointer(root: Path, state: str, stage: str) -> None:
    constitution = root / ".sdd" / "constitution.md"
    constitution.write_text(constitution.read_text(encoding="utf-8")
                            + f"\n## Current state\n\n- **State:** {state}\n- **Active stage:** {stage}\n",
                            encoding="utf-8")


def test_the_stage_in_closing_is_not_asked_for_the_line(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big")
    _pointer(root, "CLOSING", "001-big")
    assert "lock_without_audit" not in _codes(root)


def test_the_same_stage_while_implementing_is_still_noted(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big")
    _pointer(root, "IMPLEMENTING", "001-big")
    assert _codes(root)["lock_without_audit"][0]["stage"] == "001-big"


def test_closing_one_stage_does_not_excuse_another(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big")
    _stage(root, "004-other")
    _pointer(root, "CLOSING", "001-big")
    assert [f["stage"] for f in _codes(root)["lock_without_audit"]] == ["004-other"]


def test_a_track_in_closing_excuses_its_stage_only(tmp_path):
    root = _project(tmp_path)
    track = root / ".sdd" / "tracks" / "api"
    (track / "stages").mkdir(parents=True)
    (track / "state.md").write_text("- **State:** CLOSING\n- **Active stage in this track:** 010-in-track\n",
                                    encoding="utf-8")
    from test_audit import SPEC
    for name in ("010-in-track", "011-later"):
        stage = track / "stages" / name
        stage.mkdir()
        (stage / "spec.md").write_text(SPEC.format(name=name, status="locked", header="", paths="`x/**`"),
                                       encoding="utf-8")
    assert [f["stage"] for f in _codes(root)["lock_without_audit"]] == ["011-later"]


def test_a_todo_with_every_item_done_is_work_already_finished(tmp_path):
    root = _project(tmp_path)
    stage = _stage(root, "001-big")
    (stage / "todo.md").write_text("# Todo\n\n- [x] 1. a\n- [x] 2. b\n- [~] 3. not applicable\n", encoding="utf-8")
    assert "lock_without_audit" not in _codes(root)


def test_a_todo_with_an_open_item_or_no_items_is_still_noted(tmp_path):
    root = _project(tmp_path)
    stage = _stage(root, "001-big")
    todo = stage / "todo.md"
    todo.write_text("# Todo\n\n- [x] 1. a\n- [ ] 2. b\n", encoding="utf-8")
    assert "lock_without_audit" in _codes(root)
    todo.write_text("# Todo\n\nnothing listed yet\n", encoding="utf-8")
    assert "lock_without_audit" in _codes(root)


def test_closing_does_not_hide_a_mismatch_between_the_line_and_audit_md(tmp_path):
    root = _project(tmp_path)
    _stage(root, "001-big", header="- **Locked-by-audit:** round 2 · 2026-11-12 · fixed 1/1 · dismissed 1")
    _pointer(root, "CLOSING", "001-big")
    assert "lock_audit_mismatch" in _codes(root)  # a recorded line that lies is still worth a warn
