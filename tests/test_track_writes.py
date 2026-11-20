"""TK-01 to TK-04 and H-05: what the kit writes in tracks and hooks keeps the owner's text.

`track close` used to replace only the first physical line of the `State:` and `Last updated:`
bullets, so a bullet that continued on indented lines was cut in half. `--archive` moved the folder
and left every link to it behind without a word. `evaluate` counted `tracks/_closed/` as a track.
`hooks install` could not be previewed and wrote into a versioned file without saying so.
"""
from __future__ import annotations

import json
import subprocess
import types
from datetime import UTC, datetime
from pathlib import Path

from sdd_cli import _hooks, _tracks, _user_files
from sdd_cli.cli import _doctor_payload, cmd_evaluate, cmd_hooks

STATE = """# Track billing — ship it

- **Branched from stage:** 010
- **State:** IMPLEMENTING (first the schema, then
  the API, then the screens) — owner note
- **Next action:** write the API
- **Last updated:** 2026-01-01 (kickoff)
  2026-02-02 (schema done)

## Notes

Free text that must not move.
"""


def _project(root: Path, state: str = STATE, slug: str = "billing") -> Path:
    sdd = root / ".sdd"
    (sdd / "tracks" / slug).mkdir(parents=True)
    (sdd / "tracks" / slug / "state.md").write_text(state, encoding="utf-8", newline="\n")
    (sdd / "constitution.md").write_text(
        "## Current state\n\n- **State:** IMPLEMENTING\n\n### Active tracks\n\n"
        "| Track | Branched from | State | Pointer |\n|---|---|---|---|\n"
        f"| `{slug}` | 010 | IMPLEMENTING | `tracks/{slug}/state.md` |\n\n---\n\n## 1. Vision\n",
        encoding="utf-8", newline="\n")
    return root


def _state(root: Path, slug: str = "billing", archived: bool = False) -> str:
    base = root / ".sdd" / "tracks" / ("_closed" if archived else "") / slug
    return (base / "state.md").read_text(encoding="utf-8")


# ---- TK-01 ---------------------------------------------------------------------------------------

def test_a_multi_line_state_bullet_keeps_every_line(tmp_path):
    root = _project(tmp_path)
    _tracks.close(root, "billing")
    after = _state(root)
    today = datetime.now(UTC).date().isoformat()
    assert "- **State:** CLOSED\n  Previous state: IMPLEMENTING (first the schema, then\n" in after
    assert "  the API, then the screens) — owner note\n" in after  # the continuation line survives
    assert f"- **Last updated:** {today}\n  Previous update: 2026-01-01 (kickoff)\n" in after
    assert "  2026-02-02 (schema done)\n" in after


def test_closing_changes_nothing_outside_the_two_bullets(tmp_path):
    root = _project(tmp_path)
    _tracks.close(root, "billing")
    before_lines, after_lines = STATE.splitlines(), _state(root).splitlines()
    for line in before_lines:
        if not line.startswith(("- **State:**", "- **Last updated:**")):
            assert line in after_lines, line


def test_a_state_already_closed_in_prose_is_left_as_written(tmp_path):
    root = _project(tmp_path, STATE.replace("IMPLEMENTING (first", "FECHADA (first"))
    _tracks.close(root, "billing")
    assert "- **State:** FECHADA (first the schema, then" in _state(root)
    assert "Previous state" not in _state(root)


def test_a_state_file_without_the_field_is_not_touched(tmp_path):
    scratch = "# Track billing\n\nJust notes.\n"
    root = _project(tmp_path, scratch)
    result = _tracks.close(root, "billing")
    assert result["state_md"] == "unchanged" and _state(root) == scratch


def test_the_dry_run_result_carries_the_diff_and_writes_nothing(tmp_path):
    root = _project(tmp_path)
    result = _tracks.close(root, "billing", dry_run=True)
    assert any(line.startswith("+- **State:** CLOSED") for line in result["state_md_diff"])
    assert _state(root) == STATE


# ---- TK-02 ---------------------------------------------------------------------------------------

def test_a_state_with_prose_after_closed_counts_as_closed(tmp_path):
    root = _project(tmp_path, "# Track billing\n\n- **State:** CLOSED (11/09/2026) — all merged\n")
    kinds = [(d.track, d.kind) for d in _user_files._scan_tracks_v4(root / ".sdd")]
    assert kinds == [("billing", "closed_in_place")]


def test_a_state_that_only_mentions_closed_later_is_not_closed(tmp_path):
    root = _project(tmp_path, "# Track billing\n\n- **State:** IMPLEMENTING, to be closed soon\n")
    kinds = [(d.track, d.kind) for d in _user_files._scan_tracks_v4(root / ".sdd")]
    assert kinds == [("billing", "not_started")]


