"""Regression coverage for the v4 command contracts."""

from __future__ import annotations

import json
from pathlib import Path

from sdd_cli import _deps, _session
from sdd_cli.cli import build_parser


def test_v4_parser_exposes_new_commands():
    parser = build_parser()
    assert parser.parse_args(["fix", "--json"]).command == "fix"
    assert parser.parse_args(["session", "pause"]).session_command == "pause"
    assert parser.parse_args(["impact", "D-013"]).decision == "D-013"


def test_session_round_trip_and_missing_stage_is_inconsistent(tmp_path: Path):
    root = tmp_path
    (root / ".sdd" / "stages" / "001-demo").mkdir(parents=True)
    data = _session.new("IMPLEMENTING", "001-demo", context="resume here")
    _session.save(root, data)
    assert _session.load(root)["resume_hints"] == ["resume here"]
    assert _session.validate(root, _session.load(root)) == []
    data["active_stage"] = "999-missing"
    assert "active_stage does not exist: 999-missing" in _session.validate(root, data)


def test_dependencies_are_user_owned_json(tmp_path: Path):
    root = tmp_path
    (root / ".sdd").mkdir()
    payload = {"version": 1, "dependencies": [{"path": str(root), "kind": "requires"}]}
    _deps.save(root, payload)
    assert json.loads((root / ".sdd" / "dependencies.json").read_text())["version"] == 1
    assert any("cycle" in finding for finding in _deps.findings(root))
