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
