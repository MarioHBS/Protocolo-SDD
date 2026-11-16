"""4.9.0 — hooks: track guard (H-01/H-03), post-close doctor (H-02), hooks install (H-04)."""

from __future__ import annotations

import io
import json
import subprocess
import types
from pathlib import Path

import pytest

from sdd_cli import _hooks, _tracks
from sdd_cli.cli import _doctor_payload, cmd_hooks, cmd_track

CLI = "sddkit"


def _args(**values):
    return types.SimpleNamespace(**{"path": ".", "json": False, **values})


def _project(tmp_path: Path, claims: dict[str, dict]) -> Path:
    """A project with one track per entry: {slug: {"paths": [...], "branch": ...}}."""
    (tmp_path / ".sdd").mkdir(exist_ok=True)
    for slug, claim in claims.items():
        (tmp_path / ".sdd" / "tracks" / slug).mkdir(parents=True)
        _tracks.save(tmp_path, slug, {
            "version": 1, "track": slug, **({"branch": claim["branch"]} if claim.get("branch") else {}),
            "claims": [{"stage": "001", "paths": claim.get("paths", []), "sequences": [], "runtime": [],
                        "stability_sensitive": False}]})
    return tmp_path


def _subdir(tmp_path: Path, name: str) -> Path:
    (tmp_path / name).mkdir()
    return tmp_path / name


def _git_branch(root: Path, name: str) -> None:
    subprocess.run(["git", "init", "-q", "-b", name], cwd=root, check=True)


def _call(root: Path, file: str, event: str = "pre-edit", doctor=None) -> dict | None:
    payload = {"cwd": str(root), "tool_name": "Edit", "tool_input": {"file_path": str(root / file)}}
    out = _hooks.run(event, json.dumps(payload), doctor or (lambda r: {"findings": []}))
    return json.loads(out) if out else None


@pytest.fixture(autouse=True)
def _no_session_env(monkeypatch):
    monkeypatch.delenv("SDD_TRACK", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)


# ------------------------------------------------------------ H-01 guard

def test_guard_reports_a_path_claimed_by_two_tracks(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["src/app.py"]}})
    result = _tracks.guard(root, "src/app.py")
    assert [f["kind"] for f in result["findings"]] == ["track_shared_touch"]
    assert result["findings"][0]["tracks"] == ["left", "right"]


def test_guard_is_quiet_for_a_path_one_track_owns(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["web/**"]}})
    assert _tracks.guard(root, "src/app.py")["findings"] == []


def test_guard_never_flags_sdd_bookkeeping(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["**"]}, "right": {"paths": ["**"]}})
    assert _tracks.guard(root, ".sdd/stages/001-x/report.md")["findings"] == []


def test_guard_command_exit_codes(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["src/app.py"]}})
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit) as error:
        cmd_track(_args(track_command="guard", file="src/app.py", track=None))
    assert error.value.code == 1
    assert "track_shared_touch" in capsys.readouterr().out
    cmd_track(_args(track_command="guard", file="web/index.html", track=None))  # clean: no exit
    assert "no track conflict" in capsys.readouterr().out


def test_guard_command_rejects_a_file_outside_the_project(tmp_path, monkeypatch):
    root = _project(_subdir(tmp_path, "proj"), {"left": {"paths": ["src/**"]}})
    monkeypatch.chdir(root)
    with pytest.raises(SystemExit):
        cmd_track(_args(track_command="guard", file=str(tmp_path / "elsewhere.txt"), track=None))


# ------------------------------------------------------ session track

def test_session_track_comes_from_flag_then_env_then_branch(tmp_path, monkeypatch):
    root = _project(tmp_path, {"left": {"paths": ["src/**"], "branch": "feat-left"},
                               "right": {"paths": ["web/**"]}})
    _git_branch(root, "feat-left")
    assert _tracks.session_track(root) == "left"                      # branch
    monkeypatch.setenv("SDD_TRACK", "right")
    assert _tracks.session_track(root) == "right"                     # env beats branch
    assert _tracks.session_track(root, "left") == "left"              # flag beats env


