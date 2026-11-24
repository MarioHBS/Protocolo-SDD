"""4.10.0, M-05: the doctor checks the link between a D-NNN row, its record and the index.

One fixture per check. The rule that frames them: a project that keeps no ADRs by choice only
ever gets a note, never a warning or an error.
"""

from __future__ import annotations

import types
from pathlib import Path

from sdd_cli import _adr, _findings
from sdd_cli.cli import _doctor_payload, cmd_doctor

SECTION_3 = """\
## 3. Locked structural decisions

| ID    | Decision | Choice | Rationale | Locked on | Record |
|-------|----------|--------|-----------|-----------|--------|
| D-001 | database | Postgres | transactions | 2026-01-10 |  |
| D-002 | queue | none | later | 2026-01-11 |  |

"""

INDEX = """\
## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Depends on |
|-------|------|--------|------------|
| 001 | first | done | — |

"""


def _project(tmp_path: Path, field: str | None = "- **Decision records:** internal",
             section_3: str = SECTION_3) -> Path:
    section_7 = "## 7. Project decision conventions\n\n" + (field + "\n" if field else "")
    (tmp_path / ".sdd").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        "## Settings\n\n- **Language:** en\n\n" + section_3 + INDEX + section_7, encoding="utf-8", newline="\n")
    return tmp_path


def _found(root: Path, code: str) -> list[dict]:
    return [f for f in _doctor_payload(root)["findings"] if f["code"] == code]


def _adr_codes(root: Path) -> list[str]:
    return [f["code"] for f in _doctor_payload(root)["findings"]
            if f["code"].startswith(("adr_", "decision", "decisions_"))]


def _record(root: Path, title: str = "Use Postgres", **kw) -> Path:
    result = _adr.new_adr(root, title, **kw)
    return root / result["path"]


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")


def test_a_clean_project_with_records_has_no_adr_finding(tmp_path):
    root = _project(tmp_path)
    _record(root, decision="D-001")
    assert _adr_codes(root) == []


def test_decisions_without_the_folder_are_one_note_never_a_warning(tmp_path):
    root = _project(tmp_path)
    (finding,) = _found(root, "decisions_dir_missing")
    assert finding["severity"] == "note" and finding["count"] == 2
    message, hint = _findings.describe(finding)
    assert "2 decision(s) in section 3" in message and "sddkit adr init" in hint
    assert _doctor_payload(root)["status"] == 0


def test_not_applicable_and_external_silence_the_missing_folder_note(tmp_path):
    for field in ("- **Decision records:** not applicable",
                  "- **Decision records:** external — docs/decisoes/"):
        root = _project(tmp_path / field.split()[3].strip("*:"), field)
        (root / "docs" / "decisoes").mkdir(parents=True)
        assert _found(root, "decisions_dir_missing") == []


def test_the_template_placeholder_row_is_not_a_decision(tmp_path):
    placeholder = SECTION_3.split("| D-001")[0] + "| D-001 | [e.g. database] | [...] | [...] | [date] |  |\n\n"
    assert _found(_project(tmp_path, section_3=placeholder), "decisions_dir_missing") == []


def test_free_text_written_before_the_field_had_a_format_still_gets_only_the_note(tmp_path):
    root = _project(tmp_path, "- **Decision records (ADRs):** ADRs in DOC-007; amendments as 'Amendment N'")
    assert _adr_codes(root) == ["decisions_dir_missing"]


def test_a_project_without_section_3_or_section_7_has_nothing_to_say(tmp_path):
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_text("## Settings\n\n- **Language:** en\n", encoding="utf-8")
    assert _adr_codes(tmp_path) == []


