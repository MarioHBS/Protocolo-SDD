from __future__ import annotations

from sdd_cli.cli import _dashboard_data


def test_dashboard_data_has_real_views(tmp_path):
    sdd = tmp_path / ".sdd"
    (sdd / "stages" / "001-example").mkdir(parents=True)
    (sdd / "tracks").mkdir()
    (sdd / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n## Current state\n\n- **State:** INITIALIZING\n\n## 1. Project vision\n", encoding="utf-8")
    data = _dashboard_data(tmp_path)
    assert set(data) == {"Overview", "Constitution", "Stages / Tracks", "EDD", "Doctor / Fix", "Session"}
    assert "001-example" in data["Stages / Tracks"]
    assert "available" not in "\n".join(data.values())
