"""`sdd document`: interview, resume, plan validation, persistence and audit."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _docs_plan
from sdd_cli.cli import _doctor_payload, cmd_document

CONSTITUTION = (
    "## Settings\n\n- **Language:** pt-BR\n- **Documentation:** off\n\n"
    "## Current state\n\n- **State:** IMPLEMENTING\n\n"
    "## 7. Project decision conventions\n\n- **Commits:** ask first.\n\n"
    "## 8. Other\n"
)


def _project(tmp_path: Path, constitution: str = CONSTITUTION) -> Path:
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(constitution, encoding="utf-8")
    (sdd / ".sdd-manifest.json").write_text(json.dumps({"features": {"documentation": False}}), encoding="utf-8")
    return tmp_path


def _console(answers: list[str], transcript: list[str] | None = None) -> _docs_plan.Console:
    queue = list(answers)

    def read(prompt: str) -> str:
        if transcript is not None:
            transcript.append(prompt)
        if not queue:
            raise EOFError
        return queue.pop(0)

    return _docs_plan.Console(read=read, write=lambda text: transcript.append(text) if transcript is not None else None)


# Answers for a small project, in interview order.
SMALL = [
    "",                 # depth: accept the recommendation (minimal)
    "owner", "low", "",  # audience, cost of error, language (pt-BR from the constitution)
    "manual",           # base folder
    "",                 # accept the document list
    "n", "", "", "",    # numbered corpus? no; header: version, date, planned marker (defaults)
    "y", "", "1, 2",    # update on close, reviewer, README covers
    "",                 # (no existing docs) -> save?  handled below
]


def test_recommendation_grows_with_the_project():
    base = {"stages": 1, "tracks": 0, "stack": [], "existing": [], "risk_terms": []}
    assert _docs_plan.recommend_depth(base)[0] == "minimal"
    assert _docs_plan.recommend_depth({**base, "stages": 9})[0] == "medium"
    assert _docs_plan.recommend_depth({**base, "tracks": 2})[0] == "medium"
    depth, reason = _docs_plan.recommend_depth({**base, "risk_terms": ["compliance", "ledger", "payment"]})
    assert depth == "comprehensive" and "regulated" in reason
    depth, reason = _docs_plan.recommend_depth({**base, "risk_terms": ["payment"]})
    assert depth == "medium" and "payment" in reason


def test_risk_signals_come_from_vision_and_decisions_not_stage_names(tmp_path):
    constitution = """## Settings

## 1. Vision

A payment ledger.

## 4. Q

compliance

## 5. Index

