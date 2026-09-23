"""Discovery import and opt-in EDD source-of-truth migration."""

from __future__ import annotations

import json
import types

import pytest

from sdd_cli.cli import cmd_init, cmd_migrate


def _init_args(path, discovery, **more):
    values = {"path": str(path), "provider": ["generic"], "language": None,
              "estimation": False, "docs": False, "tracks": False, "edd": False,
              "dashboard_ui": "static", "force": False, "yes": True,
              "discovery": str(discovery)}
    values.update(more)
    return types.SimpleNamespace(**values)


def _discovery(path):
    data = {
        "schema_version": "sdd-discovery/v1",
        "project": {"name": "Atlas", "language": "en"},
        "vision": {"what_it_is": "A useful atlas", "who_it_is_for": "Researchers", "definition_of_done": "Search works"},
        "features": {"edd": True},
        "decisions": [{"decision": "Storage", "choice": "SQLite", "rationale": "portable", "locked_on": "2026-09-22"}],
        "open_questions": [{"question": "Who administers it?", "blocks_gate": "no", "status": "open"}],
        "backlog": [],
        "stages": [
            {"slug": "search", "title": "Search records", "origin": "escopo-original", "footprints": ["src/search/**"], "tasks": ["Add query"]},
            {"slug": "export", "title": "Export results", "origin": "escopo-original", "footprints": ["src/export/**"]},
        ],
    }
    out = path / "discovery.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    return out


def test_discovery_import_bootstraps_reviewed_project(tmp_path):
    source = _discovery(tmp_path)
    cmd_init(_init_args(tmp_path, source))
    constitution = (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert "# Constitution — Atlas" in constitution
    assert "**State:** SPECIFYING" in constitution
    assert "001-search" in constitution and "export" in constitution
    assert (tmp_path / ".sdd" / "stages" / "001-search").is_dir()
    assert "src/search/**" in (tmp_path / ".sdd" / "backlog.md").read_text(encoding="utf-8")


def test_discovery_rejects_invalid_contract_before_writing(tmp_path):
    source = tmp_path / "bad.json"
    source.write_text('{"schema_version":"wrong"}', encoding="utf-8")
    with pytest.raises(SystemExit):
        cmd_init(_init_args(tmp_path, source))
    assert not (tmp_path / ".sdd").exists()


def test_discovery_without_tty_needs_yes(tmp_path):
    source = _discovery(tmp_path)
    with pytest.raises(SystemExit):
        cmd_init(_init_args(tmp_path, source, yes=False))
    assert not (tmp_path / ".sdd").exists()


def test_edd_migration_dry_run_then_apply_is_idempotent(tmp_path):
    stage = tmp_path / ".sdd" / "stages" / "001-search"
    stage.mkdir(parents=True)
    spec = stage / "spec.md"
    spec.write_text("**Status:** locked\n\n## 5. Acceptance criteria\n\n- [ ] Search returns results\n\n## 6. Risks\n", encoding="utf-8")
    dry = types.SimpleNamespace(path=str(tmp_path), edd_source_of_truth=True, dry_run=True, yes=True)
    cmd_migrate(dry)
    assert not (stage / "evals.md").exists()
    apply = types.SimpleNamespace(path=str(tmp_path), edd_source_of_truth=True, dry_run=False, yes=True)
    cmd_migrate(apply)
    assert "E-001" in (stage / "evals.md").read_text(encoding="utf-8")
    assert "See `evals.md`." in spec.read_text(encoding="utf-8")
    cmd_migrate(apply)


def test_edd_migration_blocks_conflicting_lists(tmp_path):
    stage = tmp_path / ".sdd" / "stages" / "001-search"
    stage.mkdir(parents=True)
    (stage / "spec.md").write_text("## 5. Acceptance criteria\n\n- [ ] A\n\n## 6. Risks\n", encoding="utf-8")
    (stage / "evals.md").write_text("- [ ] E-001 - B\n", encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), edd_source_of_truth=True, dry_run=False, yes=True)
    with pytest.raises(SystemExit):
        cmd_migrate(args)
    assert "Acceptance criteria" in (stage / "spec.md").read_text(encoding="utf-8")
