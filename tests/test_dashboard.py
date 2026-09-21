"""Dashboard: a data model shared by three renderers, tested headlessly.

The rich and textual tests need the optional extras and skip cleanly without them;
the CI job that installs `.[dashboard]` runs them for real.
"""

from __future__ import annotations

import asyncio
import json
import re
import types
from pathlib import Path

import pytest

from sdd_cli import _dashboard
from sdd_cli.cli import _dashboard_data, cmd_dashboard

CONSTITUTION = """\
## Settings

- **Language:** en
- **Eval Driven Development:** on

## Current state

- **State:** IMPLEMENTING
- **Active stage:** 002-api

## 1. Project vision

Something.
"""


def _project(tmp_path: Path) -> Path:
    sdd = tmp_path / ".sdd"
    for name in ("001-base", "002-api"):
        (sdd / "stages" / name).mkdir(parents=True)
    (sdd / "stages" / "001-base" / "report.md").write_text("done", encoding="utf-8")
    (sdd / "stages" / "001-base" / "spec.md").write_text("spec", encoding="utf-8")
    (sdd / "stages" / "001-base" / "evals.md").write_text("- [ ] E-001 a\n- [ ] E-002 b\n", encoding="utf-8")
    (sdd / "stages" / "002-api" / "spec.md").write_text("spec", encoding="utf-8")
    (sdd / "tracks" / "login").mkdir(parents=True)
    (sdd / "constitution.md").write_text(CONSTITUTION, encoding="utf-8")
    (sdd / ".sdd-manifest.json").write_text(json.dumps(
        {"kit_version": "v4.1.0", "features": {"edd": True}, "providers": [], "managed_files": {}}), encoding="utf-8")
    (sdd / ".session.json").write_text(json.dumps(
        {"version": 1, "state": "PAUSED", "active_stage": "002-api", "branch": "main",
         "interruption_reason": "planned", "interrupted_at": "2026-09-21T10:00:00Z",
         "resume_hints": ["finish the endpoint"]}), encoding="utf-8")
    return tmp_path


def test_views_are_real_and_share_one_model(tmp_path):
    views = _dashboard_data(_project(tmp_path))
    assert tuple(views) == _dashboard.VIEW_NAMES
    assert "state: IMPLEMENTING" in views["Overview"] and "active stage: 002-api" in views["Overview"]
    assert "startup cost" in views["Overview"]
    assert re.search(r"hot\s+Settings", views["Constitution"])
    assert re.search(r"cold\s+1\. Project vision", views["Constitution"])
    assert "001-base  [done]" in views["Stages / Tracks"]
    assert "002-api  [in progress]" in views["Stages / Tracks"]
    assert "login  (no footprint)" in views["Stages / Tracks"]
    assert "E-001 has no evidence" in views["EDD"] and "E-002 has no evidence" in views["EDD"]
    assert "edd_eval_uncovered" in views["Doctor / Fix"] and "fix:" in views["Doctor / Fix"]
    assert "branch: main" in views["Session"] and "finish the endpoint" in views["Session"]
    assert "available" not in "\n".join(views.values())


def test_empty_views_say_so_instead_of_inventing_data(tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text("## Settings\n\n## Current state\n\n## 1. V\n", encoding="utf-8")
    views = _dashboard_data(tmp_path)
    assert views["Session"] == "no session (nothing to resume)"
    assert views["EDD"] == "Eval Driven Development is off"


def test_plain_renderer_needs_no_dependencies(tmp_path, capsys):
    project = _project(tmp_path)
    cmd_dashboard(types.SimpleNamespace(path=str(project), ui="plain", set_default=False))
    out = capsys.readouterr().out
    assert out.startswith("SDD Dashboard") and "== Doctor / Fix ==" in out and "== Session ==" in out


def test_set_default_records_the_renderer(tmp_path):
    project = _project(tmp_path)
    cmd_dashboard(types.SimpleNamespace(path=str(project), ui="plain", set_default=True))
    manifest = json.loads((project / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))
    assert manifest["dashboard_renderer"] == "plain"


def test_missing_extras_is_an_explained_error_not_a_traceback(tmp_path, monkeypatch, capsys):
    project = _project(tmp_path)

    def boom(*_args, **_kwargs):
        raise ImportError("No module named 'rich'")

    monkeypatch.setattr(_dashboard, "render_rich", boom)
    with pytest.raises(SystemExit) as error:
        cmd_dashboard(types.SimpleNamespace(path=str(project), ui="rich", set_default=False))
    assert error.value.code == 1
    err = capsys.readouterr().err
    assert "sdd-cli[dashboard]" in err and "sdd dashboard --ui plain" in err


def test_textual_without_a_terminal_refuses_instead_of_hanging(tmp_path, monkeypatch, capsys):
    project = _project(tmp_path)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: False))
    with pytest.raises(SystemExit):
        cmd_dashboard(types.SimpleNamespace(path=str(project), ui="textual", set_default=False))
    assert "needs a terminal" in capsys.readouterr().err


def test_a_project_without_sdd_is_reported(tmp_path):
    with pytest.raises(SystemExit):
        cmd_dashboard(types.SimpleNamespace(path=str(tmp_path), ui="plain", set_default=False))


def test_rich_renderer_prints_every_view_and_keeps_brackets_literal(tmp_path):
    pytest.importorskip("rich")
    from rich.console import Console

    project = _project(tmp_path)
    views = _dashboard_data(project)
    views["Doctor / Fix"] += "\nmark items [-] or [!] in evals.md"  # rich markup must not swallow these
    console = Console(record=True, width=110, force_terminal=False)
    _dashboard.render_rich(views, console)
    text = console.export_text()
    for name in views:
        assert name in text
    assert "[-] or [!]" in text and "E-001 has no evidence" in text


def test_textual_dashboard_runs_headlessly_and_every_tab_renders(tmp_path):
    pytest.importorskip("textual")
    project = _project(tmp_path)
    views = _dashboard_data(project)

    async def drive() -> tuple[dict[str, str], set[int]]:
        from textual.widgets import Static, TabbedContent

        app = _dashboard.make_app(views)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            tabs = app.query_one(TabbedContent)
            rendered, screenshots = {}, set()
            for index, name in enumerate(views):
                tabs.active = f"view-{index}"
                await pilot.pause()
                assert tabs.active_pane is not None and tabs.active_pane.id == f"view-{index}"
                rendered[name] = str(tabs.active_pane.query_one(Static).render())
                screenshots.add(hash(app.export_screenshot()))
        return rendered, screenshots

    rendered, screenshots = asyncio.run(drive())
    assert rendered == views          # each tab shows exactly its own view
    assert len(screenshots) == 6      # and the screen really changes from tab to tab