def test_duplicate_ids_are_an_error(tmp_path):
    root = _project(tmp_path)
    first = _record(root, decision="D-001")
    twin = first.with_name("ADR-001-another-file.md")
    twin.write_text(first.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    _adr.write_index(root)
    (finding,) = _found(root, "adr_duplicate_id")
    assert finding["severity"] == "error" and finding["adr"] == "ADR-001"
    assert len(finding["paths"]) == 2
    assert _doctor_payload(root)["status"] == 1


def test_a_frontmatter_id_that_two_files_share_is_a_duplicate_too(tmp_path):
    root = _project(tmp_path)
    _record(root, "One", decision="D-001")
    second = _record(root, "Two", decision="D-002")
    _edit(second, "id: ADR-002", "id: ADR-001")
    assert [f["adr"] for f in _found(root, "adr_duplicate_id")] == ["ADR-001"]


def test_a_status_outside_the_cycle_is_a_warning(tmp_path):
    root = _project(tmp_path)
    record = _record(root, decision="D-001")
    _edit(record, "status: proposta", "status: draft")
    _adr.write_index(root)
    (finding,) = _found(root, "adr_status_invalid")
    assert finding["severity"] == "warn" and "'draft'" in finding["detail"]


def test_a_record_with_no_frontmatter_is_reported_not_fatal(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    (root / ".sdd" / "decisions" / "ADR-001-hand-made.md").write_text("# Hand made\n", encoding="utf-8")
    (finding,) = _found(root, "adr_status_invalid")
    assert finding["detail"] == "no frontmatter"


def test_a_record_that_names_no_decision_or_a_missing_row(tmp_path):
    root = _project(tmp_path)
    _record(root, "No row named")
    _record(root, "Wrong row", decision="D-009")
    details = sorted(f["detail"] for f in _found(root, "adr_without_decision"))
    assert details == ["D-009 is not a row of section 3", "its frontmatter names no D-NNN"]


def test_a_row_that_points_at_a_record_that_is_gone(tmp_path):
    root = _project(tmp_path)
    record = _record(root, decision="D-001")
    _edit(root / ".sdd" / "constitution.md", "2026-01-10 |  |",
          f"2026-01-10 | [ADR-001](decisions/{record.name}) |")
    assert _found(root, "decision_row_adr_missing") == []  # the record is there
    record.unlink()
    _adr.write_index(root)
    (finding,) = _found(root, "decision_row_adr_missing")
    assert (finding["decision"], finding["adr"]) == ("D-001", "ADR-001")


def test_implemented_needs_to_say_where(tmp_path):
    root = _project(tmp_path)
    record = _record(root, decision="D-001", status="implementada")
    assert [f["adr"] for f in _found(root, "adr_implemented_without_ref")] == ["ADR-001"]
    _edit(record, "implemented_in:", "implemented_in: 003-auth")
    _adr.write_index(root)
    assert _found(root, "adr_implemented_without_ref") == []


def test_superseded_needs_an_existing_successor(tmp_path):
    root = _project(tmp_path)
    old = _record(root, "Old", decision="D-001", status="substituída")
    (finding,) = _found(root, "adr_superseded_without_successor")
    assert "empty" in finding["detail"]
    _edit(old, "superseded_by: []", "superseded_by: [ADR-007]")
    (finding,) = _found(root, "adr_superseded_without_successor")
    assert "ADR-007" in finding["detail"]


def test_superseding_with_the_command_leaves_nothing_to_report(tmp_path):
    root = _project(tmp_path)
    _record(root, "Old", decision="D-001")
    _record(root, "New", decision="D-001", supersedes=["ADR-001"])
    assert _adr_codes(root) == []


def test_an_index_that_no_longer_matches_is_a_warning_and_index_fixes_it(tmp_path):
    root = _project(tmp_path)
    record = _record(root, decision="D-001")
    _edit(record, "status: proposta", "status: aceita")
    (finding,) = _found(root, "adr_index_stale")
    assert finding["severity"] == "warn" and _findings.describe(finding)[1] == "sddkit adr index"
    _adr.write_index(root)
    assert _found(root, "adr_index_stale") == []


def test_a_missing_index_counts_as_stale(tmp_path):
    root = _project(tmp_path)
    _record(root, decision="D-001")
    (root / ".sdd" / "decisions" / "README.md").unlink()
    assert len(_found(root, "adr_index_stale")) == 1


def test_external_mode_needs_the_path_to_exist(tmp_path):
    root = _project(tmp_path, "- **Decision records:** external — docs/decisoes/")
    (finding,) = _found(root, "adr_external_path_missing")
    assert finding["severity"] == "warn" and "docs/decisoes/ does not exist" in finding["detail"]
    (root / "docs" / "decisoes").mkdir(parents=True)
    assert _found(root, "adr_external_path_missing") == []


def test_external_mode_with_no_path_and_with_a_url(tmp_path):
    root = _project(tmp_path, "- **Decision records:** external")
    assert len(_found(root, "adr_external_path_missing")) == 1
    root = _project(tmp_path / "url", "- **Decision records:** external — https://wiki.example/adr")
    assert _found(root, "adr_external_path_missing") == []


def test_in_external_mode_a_record_cell_may_cite_external_ids(tmp_path):
    root = _project(tmp_path, "- **Decision records:** external — docs/decisoes/",
                    SECTION_3.replace("2026-01-10 |  |", "2026-01-10 | ADR-004 |"))
    (root / "docs" / "decisoes").mkdir(parents=True)
    assert _adr_codes(root) == []


def test_the_doctor_prints_the_new_findings_with_their_command(tmp_path, capsys):
    root = _project(tmp_path)
    try:
        cmd_doctor(types.SimpleNamespace(path=str(root), json=False, slim=False, all=False))
    except SystemExit:
        pass
    out = capsys.readouterr().out
    assert "decisions_dir_missing" in out or "no .sdd/decisions/ folder" in out
