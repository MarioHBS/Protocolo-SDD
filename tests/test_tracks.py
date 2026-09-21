from __future__ import annotations

import types

import pytest

from sdd_cli.cli import cmd_track


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
