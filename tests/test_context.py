"""Tests for the deliberately small startup-context command."""

from __future__ import annotations

import types
from pathlib import Path

from sdd_cli.cli import cmd_context


def _args(path: Path, *, budget: bool = False, json: bool = False):
    return types.SimpleNamespace(path=str(path), budget=budget, json=json)


def test_context_reads_only_the_constitution_prefix(capsys, tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "README.md").write_text("# Method\n", encoding="utf-8")
    (sdd / "constitution.md").write_text(
        "# Constitution\n\n## Settings\n\n- **Language:** en\n\n"
        "## Current state\n\n- **State:** INITIALIZING\n\n"
        "## 1. Project vision\n\nsecret later section\n", encoding="utf-8")

    cmd_context(_args(tmp_path))
    output = capsys.readouterr().out
    assert "Language" in output
    assert "INITIALIZING" in output
    assert "secret later section" not in output


def test_context_budget_distinguishes_hot_and_cold_files(capsys, tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "README.md").write_text("x" * 40, encoding="utf-8")
    (sdd / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n## 1. Project vision\n", encoding="utf-8")
    (sdd / "roadmap.md").write_text("x" * 100, encoding="utf-8")

    cmd_context(_args(tmp_path, budget=True))
    output = capsys.readouterr().out
    assert "hot  .sdd/README.md" in output
    assert "cold .sdd/roadmap.md" in output
    assert "startup total" in output


def test_budget_counts_only_the_constitution_head_as_hot(capsys, tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "README.md").write_text("x" * 40, encoding="utf-8")
    (sdd / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n## 1. Project vision\n" + "y" * 4000, encoding="utf-8")

    cmd_context(_args(tmp_path, budget=True, json=True))
    import json as _json
    data = _json.loads(capsys.readouterr().out)
    hot = [r for r in data["budget"] if r["class"] == "hot"]
    assert {r["path"] for r in hot} == {".sdd/README.md", ".sdd/constitution.md"}
    assert next(r for r in hot if r["path"].endswith("constitution.md"))["bytes"] < 100
    assert data["startup_estimated_tokens"] < data["full_read_estimated_tokens"]


def test_context_resolves_prose_active_stage(capsys, tmp_path):
    sdd = tmp_path / ".sdd"
    (sdd / "stages" / "091-notificacoes-status").mkdir(parents=True)
    (sdd / "stages" / "091-notificacoes-status" / "spec.md").write_text("spec", encoding="utf-8")
    (sdd / "constitution.md").write_text(
        "## Settings\n\n## Current state\n\n- **State:** IMPLEMENTING\n"
        "- **Active stage:** Etapa 091 (`notificacoes-status`) especificada e travada.\n\n"
        "## 1. Project vision\n", encoding="utf-8")

    cmd_context(_args(tmp_path, json=True))
    captured = capsys.readouterr()
    import json as _json
    data = _json.loads(captured.out)
    assert data["active_stage"] == "091-notificacoes-status"
    assert data["active_paths"] == {"spec.md": ".sdd/stages/091-notificacoes-status/spec.md"}
    assert "cannot resolve" not in captured.err


def test_context_unresolvable_stage_is_not_an_error(capsys, tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(
        "## Current state\n\n- **State:** SPECIFYING\n- **Active stage:** nothing yet\n\n## 1. x\n",
        encoding="utf-8")
    cmd_context(_args(tmp_path))
    captured = capsys.readouterr()
    assert "cannot resolve" not in captured.err
    assert "Active stage: nothing yet" in captured.out
