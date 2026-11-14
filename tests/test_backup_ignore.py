"""K-01: the folders the kit writes under `.sdd/` as backups must not be left visible to Git.

`fix --weight` and `migrate` leave `.sdd/.pre-fix-backup/` and `.sdd/.pre-migrate-backup/`; a project
whose `.gitignore` does not list them would commit a copy of its own files on `git add -A`.
The check needs a real repository, so these tests use `git init` and skip without git.
"""
from __future__ import annotations

import shutil
import subprocess
import types
from pathlib import Path

import pytest

from sdd_cli.cli import _doctor_payload, cmd_fix

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git on PATH")


def _repo(tmp_path: Path, gitignore: str | None = None) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_text("# c\n", encoding="utf-8")
    if gitignore is not None:
        (tmp_path / ".gitignore").write_text(gitignore, encoding="utf-8")
    return tmp_path


def _backup(root: Path, name: str = ".pre-fix-backup") -> None:
    folder = root / ".sdd" / name / "20261114-153122"
    folder.mkdir(parents=True)
    (folder / "constitution.md").write_text("# old\n", encoding="utf-8")


def _codes(root: Path) -> set[str]:
    return {f["code"] for f in _doctor_payload(root)["findings"]}


def _fix(root: Path, **flags) -> None:
    values = {"path": str(root), "gitignore": True, "dry_run": False, "json": False}
    values.update(flags)
    try:
        cmd_fix(types.SimpleNamespace(**values))
    except SystemExit:
        pass  # status 1 = repairs applied


def test_doctor_notes_a_backup_folder_git_still_sees(tmp_path):
    root = _repo(tmp_path)
    _backup(root)
    note = next(f for f in _doctor_payload(root)["findings"] if f["code"] == "backup_not_ignored")
    assert note["severity"] == "note" and note["path"] == ".sdd/.pre-fix-backup" and note["count"] == 1


def test_an_ignored_backup_is_not_reported(tmp_path):
    root = _repo(tmp_path, "/.sdd/.pre-fix-backup/\n")
    _backup(root)
    assert "backup_not_ignored" not in _codes(root)


def test_a_project_without_backups_or_without_git_is_not_reported(tmp_path):
    root = _repo(tmp_path)
    assert "backup_not_ignored" not in _codes(root)  # no backup folder
    plain = tmp_path / "plain"
    (plain / ".sdd" / ".pre-fix-backup").mkdir(parents=True)
    assert "backup_not_ignored" not in _codes(plain)  # not a repository: nothing to ignore


def test_fix_gitignore_adds_the_backup_folders_and_is_idempotent(tmp_path):
    root = _repo(tmp_path, "node_modules")
    _backup(root)
    _backup(root, ".pre-migrate-backup")
    _fix(root)
    text = (root / ".gitignore").read_text(encoding="utf-8")
    assert text.startswith("node_modules\n")  # the owner's lines are kept, never rewritten
    assert "/.sdd/.pre-fix-backup/\n" in text and "/.sdd/.pre-migrate-backup/\n" in text
    assert "backup_not_ignored" not in _codes(root)
    _fix(root)
    assert (root / ".gitignore").read_text(encoding="utf-8") == text


def test_fix_gitignore_only_adds_what_is_missing(tmp_path):
    root = _repo(tmp_path, "/.sdd/.pre-migrate-backup/\n")
    _backup(root)
    _backup(root, ".pre-migrate-backup")
    _fix(root)
    text = (root / ".gitignore").read_text(encoding="utf-8")
    assert text.count("/.sdd/.pre-migrate-backup/") == 1 and "/.sdd/.pre-fix-backup/" in text


def test_dry_run_writes_nothing(tmp_path):
    root = _repo(tmp_path)
    _backup(root)
    _fix(root, dry_run=True)
    assert not (root / ".gitignore").exists()


def test_the_default_run_never_touches_gitignore(tmp_path):
    root = _repo(tmp_path)
    _backup(root)
    _fix(root, gitignore=False, **{"all": True})
    assert not (root / ".gitignore").exists()
