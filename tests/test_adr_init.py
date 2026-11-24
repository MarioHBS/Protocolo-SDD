"""4.10.0, M-04: `sddkit adr init` rebuilds records for a project that decided things before the folder.

Fixtures follow the episodes the plan was written from: a project with five `D-NNN` rows and ADRs
kept outside `.sdd/` (a folder with one file per ADR, or one document with many). The rules under
test: nothing is invented, nothing the owner wrote is overwritten, the constitution is copied first
and keeps its line endings, and a second run changes nothing.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _adr, _adr_init, _decisions, _docs_plan
from sdd_cli.cli import _doctor_payload, cmd_adr

ROWS = [
    ("D-001", "database", "Postgres", "transactions", "2026-01-10"),
    ("D-002", "queue", "none", "later", "2026-01-11"),
    ("D-003", "auth", "OAuth", "no passwords", "2026-01-12"),
    ("D-004", "hosting", "Fly.io", "cheap", "2026-01-13"),
    ("D-005", "ui kit", "none", "proposed (agreed 2026-01-14)", "proposed"),
]


def _constitution(rows=ROWS, with_column: bool = False, section_7: str | None = None) -> str:
    header = "| ID | Decision | Choice | Rationale | Locked on |" + (" Record |" if with_column else "")
    sep = "|----|----------|--------|-----------|-----------|" + ("--------|" if with_column else "")
    body = "\n".join(
        f"| {i} | {d} | {c} | {r} | {on} |" + ("  |" if with_column else "") for i, d, c, r, on in rows)
    seven = section_7 if section_7 is not None else (
        "- **Decision records (ADRs):** ADRs in DOC-007; amendments as 'Amendment N'")
    return (f"## Settings\n\n- **Language:** en\n\n## 3. Locked structural decisions\n\n{header}\n{sep}\n{body}\n\n"
            f"## 5. Stage index (CANONICAL)\n\n| Stage | Slug | Status |\n|---|---|---|\n| 001 | first | done |\n\n"
            f"## 7. Project decision conventions\n\n{seven}\n- **Other:** x\n")


def _project(tmp_path: Path, text: str | None = None, newline: str | None = None) -> Path:
    (tmp_path / ".sdd").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".sdd" / "constitution.md").write_text(
        text if text is not None else _constitution(), encoding="utf-8", newline=newline)
    return tmp_path


def _answers(tmp_path: Path, **data) -> Path:
    out = tmp_path / "adr-init.json"
    out.write_text(json.dumps({"schema_version": _adr_init.SCHEMA, **data}), encoding="utf-8")
    return out


def _init(root: Path, answers: Path | None = None, **flags):
    values = dict(path=str(root), adr_command="init", answers=str(answers) if answers else None,
                  resume=False, dry_run=False, json=True)
    values.update(flags)
    cmd_adr(types.SimpleNamespace(**values))


def _text(root: Path) -> str:
    return (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")


def _files(root: Path) -> list[str]:
    return sorted(p.name for p in (root / ".sdd" / "decisions").glob("ADR-*.md")) \
        if (root / ".sdd" / "decisions").is_dir() else []


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*"))
            if p.is_file() and ".pre-fix-backup" not in p.parts}


def _external_folder(root: Path) -> None:
    folder = root / "docs" / "decisoes"
    folder.mkdir(parents=True)
    (folder / "ADR-001-use-postgres.md").write_text(
        "# ADR-001 — Use Postgres\n\nWe need transactions (D-001).\n", encoding="utf-8")
    (folder / "ADR-002-queue.md").write_text("# ADR-002: Queue\n\nNo queue yet.\n", encoding="utf-8")


# ------------------------------------------------------------ rows strategy

def test_five_rows_and_two_confirmed_make_two_reconstructed_records(tmp_path, capsys):
    root = _project(tmp_path)
    answers = _answers(tmp_path, strategy="rows", records=[
        {"decision": "D-001", "status": "implementada", "stage": "001-first", "implemented_in": "001-first",
         "context": "Needed transactions.", "alternatives": ["SQLite: one writer only"]},
        {"decision": "D-003"}])
    _init(root, answers)
    assert _files(root) == ["ADR-001-database-postgres.md", "ADR-002-auth-oauth.md"]
    first, second = _adr.list_adrs(root)
    assert first.meta["reconstructed"] is True and second.meta["reconstructed"] is True
    assert first.meta["source"] == "constitution.md section 3 (D-001)"
    assert first.meta["status"] == "implementada" and first.meta["implemented_in"] == "001-first"
    assert first.meta["date"] == "2026-01-10" and first.meta["decision"] == "D-001"
    assert "Needed transactions." in first.body and "SQLite: one writer only" in first.body
    assert "Postgres" in first.body and "Rationale: transactions" in first.body
    # what the sources do not say is marked, never invented
    assert _adr_init.UNKNOWN in second.body
    assert second.meta["stage"] == "" and second.meta["implemented_in"] == ""
    assert second.meta["status"] == "aceita"  # the row is locked
    capsys.readouterr()
    text = _text(root)
    assert _decisions.has_record_column(text) is True
    cells = {r["id"]: r["record"] for r in _decisions.rows(text)}
    assert cells == {"D-001": "[ADR-001](decisions/ADR-001-database-postgres.md)", "D-002": "",
                     "D-003": "[ADR-002](decisions/ADR-002-auth-oauth.md)", "D-004": "", "D-005": ""}
    field = _decisions.decision_records(text)
    assert field["mode"] == "internal"
    assert "previously: ADRs in DOC-007" in text
    assert "| [ADR-001](ADR-001-database-postgres.md) |" in (root / ".sdd" / "decisions" / "README.md").read_text(
        encoding="utf-8")
    (backup,) = list((root / ".sdd" / ".pre-fix-backup").glob("*/constitution.md"))
    assert backup.read_text(encoding="utf-8") == _constitution()


def test_the_second_run_changes_nothing(tmp_path, capsys):
    root = _project(tmp_path)
    answers = _answers(tmp_path, records=[{"decision": "D-001"}, {"decision": "D-003"}])
    _init(root, answers)
    capsys.readouterr()
    before = _snapshot(root)
    backups = sorted((root / ".sdd" / ".pre-fix-backup").iterdir())
    _init(root, answers)
    assert _snapshot(root) == before
    assert sorted((root / ".sdd" / ".pre-fix-backup").iterdir()) == backups
    out = json.loads(capsys.readouterr().out)
    assert out["created"] == [] and out["constitution_changed"] is False


def test_dry_run_prints_the_plan_and_writes_nothing(tmp_path, capsys):
    root = _project(tmp_path)
    before = _snapshot(root)
    _init(root, _answers(tmp_path, records=[{"decision": "D-002", "context": "later"}]), dry_run=True)
    assert _snapshot(root) == {**before, "adr-init.json": (tmp_path / "adr-init.json").read_bytes()}
    plan = json.loads(capsys.readouterr().out)
    assert plan["dry_run"] is True and plan["add_record_column"] is True
    assert plan["links"] == {"D-002": "[ADR-001](decisions/ADR-001-queue-none.md)"}
    assert [c["id"] for c in plan["create"]] == ["ADR-001"] and "content" not in plan["create"][0]
    assert not (root / ".sdd" / ".reservations.json").exists()


def test_an_empty_record_list_only_adds_the_column_and_says_internal(tmp_path):
    root = _project(tmp_path)
    _init(root, _answers(tmp_path, records=[]))
    assert _files(root) == [] and not (root / ".sdd" / "decisions").exists()
    assert _decisions.has_record_column(_text(root)) is True
    assert all(r["record"] == "" for r in _decisions.rows(_text(root)))
    assert _decisions.decision_records(_text(root))["mode"] == "internal"


def test_a_record_is_never_written_over_one_the_owner_has(tmp_path):
    root = _project(tmp_path)
    (root / ".sdd" / "decisions").mkdir()
    mine = root / ".sdd" / "decisions" / "ADR-001-mine.md"
    mine.write_text("---\nid: ADR-001\nstatus: aceita\n---\n# ADR-001 — Mine\n", encoding="utf-8")
    original = mine.read_bytes()
    _init(root, _answers(tmp_path, records=[{"decision": "D-001"}]))
    assert mine.read_bytes() == original
    assert _files(root) == ["ADR-001-mine.md", "ADR-002-database-postgres.md"]


def test_the_constitution_keeps_its_crlf_endings(tmp_path):
    root = _project(tmp_path, _constitution().replace("\n", "\r\n"), newline="")
    _init(root, _answers(tmp_path, records=[{"decision": "D-001"}]))
    raw = (root / ".sdd" / "constitution.md").read_bytes()
    assert b"decisions/ADR-001" in raw and raw.count(b"\r\n") == raw.count(b"\n")


def test_a_table_that_already_has_the_column_gets_no_second_one(tmp_path):
    root = _project(tmp_path, _constitution(with_column=True))
    _init(root, _answers(tmp_path, records=[{"decision": "D-002"}]))
    header = next(line for line in _text(root).splitlines() if line.startswith("| ID"))
    assert header.count("Record") == 1


def test_the_doctor_is_quiet_after_a_clean_run(tmp_path):
    root = _project(tmp_path)
    _init(root, _answers(tmp_path, records=[{"decision": "D-001"}, {"decision": "D-003"}]))
    codes = [f["code"] for f in _doctor_payload(root)["findings"]]
    assert not [c for c in codes if c.startswith(("adr_", "decision_row", "decisions_dir"))]


# ------------------------------------------------------- external: link/import

def test_link_keeps_the_adrs_where_they_are_and_links_the_rows_that_cite_them(tmp_path):
    rows = [("D-001", "database", "Postgres (ADR-001)", "tx", "2026-01-10"),
            ("D-002", "queue", "none, see ADR-002", "later", "2026-01-11"),
            ("D-003", "auth", "OAuth", "no passwords", "2026-01-12")]
    root = _project(tmp_path, _constitution(rows))
    _external_folder(root)
    before = {p.name: p.read_bytes() for p in (root / "docs" / "decisoes").iterdir()}
    _init(root, _answers(tmp_path, strategy="link", path="docs/decisoes/"))
    assert not (root / ".sdd" / "decisions").exists()
    cells = {r["id"]: r["record"] for r in _decisions.rows(_text(root))}
    assert cells["D-001"] == "[ADR-001](../docs/decisoes/ADR-001-use-postgres.md)"
    assert cells["D-002"] == "[ADR-002](../docs/decisoes/ADR-002-queue.md)"
    assert cells["D-003"] == ""
    field = _decisions.decision_records(_text(root))
    assert (field["mode"], field["path"]) == ("external", "docs/decisoes/")
    assert {p.name: p.read_bytes() for p in (root / "docs" / "decisoes").iterdir()} == before
    assert [f["code"] for f in _doctor_payload(root)["findings"] if f["code"].startswith(("adr_", "decision"))] == []


def test_link_to_a_single_document_only_updates_section_7(tmp_path, capsys):
    root = _project(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "DOC-007.md").write_text("# ADRs\n\n## ADR-001\n\n## ADR-002\n", encoding="utf-8")
    _init(root, _answers(tmp_path, strategy="link", path="docs/DOC-007.md"))
    field = _decisions.decision_records(_text(root))
    assert (field["mode"], field["path"]) == ("external", "docs/DOC-007.md")
    assert all(r["record"] == "" for r in _decisions.rows(_text(root)))
    assert "single document is linked from section 7 only" in capsys.readouterr().out


def test_import_copies_a_folder_into_records_keeping_the_numbers(tmp_path):
    root = _project(tmp_path)
    _external_folder(root)
    _init(root, _answers(tmp_path, strategy="import", path="docs/decisoes/", map={"ADR-002": "D-002"}))
    assert _files(root) == ["ADR-001-use-postgres.md", "ADR-002-queue.md"]
    one, two = _adr.list_adrs(root)
    assert one.meta["source"] == "docs/decisoes/ADR-001-use-postgres.md" and one.meta["reconstructed"] is True
    assert one.meta["decision"] == "D-001"  # the file names it
    assert two.meta["decision"] == "D-002"  # the answers' map names it
    assert one.meta["status"] == "aceita" and one.meta["date"] == ""
    assert "We need transactions (D-001)." in one.body  # the owner's text is kept as it was
    cells = {r["id"]: r["record"] for r in _decisions.rows(_text(root))}
    assert cells["D-001"] == "[ADR-001](decisions/ADR-001-use-postgres.md)" and cells["D-003"] == ""
    assert _decisions.decision_records(_text(root))["mode"] == "internal"
    # the originals stay where they were
    assert (root / "docs" / "decisoes" / "ADR-001-use-postgres.md").is_file()


def test_import_twice_is_idempotent_and_never_overwrites(tmp_path, capsys):
    root = _project(tmp_path)
    _external_folder(root)
    answers = _answers(tmp_path, strategy="import", path="docs/decisoes/")
    _init(root, answers)
    capsys.readouterr()
    before = _snapshot(root)
    _init(root, answers)
    assert _snapshot(root) == before


def test_import_keeps_a_colliding_number_the_owner_already_has(tmp_path):
    root = _project(tmp_path)
    _external_folder(root)
    (root / ".sdd" / "decisions").mkdir()
    mine = root / ".sdd" / "decisions" / "ADR-001-mine.md"
    mine.write_text("---\nid: ADR-001\n---\n# Mine\n", encoding="utf-8")
    _init(root, _answers(tmp_path, strategy="import", path="docs/decisoes/"))
    assert mine.read_text(encoding="utf-8") == "---\nid: ADR-001\n---\n# Mine\n"
    assert _files(root) == ["ADR-001-mine.md", "ADR-002-queue.md"]


# ------------------------------------------------------------------ validation

@pytest.mark.parametrize("data, message", [
    ({"schema_version": "other/v9"}, "schema_version"),
    ({"strategy": "copy"}, "strategy must be one of"),
    ({"strategy": "link"}, "needs `path`"),
    ({"strategy": "link", "path": "../outside"}, "unsafe path"),
    ({"strategy": "link", "path": "docs/nowhere/"}, "path does not exist"),
    ({"records": [{"decision": "D-099"}]}, "is not a row of section 3"),
    ({"records": [{"decision": "D-001", "status": "draft"}]}, "outside the cycle"),
    ({"records": [{"decision": "D-001"}, {"decision": "D-001"}]}, "appears twice"),
    ({"records": [{"decision": "D-001", "alternatives": "SQLite"}]}, "alternatives must be a list of strings"),
    ({"records": "all"}, "records must be a list"),
    ({"map": {"ADR-001": 4}}, "map must be an object"),
])
def test_bad_answers_are_refused_before_anything_is_written(tmp_path, capsys, data, message):
    root = _project(tmp_path)
    (root / "docs").mkdir()
    out = tmp_path / "adr-init.json"
    out.write_text(json.dumps({"schema_version": _adr_init.SCHEMA, **data} if "schema_version" not in data
                              else data), encoding="utf-8")
    before = _snapshot(root)
    with pytest.raises(SystemExit):
        _init(root, out)
    assert message in capsys.readouterr().err
    assert _snapshot(root) == {**before}


def test_import_needs_a_folder_not_a_document(tmp_path, capsys):
    root = _project(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "DOC-007.md").write_text("# x\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        _init(root, _answers(tmp_path, strategy="import", path="docs/DOC-007.md"))
    assert "only be linked" in capsys.readouterr().err


def test_no_terminal_and_no_answers_says_how_to_continue(tmp_path, capsys, monkeypatch):
    root = _project(tmp_path)
    monkeypatch.setattr("sys.stdin", types.SimpleNamespace(isatty=lambda: False))
    with pytest.raises(SystemExit):
        _init(root)
    assert "--answers FILE.json" in capsys.readouterr().err


def test_a_project_without_a_section_3_table_has_nothing_to_rebuild(tmp_path, capsys):
    root = _project(tmp_path, "## Settings\n\n- **Language:** en\n")
    with pytest.raises(SystemExit):
        _init(root, _answers(tmp_path, records=[]))
    assert "no section 3 table" in capsys.readouterr().err


# ------------------------------------------------------------------ interview

def _console(answers: list[str], asked: list[str] | None = None) -> _docs_plan.Console:
    pending = iter(answers)

    def read(prompt: str) -> str:
        if asked is not None:
            asked.append(prompt)
        try:
            return next(pending)
        except StopIteration:
            raise EOFError from None

    return _docs_plan.Console(read=read, write=lambda text: None)


def test_the_interview_asks_per_row_and_returns_the_same_contract(tmp_path):
    root = _project(tmp_path, _constitution(ROWS[:3]))
    analysis = _adr_init.analyze(root)
    answers = _adr_init.run_interview(root, analysis, _console([
        "y", "implementada", "Needed transactions", "SQLite: one writer; Files: no queries", "001-first", "001-first",
        "n",
        "y", "", "", "", ""]))
    assert answers["strategy"] == "rows"
    first, third = answers["records"]
    assert first == {"decision": "D-001", "status": "implementada", "context": "Needed transactions",
                     "alternatives": ["SQLite: one writer", "Files: no queries"], "stage": "001-first",
                     "implemented_in": "001-first"}
    assert third["decision"] == "D-003" and third["status"] == "aceita" and third["alternatives"] == []
    checked = _adr_init.validate(answers, analysis, root)
    assert [r["decision"] for r in checked["records"]] == ["D-001", "D-003"]


def test_an_interrupted_interview_resumes_where_it_stopped(tmp_path):
    root = _project(tmp_path, _constitution(ROWS[:2]))
    analysis = _adr_init.analyze(root)
    saved: dict = {}
    with pytest.raises(_docs_plan.InterviewAborted):
        _adr_init.run_interview(root, analysis, _console(["y"]), on_step=lambda s: saved.update(json.loads(json.dumps(s))))
    assert saved["done"] == ["sources", "strategy"]  # the records step never finished
    asked: list[str] = []
    answers = _adr_init.run_interview(root, analysis, _console(["n", "n"], asked), state=saved)
    assert len(asked) == 2 and answers["records"] == []  # sources and strategy were not asked again


def test_the_interview_offers_link_or_import_when_adrs_already_exist(tmp_path):
    rows = [("D-001", "database", "Postgres (ADR-001)", "tx", "2026-01-10"),
            ("D-002", "queue", "none", "later", "2026-01-11")]
    root = _project(tmp_path, _constitution(rows))
    _external_folder(root)
    analysis = _adr_init.analyze(root)
    assert analysis["external"]["kind"] == "folder" and len(analysis["external"]["files"]) == 2
    asked: list[str] = []
    answers = _adr_init.run_interview(root, analysis, _console(["link", "docs/decisoes/", "n"], asked))
    assert answers["strategy"] == "link" and answers["path"] == "docs/decisoes/"
    assert any("What to do with them" in p for p in asked)
    # D-001 cites ADR-001, which exists outside: it is covered by the link, so only D-002 is asked about
    assert sum("deserve a record" in p for p in asked) == 1


def test_the_citations_of_a_row_in_stage_files_are_shown_not_copied(tmp_path):
    root = _project(tmp_path, _constitution(ROWS[:2]))
    stage = root / ".sdd" / "stages" / "001-first"
    stage.mkdir(parents=True)
    (stage / "report.md").write_text("Implements D-001 and D-001 again.\n", encoding="utf-8")
    candidates = {c["id"]: c for c in _adr_init.analyze(root)["candidates"]}
    assert candidates["D-001"]["cited_in"] == ["001-first"] and candidates["D-002"]["cited_in"] == []
    _init(root, _answers(tmp_path, records=[{"decision": "D-001"}]))
    (record,) = _adr.list_adrs(root)
    assert record.meta["implemented_in"] == "" and record.meta["stage"] == ""  # a hint, never written for you
