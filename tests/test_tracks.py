from __future__ import annotations

import subprocess
import types

import pytest

from sdd_cli.cli import cmd_seq, cmd_track


def _args(**values):
    return types.SimpleNamespace(path=".", json=False, **values)


def test_track_check_detects_shared_path(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for slug in ("left", "right"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    cmd_track(_args(track_command="claim", slug="left", stage="001", path_claim=["src/**"], seq=None, runtime=None, stability_sensitive=False))
    cmd_track(_args(track_command="claim", slug="right", stage="001", path_claim=["src/app.py"], seq=None, runtime=None, stability_sensitive=False))
    with pytest.raises(SystemExit) as error:
        cmd_track(_args(track_command="check"))
    assert error.value.code == 1
    assert "conflict path" in capsys.readouterr().out


def test_track_check_allows_disjoint_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for slug in ("api", "web"):
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
    cmd_track(_args(track_command="claim", slug="api", stage="001", path_claim=["api/**"], seq=None, runtime=None, stability_sensitive=False))
    cmd_track(_args(track_command="claim", slug="web", stage="001", path_claim=["web/**"], seq=None, runtime=None, stability_sensitive=False))
    cmd_track(_args(track_command="check"))
    assert "clean" in capsys.readouterr().out


def test_track_verify_flags_unclaimed_git_change(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    (tmp_path / ".sdd" / "tracks" / "api").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "api.py").write_text("before\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    (tmp_path / "src" / "api.py").write_text("after\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("after\n", encoding="utf-8")
    cmd_track(_args(track_command="claim", slug="api", stage="001", path_claim=["src/**"], seq=None, runtime=None, stability_sensitive=False))
    with pytest.raises(SystemExit) as error:
        cmd_track(_args(track_command="verify", slug="api", since=None))
    assert error.value.code == 1
    assert "README.md" in capsys.readouterr().out


def test_sequence_reservation_skips_existing_and_reserved_numbers(tmp_path, capsys):
    (tmp_path / ".sdd").mkdir()
    migrations = tmp_path / "supabase" / "migrations"
    migrations.mkdir(parents=True)
    (migrations / "0023_existing.sql").write_text("-- migration\n", encoding="utf-8")
    args = types.SimpleNamespace(path=str(tmp_path), name="migration", track="api", json=False)
    cmd_seq(args)
    cmd_seq(args)
    assert capsys.readouterr().out.splitlines() == ["0024", "0025"]
