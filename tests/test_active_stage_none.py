"""K-13: an `Active stage` that says there is none names no stage.

P2 (IP-016): "nenhuma", followed by a narrative that cited stage numbers, made `context` point at a
long finished stage as the active one.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli.cli import _context_payload, _scope_state, cmd_session


def _project(tmp_path: Path, active: str, state: str = "SPECIFYING") -> Path:
    for name in ("015-brute-force", "016-panel"):
        (tmp_path / ".sdd" / "stages" / name).mkdir(parents=True, exist_ok=True)
        (tmp_path / ".sdd" / "stages" / name / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (tmp_path / ".sdd" / "constitution.md").write_text(
        f"## Settings\n\n## Current state\n\n- **State:** {state}\n- **Active stage:** {active}\n",
        encoding="utf-8", newline="\n")
    return tmp_path


@pytest.mark.parametrize("value", [
    "(none)",
    "nenhuma",
    "Nenhuma — a 015 e a 016 já foram encerradas",
    "**nenhuma** (última: `015-brute-force`)",
    "none; stage 015 closed on Monday",
    "_(none yet)_",
    "Nenhum no momento, ver 015",
    "—",
])
def test_a_value_that_says_none_names_no_stage(tmp_path, value):
    root = _project(tmp_path, value)
    assert _scope_state(root) == ("SPECIFYING", None)
    data = _context_payload(root)
    assert data["active_stage"] is None and "active_paths" not in data


@pytest.mark.parametrize("value", [
    "015-brute-force",
    "Etapa 015 especificada e travada; nenhuma outra aberta",
    "`brute-force` (015)",
])
def test_a_value_that_names_a_stage_still_resolves(tmp_path, value):
    assert _scope_state(_project(tmp_path, value))[1] == "015-brute-force"


@pytest.mark.parametrize("name", ["nonexistent-slug", "none-handling"])
def test_an_unknown_name_is_still_passed_on(tmp_path, name):
    assert _scope_state(_project(tmp_path, f"`{name}`"))[1] == name


def test_a_synced_session_without_a_stage_is_consistent(tmp_path, capsys):
    root = _project(tmp_path, "nenhuma (015 fechada)", state="IMPLEMENTING")
    cmd_session(types.SimpleNamespace(path=str(root), track=None, session_command="sync"))
    saved = json.loads(next((root / ".sdd").rglob("*session*.json")).read_text(encoding="utf-8"))
    assert saved["active_stage"] is None
