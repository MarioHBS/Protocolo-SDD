"""B-01, B-02, B-03: the doctor measures what a session reads, shows its limits and advises by section.

`sddkit context` reads only Settings and Current state at the start of a session (the rest of the
constitution is read on demand), but `constitution_oversized` used to measure the whole file against
a fixed 24 KiB and say it was "read at every session". Now the part read at start has a limit of its
own (a warning), the whole file is a cold-file note against a ceiling the project may declare in
Settings, and the advice for a long table row depends on the section it sits in.
"""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _findings, _slim
from sdd_cli.cli import _doctor_payload, cmd_doctor


def _constitution(settings: str = "", hot_pad: int = 0, cold_pad: int = 0, cold_rows: str = "") -> str:
    hot_note = f"- **Note:** {'z' * hot_pad}\n" if hot_pad else ""
    cold = "".join(f"{'c' * 100}\n" for _ in range(cold_pad // 101))
    return (f"# Constitution\n\n## Settings\n\n- **Language:** en\n{settings}\n"
            f"## Current state\n\n- **State:** IMPLEMENTING\n{hot_note}\n"
            f"## 1. Vision\n\n{cold}\n## 3. Locked structural decisions\n\n{cold_rows}\n"
            "## 5. Stage index (CANONICAL)\n\n| Stage | Slug | Status |\n|---|---|---|\n| 001 | a | done |\n")


def _project(tmp_path: Path, text: str) -> Path:
    (tmp_path / ".sdd").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(text, encoding="utf-8", newline="\n")
    return tmp_path


def _finding(root: Path, code: str, path: str | None = None) -> dict | None:
    for item in _doctor_payload(root)["findings"]:
        if item["code"] == code and (path is None or item.get("path") == path):
            return item
    return None


CONSTITUTION = ".sdd/constitution.md"


# ---- B-01 ----------------------------------------------------------------------------------------

def test_a_big_cold_part_is_a_note_not_a_warning(tmp_path):
    root = _project(tmp_path, _constitution(cold_pad=40_000))
    assert _finding(root, "constitution_oversized") is None
    note = _finding(root, "cold_file_oversized", CONSTITUTION)
    assert note["severity"] == "note" and note["bytes"] > 40_000 and note["limit"] == 24 * 1024
    assert _doctor_payload(root)["status"] == 0


def test_the_note_names_both_sizes_and_the_biggest_sections(tmp_path):
    root = _project(tmp_path, _constitution(cold_pad=40_000))
    message, hint = _findings.describe(_finding(root, "cold_file_oversized", CONSTITUTION))
    assert "limit 24576" in message and "a session reads only" in message and "1. Vision" in message
    assert "sddkit doctor --slim" in hint and "Constitution max size" in hint


def test_a_big_start_of_the_file_is_a_warning(tmp_path):
    root = _project(tmp_path, _constitution(hot_pad=9_000))
    warn = _finding(root, "constitution_oversized")
    assert warn["severity"] == "warn" and warn["limit"] == 8 * 1024
    assert warn["bytes"] > 9_000 and warn["total"] >= warn["bytes"]
    message, hint = _findings.describe(warn)
    assert "every session reads" in message and "over 8192" in message
    assert "Current state" in hint


def test_a_start_of_the_file_under_the_limit_is_fine(tmp_path):
    root = _project(tmp_path, _constitution(hot_pad=3_000))
    assert _finding(root, "constitution_oversized") is None


def test_a_small_constitution_says_nothing(tmp_path):
    root = _project(tmp_path, _constitution())
    assert _finding(root, "constitution_oversized") is None
    assert _finding(root, "cold_file_oversized", CONSTITUTION) is None


# ---- B-02 ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [("75 KB", 76800), ("75KiB", 76800), ("1.5 MB", 1572864),
                                            ("24576", 24576), ("24576 bytes", 24576), ("lots", None), ("", None)])
def test_sizes_are_parsed(value, expected):
    assert _slim.parse_size(value) == expected