def test_session_track_ignores_a_slug_that_is_not_an_active_track(tmp_path, monkeypatch):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}})
    monkeypatch.setenv("SDD_TRACK", "ghost")
    assert _tracks.session_track(root) is None


def test_session_track_is_unknown_when_two_tracks_share_the_branch(tmp_path):
    root = _project(tmp_path, {"a": {"paths": ["a/**"], "branch": "main"},
                               "b": {"paths": ["b/**"], "branch": "main"}})
    _git_branch(root, "main")
    assert _tracks.session_track(root) is None


# ------------------------------------------------- H-01/H-03 pre-edit hook

def test_pre_edit_asks_on_a_shared_claim_and_never_denies(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["src/app.py"]}})
    out = _call(root, "src/app.py")["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "ask"
    assert "left, right" in out["permissionDecisionReason"]


def test_pre_edit_warns_outside_the_session_footprint_without_asking(tmp_path, monkeypatch):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["web/**"]}})
    monkeypatch.setenv("SDD_TRACK", "left")
    out = _call(root, "web/index.html")["hookSpecificOutput"]
    assert "permissionDecision" not in out
    assert "outside this track's declared footprint" in out["additionalContext"]
    assert "belongs to track right" in out["additionalContext"]


def test_pre_edit_is_quiet_inside_the_footprint(tmp_path, monkeypatch):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}})
    monkeypatch.setenv("SDD_TRACK", "left")
    assert _call(root, "src/app.py") is None


def test_pre_edit_without_a_known_session_track_stays_quiet_on_a_single_owner(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}})
    assert _call(root, "docs/readme.txt") is None


def test_pre_edit_accepts_a_windows_style_path(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["src/app.py"]}})
    raw = str(root / "src" / "app.py").replace("/", "\\")
    payload = {"cwd": str(root), "tool_input": {"file_path": raw}}
    out = _hooks.run("pre-edit", json.dumps(payload), lambda r: {})
    if "\\" in str(root):  # only on Windows does the backslash form resolve to the same file
        assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "ask"


# ------------------------------------------------------ H-02 post-edit

def test_post_edit_runs_doctor_when_a_report_is_written(tmp_path):
    root = _project(tmp_path, {})
    seen = []

    def doctor(path):
        seen.append(path)
        return {"findings": [{"severity": "warn", "code": "spec_without_todo"},
                             {"severity": "error", "code": "mojibake_v2"},
                             {"severity": "warn", "code": "spec_without_todo"}]}

    out = _call(root, ".sdd/stages/003-x/report.md", "post-edit", doctor)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse"
    assert "1 error(s), 2 warning(s)" in out["additionalContext"]
    assert "mojibake_v2" in out["additionalContext"] and "spec_without_todo x2" in out["additionalContext"]
    assert seen == [root.resolve()]


def test_post_edit_says_clean_when_doctor_finds_nothing(tmp_path):
    root = _project(tmp_path, {})
    out = _call(root, ".sdd/stages/003-x/report.md", "post-edit")["hookSpecificOutput"]
    assert out["additionalContext"] == "sddkit doctor after report.md: clean."


def test_post_edit_ignores_every_other_markdown_file(tmp_path):
    root = _project(tmp_path, {})

    def boom(path):
        raise AssertionError("doctor must not run")

    for name in ("README.md", "notes.md", ".sdd/stages/003-x/spec.md", "docs/report.md", ".sdd/report.md.bak"):
        assert _call(root, name, "post-edit", boom) is None


def test_post_edit_fires_for_a_report_inside_a_track(tmp_path):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}})
    assert _call(root, ".sdd/tracks/left/stages/001-x/report.md", "post-edit") is not None


# ------------------------------------------------- the hook never breaks