# ---- TK-03 ---------------------------------------------------------------------------------------

def _with_links(root: Path) -> None:
    sdd = root / ".sdd"
    (sdd / "roadmap.md").write_text("See [state](tracks/billing/state.md).\n", encoding="utf-8")
    (sdd / "CHANGELOG.md").write_text("- 2026-01-01 opened tracks/billing/ (history)\n", encoding="utf-8")


def test_archive_lists_the_links_it_leaves_behind(tmp_path):
    root = _project(tmp_path)
    _with_links(root)
    result = _tracks.close(root, "billing", archive=True)
    where = {ref["path"] for ref in result["stale_references"]}
    assert where == {".sdd/roadmap.md", ".sdd/CHANGELOG.md"}
    assert all(ref["line"] == 1 for ref in result["stale_references"])


def test_the_doctor_notes_stale_links_in_the_live_indexes_only(tmp_path):
    root = _project(tmp_path)
    _with_links(root)
    _tracks.close(root, "billing", archive=True)
    found = [f for f in _doctor_payload(root)["findings"] if f["code"] == "track_link_stale"]
    assert len(found) == 1 and found[0]["severity"] == "note"
    assert found[0]["count"] == 1 and found[0]["path"] == ".sdd/roadmap.md"  # not the CHANGELOG history


def test_a_link_to_the_new_place_is_not_stale(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "roadmap.md").write_text("See tracks/_closed/billing/state.md.\n", encoding="utf-8")
    _tracks.close(root, "billing", archive=True)
    assert [f for f in _doctor_payload(root)["findings"] if f["code"] == "track_link_stale"] == []


def test_without_archive_nothing_is_reported(tmp_path):
    root = _project(tmp_path)
    _with_links(root)
    assert _tracks.close(root, "billing")["stale_references"] == []


# ---- TK-04 ---------------------------------------------------------------------------------------

def test_evaluate_does_not_count_the_closed_bucket_as_a_track(tmp_path, capsys):
    root = _project(tmp_path)
    _tracks.close(root, "billing", archive=True)
    cmd_evaluate(types.SimpleNamespace(path=str(root), write=False, json=True))
    assert json.loads(capsys.readouterr().out)["artifacts"]["tracks"] == 0


def test_evaluate_counts_an_open_track(tmp_path, capsys):
    root = _project(tmp_path)
    cmd_evaluate(types.SimpleNamespace(path=str(root), write=False, json=True))
    assert json.loads(capsys.readouterr().out)["artifacts"]["tracks"] == 1


# ---- H-05 ----------------------------------------------------------------------------------------

def _git_init(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)


def test_install_dry_run_previews_and_writes_nothing(tmp_path):
    (tmp_path / ".sdd").mkdir()
    result = _hooks.install(tmp_path, "sddkit", dry_run=True)
    assert result["added"] == ["pre-edit", "post-edit"] and result["dry_run"] is True
    assert set(result["preview"]) == {"PreToolUse", "PostToolUse"}
    assert not _hooks.settings_path(tmp_path).exists()


def test_a_versioned_settings_file_is_flagged(tmp_path):
    (tmp_path / ".sdd").mkdir()
    _git_init(tmp_path)
    assert _hooks.install(tmp_path, "sddkit", dry_run=True)["versioned"] is True
    assert _hooks.install(tmp_path, "sddkit", local=True, dry_run=True)["versioned"] is False


def test_an_ignored_settings_file_is_not_flagged(tmp_path):
    (tmp_path / ".sdd").mkdir()
    _git_init(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/settings.json\n", encoding="utf-8")
    assert _hooks.install(tmp_path, "sddkit", dry_run=True)["versioned"] is False


def test_outside_git_nothing_is_flagged(tmp_path):
    (tmp_path / ".sdd").mkdir()
    assert _hooks.install(tmp_path, "sddkit", dry_run=True)["versioned"] is False


def test_the_command_prints_the_preview_and_the_advice(tmp_path, capsys):
    (tmp_path / ".sdd").mkdir()
    _git_init(tmp_path)
    cmd_hooks(types.SimpleNamespace(path=str(tmp_path), hooks_command="install", local=False,
                                    dry_run=True, json=False))
    out = capsys.readouterr().out
    assert "would install 2 hook(s)" in out and '"PreToolUse"' in out
    assert "versioned in Git" in out and "hooks install --local" in out
    assert not _hooks.settings_path(tmp_path).exists()


def test_a_real_install_still_writes_and_dry_run_is_off_by_default(tmp_path):
    (tmp_path / ".sdd").mkdir()
    result = _hooks.install(tmp_path, "sddkit")
    assert result["dry_run"] is False and _hooks.settings_path(tmp_path).is_file()