def test_the_project_ceiling_replaces_the_default_for_the_constitution(tmp_path):
    big = _constitution("- **Constitution max size:** 75 KB\n", cold_pad=40_000)
    assert _finding(_project(tmp_path, big), "cold_file_oversized", CONSTITUTION) is None
    small = _constitution("- **Constitution max size:** 10 KB\n", cold_pad=12_000)
    note = _finding(_project(tmp_path / "b", small), "cold_file_oversized", CONSTITUTION)
    assert note["limit"] == 10 * 1024


def test_the_project_ceiling_applies_to_roadmap_estimates_and_changelog(tmp_path):
    root = _project(tmp_path, _constitution("- **Cold file max size:** 60 KB\n"))
    (root / ".sdd" / "roadmap.md").write_text("x" * 50_000, encoding="utf-8")
    assert _finding(root, "cold_file_oversized", ".sdd/roadmap.md") is None  # 48 KB default would note it
    root = _project(tmp_path / "b", _constitution("- **Cold file max size:** 10 KB\n"))
    (root / ".sdd" / "roadmap.md").write_text("x" * 12_000, encoding="utf-8")
    note = _finding(root, "cold_file_oversized", ".sdd/roadmap.md")
    assert note["limit"] == 10 * 1024
    assert "limit 10240" in _findings.describe(note)[0]


def test_the_default_for_a_cold_file_is_unchanged(tmp_path):
    root = _project(tmp_path, _constitution())
    (root / ".sdd" / "CHANGELOG.md").write_text("x" * 50_000, encoding="utf-8")
    note = _finding(root, "cold_file_oversized", ".sdd/CHANGELOG.md")
    assert note["limit"] == 48 * 1024
    assert _findings.describe(note)[1].startswith("keep it cold")


def test_an_invalid_ceiling_is_ignored(tmp_path):
    root = _project(tmp_path, _constitution("- **Constitution max size:** plenty\n", cold_pad=40_000))
    assert _finding(root, "cold_file_oversized", CONSTITUTION)["limit"] == 24 * 1024


def test_doctor_slim_reports_the_project_ceiling_and_the_start_of_the_file(tmp_path, capsys):
    root = _project(tmp_path, _constitution("- **Constitution max size:** 75 KB\n", cold_pad=40_000))
    cmd_doctor(types.SimpleNamespace(path=str(root), json=True, slim=True, all=False))
    plan = json.loads(capsys.readouterr().out)
    assert plan["limit"] == 75 * 1024 and plan["over_by"] == 0
    assert plan["hot"]["limit"] == 8 * 1024 and 0 < plan["hot"]["bytes"] < 8 * 1024
    cmd_doctor(types.SimpleNamespace(path=str(root), json=False, slim=True, all=False))
    assert "read at the start of every session" in capsys.readouterr().out


# ---- B-03 ----------------------------------------------------------------------------------------

ROW = "| D-001 | decision | " + "x" * 700 + " |"


def _advice(tmp_path: Path, section_rows: str, heading: str = "3. Locked structural decisions") -> str:
    text = _constitution(cold_rows=section_rows).replace("## 3. Locked structural decisions", f"## {heading}")
    return _findings.describe(_finding(_project(tmp_path, text), "long_table_cell"))[1]


def test_a_long_locked_decision_goes_to_the_changelog_not_the_backlog(tmp_path):
    advice = _advice(tmp_path, ROW)
    assert "CHANGELOG.md" in advice and "never archived to backlog.md" in advice


def test_a_long_stage_index_row_goes_to_the_backlog(tmp_path):
    advice = _advice(tmp_path, ROW, heading="5. Stage index")
    assert advice.endswith("backlog.md") and "CHANGELOG" not in advice


def test_a_section_without_a_rule_gets_a_neutral_line(tmp_path):
    advice = _advice(tmp_path, ROW, heading="4. Open questions")
    assert "the file that holds it" in advice


def test_the_finding_names_its_section_and_destination(tmp_path):
    text = _constitution(cold_rows=ROW)
    item = _finding(_project(tmp_path, text), "long_table_cell")
    assert item["section"] == "3. Locked structural decisions" and item["destination"] == "CHANGELOG.md"
    assert _findings.location(item).endswith("B") and "section 3. Locked" in _findings.location(item)