@pytest.mark.parametrize("stdin", ["", "not json", "[]", "{}", '{"tool_input": "x"}',
                                   '{"tool_input": {"file_path": ""}}'])
def test_run_answers_nothing_on_malformed_input(tmp_path, stdin):
    _project(tmp_path, {})
    assert _hooks.run("pre-edit", stdin, lambda r: {}) == ""


def test_run_answers_nothing_for_a_file_outside_the_project(tmp_path):
    root = _project(_subdir(tmp_path, "proj"), {})
    assert _call(root, "../outside.txt") is None


def test_run_swallows_a_crashing_doctor(tmp_path):
    root = _project(tmp_path, {})

    def boom(path):
        raise RuntimeError("doctor broke")

    assert _call(root, ".sdd/stages/003-x/report.md", "post-edit", boom) is None


def test_run_outside_an_sdd_project_answers_nothing(tmp_path):
    payload = {"cwd": str(tmp_path), "tool_input": {"file_path": str(tmp_path / "a.py")}}
    assert _hooks.run("pre-edit", json.dumps(payload), lambda r: {}) == ""


def test_hooks_run_command_prints_json_and_exits_cleanly(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["src/app.py"]}})
    payload = {"cwd": str(root), "tool_input": {"file_path": str(root / "src" / "app.py")}}
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode())))
    cmd_hooks(types.SimpleNamespace(hooks_command="run", event="pre-edit"))
    assert json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_hooks_run_doctor_integration_on_a_real_project(tmp_path):
    root = _project(tmp_path, {})
    (root / ".sdd" / "stages" / "001-x").mkdir(parents=True)
    out = _call(root, ".sdd/stages/001-x/report.md", "post-edit", _doctor_payload)
    assert out["hookSpecificOutput"]["additionalContext"].startswith("sddkit doctor after report.md:")


# --------------------------------------------------- H-04 install/uninstall

def _settings(root: Path, local: bool = False) -> dict:
    return json.loads(_hooks.settings_path(root, local).read_text(encoding="utf-8"))


def test_install_registers_both_hooks_once(tmp_path):
    root = _project(tmp_path, {})
    assert _hooks.install(root, CLI)["added"] == ["pre-edit", "post-edit"]
    assert _hooks.install(root, CLI)["added"] == []
    data = _settings(root)
    assert len(data["hooks"]["PreToolUse"]) == 1 and len(data["hooks"]["PostToolUse"]) == 1
    group = data["hooks"]["PreToolUse"][0]
    assert group["matcher"] == "Edit|Write|MultiEdit"
    assert group["hooks"][0]["command"] == "sddkit hooks run pre-edit"


def test_install_keeps_the_owners_settings_and_hooks(tmp_path):
    root = _project(tmp_path, {})
    path = _hooks.settings_path(root)
    path.parent.mkdir()
    own = {"permissions": {"allow": ["Bash(ls)"]},
           "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "lint.sh"}]}],
                     "Stop": [{"hooks": [{"type": "command", "command": "bell.sh"}]}]}}
    path.write_text(json.dumps(own), encoding="utf-8")
    _hooks.install(root, CLI)
    data = _settings(root)
    assert data["permissions"] == own["permissions"]
    assert data["hooks"]["Stop"] == own["hooks"]["Stop"]
    assert data["hooks"]["PreToolUse"][0] == own["hooks"]["PreToolUse"][0]
    assert len(data["hooks"]["PreToolUse"]) == 2


def test_uninstall_removes_only_the_kits_entries(tmp_path):
    root = _project(tmp_path, {})
    path = _hooks.settings_path(root)
    path.parent.mkdir()
    own_group = {"matcher": "Bash", "hooks": [{"type": "command", "command": "lint.sh"}]}
    path.write_text(json.dumps({"model": "x", "hooks": {"PreToolUse": [own_group]}}), encoding="utf-8")
    _hooks.install(root, CLI)
    result = _hooks.uninstall(root, CLI)
    assert sorted(result["removed"]) == ["sddkit hooks run post-edit", "sddkit hooks run pre-edit"]
    assert _settings(root) == {"model": "x", "hooks": {"PreToolUse": [own_group]}}


