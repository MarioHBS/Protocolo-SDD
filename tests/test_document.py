from __future__ import annotations

import json
import types

from sdd_cli.cli import cmd_document


def test_document_answers_persist_plan_and_create_stubs(tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text("## Settings\n\n- **Documentation:** off\n", encoding="utf-8")
    (sdd / ".sdd-manifest.json").write_text(json.dumps({"features": {"documentation": False}}), encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({"base_path": "docs", "documents": [{"path": "architecture.md", "purpose": "overview"}]}), encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), answers=str(answers), create_stubs=True, dry_run=False, json=False)
    cmd_document(args)
    assert (sdd / "documentation.json").is_file()
    assert (tmp_path / "docs" / "architecture.md").is_file()
    assert "Documentation:** on" in (sdd / "constitution.md").read_text(encoding="utf-8")


def test_document_rejects_parent_paths(tmp_path):
    (tmp_path / ".sdd").mkdir()
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({"documents": [{"path": "../unsafe.md"}]}), encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), answers=str(answers), create_stubs=False, dry_run=True, json=False)
    try:
        cmd_document(args)
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("unsafe path must fail")
