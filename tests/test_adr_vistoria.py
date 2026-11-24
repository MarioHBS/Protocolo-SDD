"""4.10.0, fixes from the final audit (vistoria): each test reproduces what the audit found.

B1 `adr init` rewrote section 7 even when it created nothing; I1 `--dry-run` left a state file;
I2 superseding left section 3 pointing at the old record; I3 `adr init` made a second record for a
decision that already had one; I4 superseding rewrote an owner's file without a backup and could
corrupt bytes; M1-M11 smaller reads, validations and the interview resume.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest
from test_adr import CONSTITUTION, _files, _new, _project
from test_adr_init import (
    ROWS,
    _answers,
    _console,
    _constitution,
    _init,
    _snapshot,
    _text,
)

from sdd_cli import _adr, _adr_init, _decisions, _docs_plan
from sdd_cli.cli import cmd_adr

# ------------------------------------------------------------------ I1


def test_a_dry_run_interview_leaves_no_state_file(tmp_path, monkeypatch):
    root = _project(tmp_path, _constitution(ROWS[:2]))
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: True))
    scripted = _console(["n", "n"])
    monkeypatch.setattr(_docs_plan, "Console", lambda: scripted)
    before = _snapshot(root)
    _init(root, dry_run=True)
    assert _snapshot(root) == before
    assert not (root / ".sdd" / ".adr-interview.json").exists()


# ------------------------------------------------------------------ I2


def test_superseding_with_decision_moves_the_section_3_link_to_the_new_record(tmp_path):
    root = _project(tmp_path)
    _new(root, "Use Postgres", decision="D-001")
    _new(root, "Use MySQL", decision="D-001", supersedes=["ADR-001"])
    cells = {r["id"]: r["record"] for r in _decisions.rows(_text(root))}
    assert cells["D-001"] == "[ADR-002](decisions/ADR-002-use-mysql.md)"


def test_a_cell_holding_some_other_value_is_still_left_alone_when_superseding(tmp_path):
    root = _project(tmp_path, CONSTITUTION.replace("2026-01-10 |  |", "2026-01-10 | DOC-007 |"))
    _new(root, "Use Postgres")
    _new(root, "Use MySQL", decision="D-001", supersedes=["ADR-001"])
    assert _decisions.rows(_text(root))[0]["record"] == "DOC-007"


# ------------------------------------------------------------------ I3


def test_init_links_a_record_that_adr_new_already_made_instead_of_making_a_second(tmp_path):
    old_table = _constitution(ROWS[:2], section_7="- **Decision records:** internal")
    root = _project(tmp_path, old_table)
    _new(root, "Use Postgres", decision="D-001")  # the table has no Record column
    assert _files(root) == ["ADR-001-use-postgres.md"]
    analysis = _adr_init.analyze(root)
    assert [c["id"] for c in _adr_init.pending(analysis)] == ["D-002"]
    _init(root, _answers(tmp_path, records=[{"decision": "D-001"}, {"decision": "D-002"}]))
    assert _files(root) == ["ADR-001-use-postgres.md", "ADR-002-queue-none.md"]  # none for D-001
    cells = {r["id"]: r["record"] for r in _decisions.rows(_text(root))}
    assert cells["D-001"] == "[ADR-001](decisions/ADR-001-use-postgres.md)"


def test_init_adds_the_column_for_a_record_that_exists_even_when_no_new_one_is_made(tmp_path):
    root = _project(tmp_path, _constitution(ROWS[:2], section_7="- **Decision records:** internal"))
    _new(root, "Use Postgres", decision="D-001")
    _init(root, _answers(tmp_path, records=[]))
    assert _decisions.has_record_column(_text(root)) is True
    assert _decisions.rows(_text(root))[0]["record"] == "[ADR-001](decisions/ADR-001-use-postgres.md)"


def test_a_superseded_record_does_not_count_as_covering_its_row(tmp_path):
    root = _project(tmp_path, _constitution(ROWS[:1], section_7="- **Decision records:** internal"))
    _new(root, "Old", decision="D-001", status="substituída")
    assert [c["id"] for c in _adr_init.pending(_adr_init.analyze(root))] == ["D-001"]


# ------------------------------------------------------------------ I4


def test_superseding_backs_up_the_old_record_and_changes_only_two_lines(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    old = root / ".sdd" / "decisions" / "ADR-001-mine.md"
    original = ("---\r\nid: ADR-001\r\nstatus: aceita\r\n# nota do dono: revisar\r\ndecision: D-001\r\n---\r\n"
                "# ADR-001 — Minha decisão\r\n\r\nCorpo com acentuação.\r\n").encode()
    old.write_bytes(original)
    _new(root, "Next", supersedes=["ADR-001"])
    after = old.read_bytes().decode("utf-8")
    assert "# nota do dono: revisar" in after and "Corpo com acentuação." in after
    assert "status: substituída" in after and "superseded_by: [ADR-002]" in after
    assert after.count("\r\n") == after.count("\n")  # CRLF kept
    (backup,) = list((root / ".sdd" / ".pre-fix-backup").glob("*/decisions/ADR-001-mine.md"))
    assert backup.read_bytes() == original


def test_a_record_that_is_not_utf8_is_refused_before_a_number_is_reserved(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    old = root / ".sdd" / "decisions" / "ADR-001-latin.md"
    raw = "---\nid: ADR-001\nstatus: aceita\n---\n# decisão\n".encode("cp1252")
    old.write_bytes(raw)
    with pytest.raises(SystemExit):
        _new(root, "Next", supersedes=["ADR-001"])
    assert old.read_bytes() == raw and not (root / ".sdd" / ".reservations.json").exists()


def test_a_record_without_frontmatter_cannot_be_superseded(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    (root / ".sdd" / "decisions" / "ADR-001-plain.md").write_text("# plain\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        _new(root, "Next", supersedes=["ADR-001"])


# ----------------------------------------------------- frontmatter parser (M7)


@pytest.mark.parametrize("raw, expected", [
    ("aceita  # a note", "aceita"), ("'aceita'", "aceita"), ('"a: b"', "a: b"),
    ('["a, b", c]', ["a, b", "c"]), ("[ADR-001]  # x", ["ADR-001"]), ("[]", [])])
def test_frontmatter_values_are_read_the_way_an_editor_writes_them(raw, expected):
    assert _adr._scalar(raw) == expected


def test_a_record_saved_with_a_bom_is_read(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    (root / ".sdd" / "decisions" / "ADR-001-bom.md").write_bytes(
        b"\xef\xbb\xbf---\nid: ADR-001\nstatus: aceita\n---\n# x\n")
    (record,) = _adr.list_adrs(root)
    assert record.error is None and record.status == "aceita"


# ------------------------------------------------------- section 3 and 7 (M2, M3)


def test_a_reordered_table_is_read_by_its_labels(tmp_path):
    text = ("## 3. Locked structural decisions\n\n| ID | Decision | Locked on | Choice | Rationale |\n"
            "|----|----------|-----------|--------|-----------|\n| D-001 | db | 2026-01-01 | Postgres | tx |\n\n"
            "## 7. Project decision conventions\n\n- **Decision records:** internal\n")
    root = _project(tmp_path, text)
    (candidate,) = _adr_init.analyze(root)["candidates"]
    assert (candidate["choice"], candidate["rationale"], candidate["locked_on"], candidate["locked"]) == (
        "Postgres", "tx", "2026-01-01", True)


@pytest.mark.parametrize("line, mode", [
    ("- **Decision records:** interno", "internal"),
    ("- **Decision Records:** externo — docs/decisoes/", "external"),
    ("- **decision records:** Internal", "internal")])
def test_section_7_accepts_portuguese_values_and_any_case(line, mode):
    assert _decisions.decision_records(f"## 7. Project decision conventions\n\n{line}\n")["mode"] == mode


def test_the_text_of_a_not_applicable_section_7_is_kept_when_it_is_replaced():
    text = "## 7. Project decision conventions\n\n- **Decision records:** not applicable — a decision of 2025\n"
    assert "previously: not applicable — a decision of 2025" in _decisions.set_decision_records(
        text, "internal")


# ------------------------------------------------- answers file and plan (M1, M5, M10)


def test_map_must_point_at_rows_of_section_3(tmp_path, capsys):
    root = _project(tmp_path)
    (root / "docs").mkdir()
    with pytest.raises(SystemExit):
        _init(root, _answers(tmp_path, strategy="link", path="docs", map={"ADR-002": "D-999"}))
    assert "not in section 3: D-999" in capsys.readouterr().err


def test_new_records_are_numbered_after_adr_files_that_live_outside(tmp_path):
    root = _project(tmp_path)
    folder = root / "docs" / "adr"
    folder.mkdir(parents=True)
    (folder / "ADR-001-x.md").write_text("# ADR-001 — X\n", encoding="utf-8")
    (folder / "ADR-002-y.md").write_text("# ADR-002 — Y\n", encoding="utf-8")
    _init(root, _answers(tmp_path, strategy="rows", records=[{"decision": "D-001"}]))
    assert _files(root) == ["ADR-003-database-postgres.md"]


def test_a_number_taken_while_the_plan_was_made_aborts_before_anything_is_written(tmp_path):
    root = _project(tmp_path)
    analysis = _adr_init.analyze(root)
    answers = _adr_init.validate(json.loads(_answers(tmp_path, records=[{"decision": "D-001"}]).read_text(
        encoding="utf-8")), analysis, root)
    plan = _adr_init.build_plan(root, analysis, answers)
    _new(root, "Someone else was faster")  # takes ADR-001 between the plan and the write
    before = _snapshot(root)
    with pytest.raises(ValueError, match="taken by another session"):
        _adr_init.apply(root, plan)
    assert _snapshot(root) == before


def test_a_link_is_not_written_for_a_file_that_could_not_be_created(tmp_path):
    root = _project(tmp_path)
    analysis = _adr_init.analyze(root)
    answers = _adr_init.validate(json.loads(_answers(tmp_path, records=[{"decision": "D-001"}]).read_text(
        encoding="utf-8")), analysis, root)
    plan = _adr_init.build_plan(root, analysis, answers)
    target = root / plan["create"][0]["path"]
    target.parent.mkdir(parents=True)
    target.write_text("mine\n", encoding="utf-8")  # the very file name appears after the plan
    result = _adr_init.apply(root, plan)
    assert result["skipped_existing"] and target.read_text(encoding="utf-8") == "mine\n"
    assert all(r["record"] == "" for r in _decisions.rows(_text(root)))


# ------------------------------------------------------------ interview (M11)


def test_resume_keeps_the_rows_already_answered(tmp_path):
    root = _project(tmp_path, _constitution(ROWS[:3]))
    analysis = _adr_init.analyze(root)
    store: dict = {}

    def keep(state):
        store["state"] = json.loads(json.dumps(state))  # what the file on disk would hold

    # D-001: yes (accepted, nothing else); D-002: no; the input ends at the question about D-003
    with pytest.raises(_docs_plan.InterviewAborted):
        _adr_init.run_interview(root, analysis, _console(["y", "aceita", "", "", "", "n"]), on_step=keep)
    assert store["state"]["answers"]["asked"] == ["D-001", "D-002"]
    assert "records" not in store["state"]["done"]  # the step never finished, yet two rows are kept
    asked: list[str] = []
    answers = _adr_init.run_interview(root, analysis, _console(["n"], asked), state=store["state"])
    assert [r["decision"] for r in answers["records"]] == ["D-001"]
    assert sum("deserve a record" in p for p in asked) == 1  # only the row that was never answered


# --------------------------------------------------------------- doctor wording (M8)


def test_the_missing_folder_note_counts_decisions_not_only_locked_ones(tmp_path):
    from sdd_cli import _findings
    from sdd_cli.cli import _doctor_payload
    root = _project(tmp_path, _constitution(ROWS, section_7="- **Decision records:** internal"))
    (finding,) = [f for f in _doctor_payload(root)["findings"] if f["code"] == "decisions_dir_missing"]
    assert "5 decision(s) in section 3" in _findings.describe(finding)[0]


def test_the_command_group_is_unchanged_for_index(tmp_path):
    root = _project(tmp_path)
    cmd_adr(types.SimpleNamespace(path=str(root), adr_command="index", check=False, json=False))
    assert Path(root / ".sdd").is_dir()