def test_uninstall_drops_an_emptied_hooks_key(tmp_path):
    root = _project(tmp_path, {})
    _hooks.install(root, CLI)
    _hooks.uninstall(root, CLI)
    assert _settings(root) == {}
    assert _hooks.uninstall(root, CLI)["removed"] == []


def test_install_refuses_invalid_settings_and_writes_nothing(tmp_path):
    root = _project(tmp_path, {})
    path = _hooks.settings_path(root)
    path.parent.mkdir()
    for bad in ("{not json", "[]", '{"hooks": []}', '{"hooks": {"PreToolUse": {}}}'):
        path.write_text(bad, encoding="utf-8")
        with pytest.raises(ValueError):
            _hooks.install(root, CLI)
        assert path.read_text(encoding="utf-8") == bad


def test_install_local_writes_the_uncommitted_file(tmp_path):
    root = _project(tmp_path, {})
    _hooks.install(root, CLI, local=True)
    assert _hooks.settings_path(root, True).is_file()
    assert not _hooks.settings_path(root).exists()
    assert _hooks.status(root, CLI)["hooks"] == {"pre-edit": ["settings.local.json"],
                                                  "post-edit": ["settings.local.json"]}


def test_hooks_commands_report_install_status_and_uninstall(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path, {})
    monkeypatch.chdir(root)
    cmd_hooks(_args(hooks_command="status"))
    assert "off" in capsys.readouterr().out
    cmd_hooks(_args(hooks_command="install", local=False))
    assert "installed 2 hook(s)" in capsys.readouterr().out
    cmd_hooks(_args(hooks_command="install", local=False))
    assert "nothing to do" in capsys.readouterr().out
    cmd_hooks(_args(hooks_command="status", json=True))
    assert json.loads(capsys.readouterr().out)["installed"] is True
    cmd_hooks(_args(hooks_command="uninstall", local=False))
    assert "removed 2 hook(s)" in capsys.readouterr().out


def test_hooks_install_exits_with_an_error_on_broken_settings(tmp_path, monkeypatch):
    root = _project(tmp_path, {})
    monkeypatch.chdir(root)
    path = _hooks.settings_path(root)
    path.parent.mkdir()
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(SystemExit):
        cmd_hooks(_args(hooks_command="install", local=False))


def test_hooks_install_needs_an_sdd_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cmd_hooks(_args(hooks_command="install", local=False))


# ------------------------------------------------- manual path unchanged

def test_manual_commands_answer_the_same_with_and_without_the_hooks(tmp_path, monkeypatch, capsys):
    root = _project(tmp_path, {"left": {"paths": ["src/**"]}, "right": {"paths": ["src/app.py"]}})
    monkeypatch.chdir(root)

    def manual():
        capsys.readouterr()
        with pytest.raises(SystemExit):
            cmd_track(_args(track_command="check"))
        check = capsys.readouterr().out
        with pytest.raises(SystemExit):
            cmd_track(_args(track_command="guard", file="src/app.py", track=None))
        return check, capsys.readouterr().out, _doctor_payload(root)["findings"]

    before = manual()
    _hooks.install(root, CLI)
    assert manual() == before


def test_update_never_registers_a_hook(tmp_path, capsys):
    from test_update import _seed_project

    from sdd_cli.cli import cmd_update

    root = _seed_project(tmp_path, "4.8.2")
    try:
        cmd_update(types.SimpleNamespace(path=str(root), dry_run=False, notes=False, global_skill=False))
    except SystemExit:
        pass
    capsys.readouterr()
    assert not _hooks.settings_path(root).exists()
    assert not _hooks.settings_path(root, True).exists()