| 001 | audit-current-state |
"""
    _project(tmp_path, constitution)
    signals = _docs_plan.project_signals(tmp_path)
    assert signals["risk_terms"] == ["ledger", "payment"]


def test_interview_builds_a_validated_plan(tmp_path):
    _project(tmp_path)
    plan = _docs_plan.run_interview(tmp_path, _console(SMALL))
    assert plan["depth"] == "minimal"
    assert plan["language"] == "pt-BR"
    assert plan["base_path"] == "manual"
    assert plan["documents"][0]["path"] == "README.md"
    assert plan["documents"][0]["covers"] == ["1", "2"]
    assert plan["maintenance"] == {"update_on_close": True, "reviewer": "owner"}


def test_documents_can_be_added_removed_and_relocated(tmp_path):
    _project(tmp_path)
    answers = ["", "owner", "low", "", "docs",
               "a", "glossary.md", "domain terms",          # add
               "e 1", "README.md", "readme", "README.md",   # edit: keep, own location
               "",                                          # accept list
               "n", "", "", "", "y", "", "", "", ""]
    plan = _docs_plan.run_interview(tmp_path, _console(answers))
    assert [d["path"] for d in plan["documents"]] == ["README.md", "glossary.md"]
    assert plan["documents"][0]["location"] == "README.md"
    removed = ["", "owner", "low", "", "docs", "r 1", "", "n", "", "", "", "y", "", "", ""]
    assert _docs_plan.run_interview(tmp_path, _console(removed))["documents"] == []


def test_a_location_outside_the_project_needs_explicit_confirmation(tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    _project(project)
    outside = str(tmp_path / "shared-docs")
    common = ["", "owner", "low", ""]
    tail = ["", "n", "", "", "", "y", "", "", ""]
    declined = _docs_plan.run_interview(project, _console(common + [outside, "n"] + tail))
    assert declined["base_path"] == "docs" and declined["allow_outside_project"] is False
    accepted = _docs_plan.run_interview(project, _console(common + [outside, "y"] + tail))
    assert accepted["allow_outside_project"] is True
    plain = {**accepted["documents"][0], "location": None}
    assert _docs_plan.is_outside(project, _docs_plan.resolve(project, accepted, plain))


def test_existing_docs_can_be_adopted_and_are_not_stubbed(tmp_path):
    _project(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "legacy.md").write_text("# Legacy\n", encoding="utf-8")
    answers = ["", "owner", "low", "", "docs", "", "n", "", "", "", "y", "", "", "y", "y"]
    plan = _docs_plan.run_interview(tmp_path, _console(answers))
    adopted = [d for d in plan["documents"] if d["origin"] == "adopted"]
    assert [d["location"] for d in adopted] == ["docs/legacy.md"]
    created, _ = _docs_plan.write_stubs(tmp_path, plan)
    assert all("legacy" not in c for c in created)
    assert (tmp_path / "docs" / "legacy.md").read_text(encoding="utf-8") == "# Legacy\n"


def test_interrupted_interview_resumes_where_it_stopped(tmp_path):
    _project(tmp_path)
    saved: dict = {}
    with pytest.raises(_docs_plan.InterviewAborted):
        _docs_plan.run_interview(tmp_path, _console(SMALL[:5]),  # stops while asking the document list
                                 save_state=lambda s: saved.update(json.loads(json.dumps(s))))
    assert saved["done"] == ["depth", "audience", "location"]
    asked: list[str] = []
    plan = _docs_plan.run_interview(tmp_path, _console(SMALL[5:], asked), state=saved)
    assert plan["base_path"] == "manual"  # remembered, not asked again
    assert not any("Base folder" in line or "Documentation depth" in line for line in asked)


def test_validation_rejects_unsafe_paths():
    with pytest.raises(ValueError, match="unsafe document path"):
        _docs_plan.validate({"documents": [{"path": "../x.md"}]})
    with pytest.raises(ValueError, match="base_path"):
        _docs_plan.validate({"base_path": "../out", "documents": []})
    with pytest.raises(ValueError, match="allow_outside_project"):
        _docs_plan.validate({"documents": [{"path": "a.md", "location": "../x/a.md"}]})
    ok = _docs_plan.validate({"base_path": "../out", "allow_outside_project": True,
                              "documents": [{"path": "a.md"}]})
    assert ok["base_path"] == "../out"


def _answers_file(tmp_path: Path, **extra) -> Path:
    path = tmp_path / "answers.json"
    path.write_text(json.dumps({"depth": "medium", "base_path": "docs",
                                "documents": [{"path": "architecture.md", "purpose": "overview"}], **extra}),
                    encoding="utf-8")
    return path


def _args(tmp_path: Path, **kw):
    values = {"path": str(tmp_path), "answers": None, "resume": False, "create_stubs": False,
              "dry_run": False, "json": False}
    values.update(kw)
    return types.SimpleNamespace(**values)


def test_answers_file_persists_plan_turns_feature_on_and_notes_section_7(tmp_path, capsys):
    _project(tmp_path)
    cmd_document(_args(tmp_path, answers=str(_answers_file(tmp_path)), create_stubs=True))
    plan = json.loads((tmp_path / ".sdd" / "documentation.json").read_text(encoding="utf-8"))
    assert plan["documents"][0]["path"] == "architecture.md"
    stub = (tmp_path / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "**Version:** 0.1" in stub and "Planned" in stub
    text = (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert "**Documentation:** on" in text
    assert json.loads((tmp_path / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))[
        "features"]["documentation"] is True
    assert text.count("**Documentation set:**") == 1
    assert text.index("**Documentation set:**") < text.index("## 8. Other")
    cmd_document(_args(tmp_path, answers=str(_answers_file(tmp_path))))  # idempotent
    assert (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8").count("**Documentation set:**") == 1
    assert "ok" in capsys.readouterr().out


def test_existing_documents_are_never_overwritten(tmp_path):
    _project(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "architecture.md").write_text("mine", encoding="utf-8")
    cmd_document(_args(tmp_path, answers=str(_answers_file(tmp_path)), create_stubs=True))
    assert (tmp_path / "docs" / "architecture.md").read_text(encoding="utf-8") == "mine"


def test_section_7_note_keeps_crlf(tmp_path):
    _project(tmp_path, CONSTITUTION.replace("\n", "\r\n"))
    cmd_document(_args(tmp_path, answers=str(_answers_file(tmp_path))))
    raw = (tmp_path / ".sdd" / "constitution.md").read_bytes()
    assert raw.count(b"\n") == raw.count(b"\r\n")


def test_dry_run_writes_nothing(tmp_path, capsys):
    _project(tmp_path)
    cmd_document(_args(tmp_path, answers=str(_answers_file(tmp_path)), dry_run=True, json=True))
    assert not (tmp_path / ".sdd" / "documentation.json").exists()
    assert json.loads(capsys.readouterr().out)["command"] == "document"


def test_without_a_terminal_or_answers_it_refuses(tmp_path, monkeypatch):
    _project(tmp_path)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: False))
    with pytest.raises(SystemExit):
        cmd_document(_args(tmp_path))


def test_unsafe_answers_are_rejected(tmp_path):
    _project(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"documents": [{"path": "../../etc/x.md"}]}), encoding="utf-8")
    with pytest.raises(SystemExit):
        cmd_document(_args(tmp_path, answers=str(bad)))


def test_doctor_audits_the_plan(tmp_path):
    _project(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-shared"
    cmd_document(_args(tmp_path, answers=str(_answers_file(
        tmp_path, allow_outside_project=True,
        documents=[{"path": "a.md", "location": str(outside / "a.md")}, {"path": "b.md"}]))))
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "b.md").write_text("# B\n\nno metadata here\n", encoding="utf-8")
    codes = [(f["code"]) for f in _doctor_payload(tmp_path)["findings"] if f["code"].startswith("docs_")]
    assert "docs_path_outside_project" in codes
    assert "docs_missing_file" in codes      # a.md was never created
    assert "docs_missing_header" in codes    # b.md has no Version / Last updated
