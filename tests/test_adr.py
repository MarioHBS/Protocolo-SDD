"""4.10.0, M-01 and M-02: decision records in .sdd/decisions/, their numbering and their index.

The commands are called in-process with a namespace (as in test_document.py), on a project
folder made here: a constitution with a section 3 table is all they need.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _adr, _decisions
from sdd_cli.cli import cmd_adr

CONSTITUTION = """\
# Constitution

## 3. Locked structural decisions

| ID    | Decision | Choice | Rationale | Locked on | Record |
|-------|----------|--------|-----------|-----------|--------|
| D-001 | database | Postgres | transactions | 2026-01-10 |  |
| D-002 | queue | none | not needed yet | 2026-01-11 |  |

## 7. Project decision conventions

- **Decision records:** internal
"""


def _project(tmp_path: Path, constitution: str = CONSTITUTION, newline: str | None = None) -> Path:
    (tmp_path / ".sdd").mkdir()
    (tmp_path / ".sdd" / "constitution.md").write_text(constitution, encoding="utf-8", newline=newline)
    return tmp_path


def _new(root: Path, title: str = "Use Postgres", **kw):
    values = dict(path=str(root), adr_command="new", title=title, decision=None, stage=None,
                  status=_adr.PROPOSED, supersedes=None, context=None, alternative=None,
                  dry_run=False, json=False)
    values.update(kw)
    cmd_adr(types.SimpleNamespace(**values))


def _index(root: Path, **kw):
    values = dict(path=str(root), adr_command="index", check=False, json=False)
    values.update(kw)
    cmd_adr(types.SimpleNamespace(**values))


def _files(root: Path) -> list[str]:
    return sorted(p.name for p in (root / ".sdd" / "decisions").glob("ADR-*.md"))


# ------------------------------------------------------------------- M-01

def test_first_record_creates_the_folder_the_file_and_the_index(tmp_path):
    root = _project(tmp_path)
    _new(root, "Use Postgres", stage="002-data", context="Need transactions",
         alternative=["SQLite: one writer only"])
    assert _files(root) == ["ADR-001-use-postgres.md"]
    text = (root / ".sdd" / "decisions" / "ADR-001-use-postgres.md").read_text(encoding="utf-8")
    meta, _, body = _adr.split(text)
    assert meta["id"] == "ADR-001" and meta["status"] == "proposta" and meta["stage"] == "002-data"
    assert meta["reconstructed"] is False and meta["supersedes"] == []
    assert "# ADR-001 — Use Postgres" in body and "Need transactions" in body
    assert "SQLite: one writer only" in body
    assert "ARCHITECTURE DECISION RECORD" not in text  # the template's leading comment is dropped
    assert (root / ".sdd" / "decisions" / "README.md").is_file()


def test_numbers_are_never_reused_even_after_the_file_is_deleted(tmp_path):
    root = _project(tmp_path)
    for title in ("One", "Two", "Three"):
        _new(root, title)
    (root / ".sdd" / "decisions" / "ADR-002-two.md").unlink()
    _new(root, "Four")
    assert _files(root) == ["ADR-001-one.md", "ADR-003-three.md", "ADR-004-four.md"]
    # deleting the LAST record must not free its number either: the ledger remembers it
    (root / ".sdd" / "decisions" / "ADR-004-four.md").unlink()
    _new(root, "Five")
    assert _files(root)[-1] == "ADR-005-five.md"


def test_two_reservations_in_a_row_get_different_numbers(tmp_path):
    root = _project(tmp_path)
    assert _adr.reserve_number(root) == 1
    assert _adr.reserve_number(root) == 2
    ledger = json.loads((root / ".sdd" / ".reservations.json").read_text(encoding="utf-8"))
    assert [e["number"] for e in ledger["sequences"]["adr"]] == ["001", "002"]


def test_dry_run_reserves_nothing_and_writes_nothing(tmp_path, capsys):
    root = _project(tmp_path)
    _new(root, "Use Postgres", dry_run=True, decision="D-001")
    assert not (root / ".sdd" / "decisions").exists()
    assert not (root / ".sdd" / ".reservations.json").exists()
    assert not (root / ".sdd" / ".pre-fix-backup").exists()
    assert (root / ".sdd" / "constitution.md").read_text(encoding="utf-8") == CONSTITUTION
    assert "would create .sdd/decisions/ADR-001-use-postgres.md" in capsys.readouterr().out


def test_frontmatter_round_trips_values_that_need_quoting():
    meta = {"id": "ADR-001", "status": "aceita", "source": "DOC-007: section 3 # note",
            "supersedes": ["ADR-000"], "reconstructed": True, "implemented_in": ""}
    text = _adr.render_frontmatter(meta) + "\nbody\n"
    parsed, _, body = _adr.split(text)
    assert parsed == meta and body == "\nbody\n"


def test_status_outside_the_cycle_is_refused(tmp_path):
    root = _project(tmp_path)
    with pytest.raises(SystemExit):
        _new(root, "X", status="draft")
    assert not (root / ".sdd" / "decisions").exists()


def test_unaccented_substituida_is_the_same_status():
    assert _adr.normalize_status("substituida") == "substituída"
    assert _adr.normalize_status("Aceita") == "aceita"
    assert _adr.normalize_status("draft") is None


def test_superseding_changes_only_the_frontmatter_of_the_old_record(tmp_path):
    root = _project(tmp_path)
    _new(root, "Use Postgres")
    old = root / ".sdd" / "decisions" / "ADR-001-use-postgres.md"
    before_body = _adr.split(old.read_text(encoding="utf-8"))[2]
    _new(root, "Use CockroachDB", supersedes=["ADR-001"])
    meta, _, body = _adr.split(old.read_text(encoding="utf-8"))
    assert meta["status"] == "substituída" and meta["superseded_by"] == ["ADR-002"]
    assert body == before_body
    new_meta = _adr.split((root / ".sdd" / "decisions" / "ADR-002-use-cockroachdb.md")
                          .read_text(encoding="utf-8"))[0]
    assert new_meta["supersedes"] == ["ADR-001"]


def test_superseding_an_unknown_record_is_refused_before_anything_is_written(tmp_path):
    root = _project(tmp_path)
    with pytest.raises(SystemExit):
        _new(root, "X", supersedes=["ADR-009"])
    assert not (root / ".sdd" / "decisions").exists()
    assert not (root / ".sdd" / ".reservations.json").exists()


def test_a_bad_decision_id_is_refused(tmp_path):
    root = _project(tmp_path)
    with pytest.raises(SystemExit):
        _new(root, "X", decision="decision one")


def test_the_projects_own_template_is_used_when_it_exists(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "templates").mkdir()
    (root / ".sdd" / "templates" / "adr.template.md").write_text(
        "# {{ID}}: {{TITLE}}\n\nOur layout.\n", encoding="utf-8")
    _new(root, "Use Postgres")
    text = (root / ".sdd" / "decisions" / "ADR-001-use-postgres.md").read_text(encoding="utf-8")
    assert "# ADR-001: Use Postgres" in text and "Our layout." in text


def test_a_plain_record_with_no_frontmatter_is_listed_not_fatal(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    (root / ".sdd" / "decisions" / "ADR-007-hand-made.md").write_text("# Hand made\n", encoding="utf-8")
    (record,) = _adr.list_adrs(root)
    assert record.error == "no frontmatter" and record.number == 7 and record.id == "ADR-007"
    _new(root, "Next")
    assert "ADR-008-next.md" in _files(root)


# -------------------------------------- M-01/M-02: the link in section 3

def test_new_with_decision_fills_the_record_cell_and_keeps_a_backup(tmp_path):
    root = _project(tmp_path)
    _new(root, "Use Postgres", decision="D-001")
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert "[ADR-001](decisions/ADR-001-use-postgres.md)" in text
    assert [r["record"] for r in _decisions.rows(text)] == [
        "[ADR-001](decisions/ADR-001-use-postgres.md)", ""]
    (backup,) = list((root / ".sdd" / ".pre-fix-backup").glob("*/constitution.md"))
    assert backup.read_text(encoding="utf-8") == CONSTITUTION


def test_the_constitution_keeps_its_crlf_line_endings(tmp_path):
    root = _project(tmp_path, CONSTITUTION.replace("\n", "\r\n"), newline="")
    _new(root, "Use Postgres", decision="D-002")
    raw = (root / ".sdd" / "constitution.md").read_bytes()
    assert b"decisions/ADR-001-use-postgres.md" in raw
    assert raw.count(b"\r\n") == raw.count(b"\n")


def test_a_section_3_table_without_the_column_is_left_alone(tmp_path, capsys):
    old = CONSTITUTION.replace(" | Record |", " |").replace("|--------|", "|").replace(" |  |\n", " |\n")
    root = _project(tmp_path, old)
    _new(root, "Use Postgres", decision="D-001")
    assert (root / ".sdd" / "constitution.md").read_text(encoding="utf-8") == old
    assert not (root / ".sdd" / ".pre-fix-backup").exists()
    assert "no Record column" in capsys.readouterr().out
    assert _files(root) == ["ADR-001-use-postgres.md"]


def test_a_filled_record_cell_is_not_overwritten(tmp_path):
    root = _project(tmp_path, CONSTITUTION.replace("2026-01-10 |  |", "2026-01-10 | DOC-007 |"))
    _new(root, "Use Postgres", decision="D-001")
    assert "DOC-007" in (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")


def test_a_decision_with_no_row_is_only_a_note(tmp_path, capsys):
    root = _project(tmp_path)
    _new(root, "Use Postgres", decision="D-009")
    assert "no row D-009" in capsys.readouterr().out
    assert _files(root) == ["ADR-001-use-postgres.md"]


# ------------------------------------------------------------------- M-02

def test_index_lists_every_record_and_is_identical_when_nothing_changed(tmp_path, capsys):
    root = _project(tmp_path)
    _new(root, "Use Postgres", decision="D-001", stage="002-data")
    _new(root, "Queue | later", decision="D-002")
    index = root / ".sdd" / "decisions" / "README.md"
    first = index.read_bytes()
    text = first.decode("utf-8")
    assert "| [ADR-001](ADR-001-use-postgres.md) | Use Postgres | proposta | D-001 | 002-data |" in text
    assert "Queue \\| later" in text  # a pipe in a title cannot break the table
    assert text.index("ADR-001") < text.index("ADR-002")
    assert b"\r" not in first
    capsys.readouterr()
    _index(root)
    assert index.read_bytes() == first
    assert "already current" in capsys.readouterr().out


def test_index_follows_a_status_edited_by_hand(tmp_path):
    root = _project(tmp_path)
    _new(root, "Use Postgres")
    record = root / ".sdd" / "decisions" / "ADR-001-use-postgres.md"
    record.write_text(record.read_text(encoding="utf-8").replace("status: proposta", "status: aceita"),
                      encoding="utf-8")
    assert _adr.index_is_stale(root)
    with pytest.raises(SystemExit):
        _index(root, check=True)
    _index(root)
    assert "| aceita |" in (root / ".sdd" / "decisions" / "README.md").read_text(encoding="utf-8")
    assert not _adr.index_is_stale(root)
    _index(root, check=True)


def test_index_in_a_project_with_no_records_creates_nothing(tmp_path, capsys):
    root = _project(tmp_path)
    _index(root)
    assert not (root / ".sdd" / "decisions").exists()
    assert "nothing written" in capsys.readouterr().out


def test_an_old_section_3_table_is_still_read(tmp_path):
    old = ("## 3. Locked structural decisions\n\n| ID | Decision | Choice | Rationale | Locked on |\n"
           "|----|----------|--------|-----------|-----------|\n| D-001 | a | b | c | d |\n\n## 4. Open\n")
    assert _decisions.has_record_column(old) is False
    assert _decisions.real_ids(old) == ["D-001"]
    assert _decisions.rows(old)[0]["record"] == ""


def test_the_template_placeholder_row_is_not_a_decision():
    text = ("## 3. Locked structural decisions\n\n| ID | Decision | Choice | Rationale | Locked on |\n"
            "|----|----------|--------|-----------|-----------|\n| D-001 | [e.g. database] | [...] | [...] | [date] |\n")
    assert _decisions.rows(text)[0]["placeholder"] is True
    assert _decisions.real_ids(text) == []


def test_adding_the_record_column_is_idempotent_and_keeps_line_endings():
    old = ("## 3. Locked structural decisions\r\n\r\n| ID | Decision | Choice | Rationale | Locked on |\r\n"
           "|----|----------|--------|-----------|-----------|\r\n| D-001 | a | b | c | d |\r\n\r\n## 4. Q\r\n")
    updated, changed = _decisions.add_record_column(old)
    assert changed and _decisions.has_record_column(updated) is True
    assert updated.count("\r\n") == old.count("\r\n") and "\n" not in updated.replace("\r\n", "")
    assert [len(r["cells"]) for r in _decisions.rows(updated)] == [6]
    assert _decisions.add_record_column(updated) == (updated, False)


# ------------------------------------------------------------- section 7

@pytest.mark.parametrize("line, mode, path", [
    ("- **Decision records:** internal", "internal", ""),
    ("- **Decision records:** external — docs/decisoes/", "external", "docs/decisoes/"),
    ("- **Decision records:** external (`docs/adr`)", "external", "docs/adr"),
    ("- **Decision records (ADRs):** not applicable", "none", ""),
    ("- **Decision records (ADRs):** Não aplicável; decisões ficam na seção 3", "none", ""),
    ("- **Decision records (ADRs):** não há ADRs formais; decisões vivem só em §3", "none", ""),
    ("- **Decision records (ADRs):** No ADRs, decisions live in section 3", "none", ""),
    ("- **Decision records (ADRs):** ADRs in DOC-007; amendments as 'Amendment N'", "legacy", ""),
    ("- **Decision records (ADRs):** [where they live, format]", "unset", ""),
])
def test_section_7_field_modes(line, mode, path):
    found = _decisions.decision_records(f"## 7. Project decision conventions\n\n{line}\n- **Other:** x\n")
    assert (found["mode"], found["path"]) == (mode, path)


def test_section_7_field_set_keeps_the_text_it_replaces():
    text = ("## 7. Project decision conventions\n\n- **Decision records (ADRs):** ADRs in DOC-007;\n"
            "  amendments as 'Amendment N'.\n- **Other:** x\n")
    updated = _decisions.set_decision_records(text, "external", "docs/DOC-007.md")
    assert "- **Decision records:** external — docs/DOC-007.md — previously: ADRs in DOC-007; amendments" in updated
    assert "- **Other:** x" in updated
    assert _decisions.decision_records(updated)["mode"] == "external"
    assert _decisions.decision_records(updated)["path"] == "docs/DOC-007.md"
