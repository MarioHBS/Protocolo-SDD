"""D-01 to D-05: the doctor no longer says less than it knows.

A missing `Weight` column came out as "clean" and only `fix --weight --dry-run` told. A repeated
finding showed its first occurrence and a count. The doctor did not look above the folder it was
run in. The advice for worktree copies was JavaScript-only. A session on a branch that was already
merged was a WARN.
"""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

from sdd_cli import _findings
from sdd_cli.cli import (
    _doctor_payload,
    _find_project_root,
    cmd_context,
    cmd_doctor,
    cmd_fix,
    cmd_init,
)

INDEX = """## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Depends on |
|-------|------|--------|------------|
| 001 | first | done | — |
"""


def _project(tmp_path: Path, extra: str = "") -> Path:
    (tmp_path / ".sdd").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n## 3. Locked decisions\n\n" + extra + "\n" + INDEX,
        encoding="utf-8", newline="\n")
    return tmp_path


def _codes(root: Path) -> list[str]:
    return [f["code"] for f in _doctor_payload(root)["findings"]]


def _doctor(root: Path, capsys, **flags) -> str:
    values = {"path": str(root), "json": False, "slim": False, "all": False}
    values.update(flags)
    try:
        cmd_doctor(types.SimpleNamespace(**values))
    except SystemExit:
        pass
    return capsys.readouterr().out


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


# ---- D-01 ----------------------------------------------------------------------------------------

def _audited(root: Path) -> Path:
    stage = root / ".sdd" / "stages" / "001-first"
    stage.mkdir(parents=True)
    (stage / "audit.md").write_text("# Audit\n", encoding="utf-8")
    return root


def test_a_stage_index_without_weight_is_a_note_when_the_project_audits(tmp_path):
    root = _audited(_project(tmp_path))
    found = [f for f in _doctor_payload(root)["findings"] if f["code"] == "weight_column_missing"]
    assert len(found) == 1 and found[0]["severity"] == "note" and found[0]["tables"] == 1
    assert _doctor_payload(root)["status"] == 0
    message, hint = _findings.describe(found[0])
    assert "Weight" in message and "sddkit fix --weight --dry-run" in hint


def test_a_project_that_never_audits_hears_nothing(tmp_path):
    assert "weight_column_missing" not in _codes(_project(tmp_path))


def test_the_note_goes_away_after_fix_weight(tmp_path):
    root = _audited(_project(tmp_path))
    try:
        cmd_fix(types.SimpleNamespace(path=str(root), json=True, dry_run=False, weight=True))
    except SystemExit:
        pass
    assert "weight_column_missing" not in _codes(root)


def test_a_new_project_does_not_start_with_the_note(tmp_path):
    cmd_init(types.SimpleNamespace(path=str(tmp_path), provider=["claude"], language="pt-BR",
                                   estimation=False, docs=False, tracks=False, edd=False,
                                   dashboard_ui="rich", force=False, yes=True))
    assert "weight_column_missing" not in _codes(tmp_path)


def test_no_stage_index_no_note(tmp_path):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_text("## Settings\n\n- **Language:** en\n", encoding="utf-8")
    assert "weight_column_missing" not in _codes(tmp_path)


# ---- D-02 ----------------------------------------------------------------------------------------

LONG = "| D-00{n} | decision | " + "x" * 700 + " |"


def _long_rows(count: int) -> str:
    return "\n".join(LONG.format(n=i) for i in range(1, count + 1))


def test_a_repeated_finding_shows_the_first_one_and_how_to_see_the_rest(tmp_path, capsys):
    root = _project(tmp_path, _long_rows(3))
    out = _doctor(root, capsys)
    assert "long_table_cell (x3)" in out and "doctor --all" in out
    assert out.count("D-00") == 0


def test_all_lists_every_occurrence_with_its_line_and_size(tmp_path, capsys):
    root = _project(tmp_path, _long_rows(3))
    out = _doctor(root, capsys, all=True)
    lines = [line for line in out.splitlines() if line.strip().startswith("- line ")]
    assert len(lines) == 3 and all("B" in line for line in lines)
    assert "doctor --all" not in out


def test_group_keeps_every_member():
    grouped = _findings.group([{"severity": "warn", "code": "long_table_cell", "line": n} for n in (4, 9)])
    assert [m["line"] for m in grouped[0]["members"]] == [4, 9] and grouped[0]["count"] == 2


def test_all_prints_line_column_and_snippet_for_each_accent_loss_hit(tmp_path, capsys):
    root = _project(tmp_path)
    stage = root / ".sdd" / "stages" / "001-first"
    stage.mkdir(parents=True)
    (stage / "spec.md").write_text("# Spec\n\nA decis?o foi tomada. Outra: a??o.\n", encoding="utf-8")
    plain = _doctor(root, capsys)
    assert "accent-loss" in plain and "doctor --all" not in plain.split("accent-loss")[0]
    full = _doctor(root, capsys, all=True)
    assert "3:" in full  # line 3, with a column after it


# ---- D-03 ----------------------------------------------------------------------------------------

