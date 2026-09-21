from __future__ import annotations

import json
import types

from sdd_cli.cli import cmd_evaluate


def test_evaluate_writes_local_snapshot(tmp_path):
    (tmp_path / ".sdd" / "stages").mkdir(parents=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n## 1. Project vision\n", encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), write=True, json=False)
    cmd_evaluate(args)
    snapshot = tmp_path / ".sdd" / "kit-evaluation" / "snapshot.json"
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["artifacts"]["stages"] == 0
    assert "context" in data
