"""`sddkit fix --weight` adds the empty `Weight` column to a stage index that lacks it (U-03).

The constitution is the owner's file, so the repair is opt-in, idempotent, keeps the file's own
line endings and leaves an exact copy under `.sdd/.pre-fix-backup/` before writing.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _index_checks as ix
from sdd_cli.cli import cmd_fix

CONSTITUTION = """# Constitution

## 1. Settings

- **Language:** en

## 5. Stage index (CANONICAL)

<!--
| Stage | Slug | Status |
|-------|------|--------|
-->

| Stage | Slug | Status | Depends on |
|-------|------|--------|------------|
| 001 | first | done | — |
| 002 | second | in progress |

### Provisional queue

| Slug | Status | Depends on | Notes |
|------|--------|------------|-------|
| third | queued | — | later |

## 6. History

| Slug | Note |
|------|------|
| x | untouched |
"""


def _project(tmp_path: Path, text: str = CONSTITUTION, newline: str = "\n") -> Path:
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_bytes(text.replace("\n", newline).encode("utf-8"))
    return tmp_path


def _fix(root: Path, capsys, **flags) -> tuple[dict, int | None]:
    values = {"path": str(root), "json": True, "dry_run": False}
    values.update(flags)
    code = None
    try:
        cmd_fix(types.SimpleNamespace(**values))
    except SystemExit as exc:
        code = exc.code
    return json.loads(capsys.readouterr().out), code


def test_adds_the_column_to_the_canonical_table_and_the_queue(tmp_path, capsys):
    root = _project(tmp_path)
    result, code = _fix(root, capsys, weight=True)
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert code == 1 and result["repairs"] == [
        {"kind": "weight_column", "path": ".sdd/constitution.md", "tables": 2}]
    assert "| Stage | Slug | Status | Depends on | Weight |" in text
    assert "| Slug | Status | Depends on | Notes | Weight |" in text
    assert "| 002 | second | in progress | | |" in text  # a short row is padded into the new column
    assert "| Slug | Note |\n|------|------|\n| x | untouched |" in text  # §6 table untouched
    assert "<!--\n| Stage | Slug | Status |\n|-------|------|--------|\n-->" in text  # comment untouched


def test_the_added_column_changes_no_stage_weight(tmp_path, capsys):
    root = _project(tmp_path)
    before = ix.stage_weights(root / ".sdd")
    _fix(root, capsys, weight=True)
    after = ix.stage_weights(root / ".sdd")
    assert set(after.values()) == {"full"} and set(after) == set(before) | set(after)


def test_it_is_idempotent_and_reports_clean_the_second_time(tmp_path, capsys):
    root = _project(tmp_path)
    _fix(root, capsys, weight=True)
    once = (root / ".sdd" / "constitution.md").read_bytes()
    result, code = _fix(root, capsys, weight=True)
    assert code is None and result["repairs"] == []
    assert (root / ".sdd" / "constitution.md").read_bytes() == once


def test_a_table_that_already_has_weight_or_peso_is_left_alone(tmp_path, capsys):
    text = CONSTITUTION.replace("| Stage | Slug | Status | Depends on |\n|-------|------|--------|------------|",
                                "| Stage | Slug | Status | Peso |\n|-------|------|--------|------|")
    root = _project(tmp_path, text)
    result, _ = _fix(root, capsys, weight=True)
    assert result["repairs"][0]["tables"] == 1  # only the queue lacked the column


def test_dry_run_writes_nothing_and_leaves_no_backup(tmp_path, capsys):
    root = _project(tmp_path)
    before = (root / ".sdd" / "constitution.md").read_bytes()
    result, code = _fix(root, capsys, weight=True, dry_run=True)
    assert code == 1 and result["dry_run"] is True and result["repairs"]
    assert (root / ".sdd" / "constitution.md").read_bytes() == before
    assert not (root / ".sdd" / ".pre-fix-backup").exists()


def test_a_backup_holds_the_exact_original_bytes(tmp_path, capsys):
    root = _project(tmp_path)
    before = (root / ".sdd" / "constitution.md").read_bytes()
    _fix(root, capsys, weight=True)
    (backup,) = (root / ".sdd" / ".pre-fix-backup").glob("*/constitution.md")
    assert backup.read_bytes() == before


def test_crlf_line_endings_are_kept(tmp_path, capsys):
    root = _project(tmp_path, newline="\r\n")
    _fix(root, capsys, weight=True)
    raw = (root / ".sdd" / "constitution.md").read_bytes()
    assert b"\r\n" in raw and raw.count(b"\n") == raw.count(b"\r\n")


def test_it_is_not_part_of_the_default_run(tmp_path, capsys):
    root = _project(tmp_path)
    before = (root / ".sdd" / "constitution.md").read_bytes()
    _fix(root, capsys)  # no flags: the usual repairs, never the owner's stage index
    assert (root / ".sdd" / "constitution.md").read_bytes() == before
    _fix(root, capsys, **{"all": True})
    assert (root / ".sdd" / "constitution.md").read_bytes() == before


def test_the_backup_is_neither_audited_nor_rewritten_by_the_other_repairs(tmp_path, capsys):
    root = _project(tmp_path, newline="\r\n")
    _fix(root, capsys, weight=True)
    (backup,) = (root / ".sdd" / ".pre-fix-backup").glob("*/constitution.md")
    original = backup.read_bytes()
    _fix(root, capsys, eol=True)
    assert backup.read_bytes() == original


def test_a_project_without_a_constitution_is_reported_not_crashed(tmp_path, capsys):
    (tmp_path / ".sdd").mkdir()
    result, code = _fix(tmp_path, capsys, weight=True)
    assert code == 2 and result["unresolved"][0]["kind"] == "weight_without_constitution"


@pytest.mark.parametrize("text", ["# no stage index here\n", "## 5. Stage index\n\nno table\n"])
def test_a_constitution_with_nothing_to_change_is_clean(tmp_path, capsys, text):
    root = _project(tmp_path, text)
    result, code = _fix(root, capsys, weight=True)
    assert code is None and result["repairs"] == []