def test_doctor_in_a_subfolder_audits_the_project_above(tmp_path, capsys):
    root = _project(tmp_path)
    sub = root / "nested" / "deeper"
    sub.mkdir(parents=True)
    cmd_doctor(types.SimpleNamespace(path=str(sub), json=True, slim=False, all=False))
    assert json.loads(capsys.readouterr().out)["project"] == str(root.resolve())
    out = _doctor(sub, capsys)
    assert "project root found above" in out and "not an SDD project" not in out


def test_a_folder_with_no_project_above_still_says_so(tmp_path, capsys):
    out = _doctor(tmp_path, capsys)
    assert "not an SDD project" in out


def test_the_nearest_project_wins(tmp_path):
    outer = _project(tmp_path)
    inner = _project(outer / "inner")  # a nested repository with its own .sdd/
    (inner / "src").mkdir()
    assert _find_project_root((inner / "src").resolve()) == inner.resolve()
    assert _find_project_root(inner.resolve()) == inner.resolve()
    assert _find_project_root(outer.resolve()) == outer.resolve()


def test_context_in_a_subfolder_finds_the_project(tmp_path, capsys):
    root = _project(tmp_path)
    sub = root / "src"
    sub.mkdir()
    cmd_context(types.SimpleNamespace(path=str(sub), json=True, budget=False))
    assert json.loads(capsys.readouterr().out)["project"] == str(root.resolve())


# ---- D-04 ----------------------------------------------------------------------------------------

def _worktree_project(tmp_path: Path) -> Path:
    root = _project(tmp_path)
    (root / ".kilo" / "worktrees" / "copy" / ".sdd").mkdir(parents=True)
    _git(root, "init", "-q")
    (root / ".gitignore").write_text(".kilo/worktrees\n", encoding="utf-8")
    return root


def _advice(root: Path) -> str | None:
    found = [f for f in _doctor_payload(root)["findings"] if f["code"] == "nested_worktree_copies_ignored"]
    return _findings.describe(found[0])[1] if found else None


def test_a_dart_project_is_told_about_analyzer_exclude(tmp_path):
    root = _worktree_project(tmp_path)
    (root / "pubspec.yaml").write_text("name: app\n", encoding="utf-8")
    advice = _advice(root)
    assert "analyzer.exclude" in advice and "vitest" not in advice


def test_the_note_stops_once_analysis_options_excludes_the_folder(tmp_path):
    root = _worktree_project(tmp_path)
    (root / "pubspec.yaml").write_text("name: app\n", encoding="utf-8")
    (root / "analysis_options.yaml").write_text("analyzer:\n  exclude: [.kilo/worktrees/**]\n", encoding="utf-8")
    assert _advice(root) is None


def test_a_javascript_project_keeps_the_original_advice(tmp_path):
    root = _worktree_project(tmp_path)
    (root / "package.json").write_text("{}\n", encoding="utf-8")
    assert "vitest.config test.exclude" in _advice(root)


def test_the_note_stops_once_every_js_config_excludes_the_folder(tmp_path):
    root = _worktree_project(tmp_path)
    (root / "package.json").write_text("{}\n", encoding="utf-8")
    (root / "tsconfig.json").write_text('{"exclude": [".kilo/worktrees"]}\n', encoding="utf-8")
    assert _advice(root) is None


def test_an_unknown_stack_gets_a_generic_line(tmp_path):
    advice = _advice(_worktree_project(tmp_path))
    assert "every test, lint or type-check tool" in advice and "vitest" not in advice


# ---- D-05 ----------------------------------------------------------------------------------------

def _repo_with_stage_branch(tmp_path: Path, merged: bool) -> Path:
    root = _project(tmp_path)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    _git(root, "switch", "-q", "-c", "etapa/001")
    (root / "work.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "work.txt")
    _git(root, "commit", "-q", "-m", "work")
    _git(root, "switch", "-q", "main")
    if merged:
        _git(root, "merge", "-q", "etapa/001")
    (root / ".sdd" / ".session.json").write_text(json.dumps(
        {"version": 1, "state": "IMPLEMENTING", "active_stage": None, "branch": "etapa/001"}), encoding="utf-8")
    return root


def test_a_merged_stage_branch_is_a_note(tmp_path):
    root = _repo_with_stage_branch(tmp_path, merged=True)
    found = [f for f in _doctor_payload(root)["findings"] if f["code"].startswith("session_branch")]
    assert [(f["code"], f["severity"]) for f in found] == [("session_branch_merged", "note")]
    assert "already merged into main" in _findings.describe(found[0])[0]


def test_a_branch_with_commits_ahead_stays_a_warning(tmp_path):
    root = _repo_with_stage_branch(tmp_path, merged=False)
    found = [f for f in _doctor_payload(root)["findings"] if f["code"].startswith("session_branch")]
    assert [(f["code"], f["severity"]) for f in found] == [("session_branch_mismatch", "warn")]


def test_a_deleted_branch_stays_a_warning(tmp_path):
    root = _repo_with_stage_branch(tmp_path, merged=True)
    _git(root, "branch", "-q", "-D", "etapa/001")
    found = [f for f in _doctor_payload(root)["findings"] if f["code"].startswith("session_branch")]
    assert [f["code"] for f in found] == ["session_branch_mismatch"]
