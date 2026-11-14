"""K-05: a kit backup folder Git already tracks is not fixed by `.gitignore`.

P4 had `.sdd/.pre-migrate-backup/` committed months earlier. The 4.8.1 note said `fix --gitignore`,
which wrote the line but left the file tracked, so the note came back unchanged; and with the line
already there, every run appended it again. A tracked folder needs `git rm -r --cached`, which the
kit leaves to the owner.
"""
from __future__ import annotations

import shutil
import subprocess
import types
from pathlib import Path

import pytest
from test_backup_ignore import _backup, _codes, _repo

from sdd_cli.cli import _doctor_payload, cmd_fix

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git on PATH")


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
                   cwd=root, check=True, capture_output=True)


def _commit_backup(root: Path, name: str = ".pre-migrate-backup") -> None:
    _backup(root, name)
    _git(root, "add", "-A", "-f")
    _git(root, "commit", "-qm", "base")


def _fix(root: Path) -> int:
    args = types.SimpleNamespace(path=str(root), gitignore=True, dry_run=False, json=False)
    try:
        cmd_fix(args)
    except SystemExit as stop:
        return int(stop.code)
    return 0


def test_a_tracked_backup_is_its_own_note_and_never_the_ignore_one(tmp_path):
    root = _repo(tmp_path)
    _commit_backup(root)
    codes = _codes(root)
    assert "backup_tracked" in codes and "backup_not_ignored" not in codes
    note = next(f for f in _doctor_payload(root)["findings"] if f["code"] == "backup_tracked")
    assert note["severity"] == "note" and note["path"] == ".sdd/.pre-migrate-backup" and note["count"] == 1


def test_fix_writes_the_line_once_lists_the_folder_and_the_owner_untracks_it(tmp_path):
    root = _repo(tmp_path)
    _commit_backup(root)
    assert _fix(root) == 2  # unresolved: the kit does not touch the index
    text = (root / ".gitignore").read_text(encoding="utf-8")
    assert text.count("/.sdd/.pre-migrate-backup/") == 1
    assert "backup_tracked" in _codes(root)  # the line alone does not clear it
    _git(root, "rm", "-r", "--cached", "-q", ".sdd/.pre-migrate-backup")
    assert not {"backup_tracked", "backup_not_ignored"} & _codes(root)


def test_a_tracked_folder_already_listed_never_gets_the_line_twice(tmp_path):
    root = _repo(tmp_path, "/.sdd/.pre-migrate-backup/\n")
    _commit_backup(root)
    before = (root / ".gitignore").read_text(encoding="utf-8")
    assert _fix(root) == 2
    assert _fix(root) == 2
    assert (root / ".gitignore").read_text(encoding="utf-8") == before


def test_one_folder_tracked_and_another_only_visible_get_one_note_each(tmp_path):
    root = _repo(tmp_path)
    _commit_backup(root, ".pre-migrate-backup")
    _backup(root, ".pre-fix-backup")
    codes = _codes(root)
    assert {"backup_tracked", "backup_not_ignored"} <= codes
    _fix(root)
    text = (root / ".gitignore").read_text(encoding="utf-8")
    assert "/.sdd/.pre-fix-backup/" in text and "/.sdd/.pre-migrate-backup/" in text
    assert "backup_not_ignored" not in _codes(root)


def test_outside_git_nothing_is_reported(tmp_path):
    plain = tmp_path / "plain"
    (plain / ".sdd" / ".pre-migrate-backup").mkdir(parents=True)
    assert not {"backup_tracked", "backup_not_ignored"} & _codes(plain)
