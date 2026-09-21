"""`sdd init`: what a first install writes, and what it must never overwrite."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli.cli import cmd_init
from sdd_cli.content import KIT_VERSION


def _args(path: Path, **values) -> types.SimpleNamespace:
    base = {"path": str(path), "provider": ["claude"], "language": "pt-BR", "estimation": False,
            "docs": False, "tracks": False, "edd": False, "dashboard_ui": "rich", "force": False, "yes": True}
    base.update(values)
    return types.SimpleNamespace(**base)


def _manifest(path: Path) -> dict:
    return json.loads((path / ".sdd" / ".sdd-manifest.json").read_text(encoding="utf-8"))


def test_first_install_writes_the_kit_the_manifest_and_a_shim(tmp_path):
    cmd_init(_args(tmp_path))
    sdd = tmp_path / ".sdd"
    for name in ("README.md", "constitution.md", "roadmap.md", "CHANGELOG.md"):
        assert (sdd / name).is_file(), name
    assert (sdd / "skills" / "sdd-track" / "SKILL.md").is_file()
    assert (sdd / "templates" / "cross-cutting.template.md").is_file()
    assert (sdd / "stages").is_dir() and (sdd / "tracks").is_dir()
    assert (tmp_path / ".claude" / "commands" / "sdd.md").is_file()
    assert (tmp_path / ".gitattributes").is_file()

    data = _manifest(tmp_path)
    assert data["kit_version"] == KIT_VERSION
    assert data["language"] == "pt-BR" and data["providers"] == ["claude"]
    assert ".sdd/README.md" in data["managed_files"] and ".claude/commands/sdd.md" in data["managed_files"]
    # user files are not managed: the CLI must never treat them as its own
    assert ".sdd/constitution.md" not in data["managed_files"]


def test_settings_placeholders_are_filled_from_the_flags(tmp_path):
    cmd_init(_args(tmp_path, estimation=True, docs=True, tracks=True, edd=True, language="en"))
    text = (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert "{{" not in text
    for label in ("Estimation tracking", "Documentation", "Parallel tracks", "Eval Driven Development"):
        assert f"**{label}:** on" in text
    assert "**Language:** en" in text
    assert _manifest(tmp_path)["features"] == {"estimation": True, "documentation": True,
                                              "tracks": True, "edd": True}


def test_shim_tells_the_agent_to_load_only_what_it_needs(tmp_path):
    cmd_init(_args(tmp_path))
    shim = (tmp_path / ".claude" / "commands" / "sdd.md").read_text(encoding="utf-8")
    assert "sdd context" in shim and "`## 1.`" in shim
    assert "linked git worktree" in shim


def test_reinstall_without_force_changes_nothing(tmp_path, capsys):
    cmd_init(_args(tmp_path))
    constitution = tmp_path / ".sdd" / "constitution.md"
    constitution.write_text(constitution.read_text(encoding="utf-8") + "\nMY DECISION\n", encoding="utf-8")
    before = (tmp_path / ".sdd" / ".sdd-manifest.json").read_bytes()
    with pytest.raises(SystemExit) as exit_info:
        cmd_init(_args(tmp_path))
    assert exit_info.value.code == 0
    assert "already initialized" in capsys.readouterr().out
    assert "MY DECISION" in constitution.read_text(encoding="utf-8")
    assert (tmp_path / ".sdd" / ".sdd-manifest.json").read_bytes() == before


def test_force_refreshes_managed_files_but_keeps_user_files(tmp_path):
    cmd_init(_args(tmp_path))
    sdd = tmp_path / ".sdd"
    (sdd / "constitution.md").write_text("MINE", encoding="utf-8")
    (sdd / "roadmap.md").write_text("MY ROADMAP", encoding="utf-8")
    (sdd / "stages" / "001-x").mkdir()
    (sdd / "stages" / "001-x" / "spec.md").write_text("MY SPEC", encoding="utf-8")
    (sdd / "README.md").write_text("tampered", encoding="utf-8")
    cmd_init(_args(tmp_path, force=True))
    assert (sdd / "constitution.md").read_text(encoding="utf-8") == "MINE"
    assert (sdd / "roadmap.md").read_text(encoding="utf-8") == "MY ROADMAP"
    assert (sdd / "stages" / "001-x" / "spec.md").read_text(encoding="utf-8") == "MY SPEC"
    assert (sdd / "README.md").read_text(encoding="utf-8") != "tampered"


def test_several_providers_share_one_sdd_folder(tmp_path):
    cmd_init(_args(tmp_path, provider=["claude", "cursor", "kilo"]))
    assert (tmp_path / ".claude" / "commands" / "sdd.md").is_file()
    assert (tmp_path / ".cursor" / "rules" / "sdd.mdc").is_file()
    assert (tmp_path / ".kilo" / "commands" / "sdd.md").is_file()
    assert _manifest(tmp_path)["providers"] == ["claude", "cursor", "kilo"]


def test_unknown_provider_and_missing_path_are_refused(tmp_path):
    with pytest.raises(SystemExit):
        cmd_init(_args(tmp_path, provider=["nope"]))
    with pytest.raises(SystemExit):
        cmd_init(_args(tmp_path / "does-not-exist"))
    assert not (tmp_path / ".sdd").exists()  # nothing half-installed


def test_documentation_flag_points_to_sdd_document(tmp_path, capsys):
    cmd_init(_args(tmp_path, docs=True))
    assert "sdd document" in capsys.readouterr().out
