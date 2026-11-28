"""K-08: a `|` inside a table cell is part of the cell.

The 4.10.0 review found that a cell written as `A \\| B` was cut in two by the reader, so rewriting
the row moved every following cell, and `init --discovery` wrote a value with a bare `|` straight
into the decision table.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _decisions, _index_checks
from sdd_cli.cli import cmd_init

TABLE = """## 3. Locked decisions

| ID | Decision | Choice | Rationale | Locked on | Record |
|----|----------|--------|-----------|-----------|--------|
| D-001 | Output | `a \\| b` | pipes in a shell | 2026-09-22 |  |
"""


@pytest.mark.parametrize("line,cells", [
    ("| a | b |", ["a", "b"]),
    ("| a \\| b | c |", ["a \\| b", "c"]),
    ("| a | ends with \\| |", ["a", "ends with \\|"]),
    ("| a | ends with \\|", ["a", "ends with \\|"]),
    ("| a |  | c |", ["a", "", "c"]),
    ("|", [""]),
])
def test_cells_are_cut_only_at_a_bare_pipe(line, cells):
    assert _index_checks._cells(line) == cells


@pytest.mark.parametrize("value,cell", [
    ("a | b", "a \\| b"),
    ("a \\| b", "a \\| b"),
    ("one\ntwo\r\nthree", "one two three"),
    ("C:\\Users\\x", "C:\\Users\\x"),
])
def test_a_value_is_escaped_once_and_stays_on_one_line(value, cell):
    assert _index_checks.cell_text(value) == cell


def test_writing_the_record_cell_keeps_the_other_cells_byte_for_byte():
    text, outcome = _decisions.set_record(TABLE, "D-001", "[ADR-001](decisions/ADR-001-x.md)")
    assert outcome == "set"
    assert ("| D-001 | Output | `a \\| b` | pipes in a shell | 2026-09-22 | "
            "[ADR-001](decisions/ADR-001-x.md) |") in text
    (row,) = _decisions.rows(text)
    assert row["fields"]["rationale"] == "pipes in a shell"


def _discovery(tmp_path: Path) -> Path:
    data = {
        "schema_version": "sdd-discovery/v1",
        "project": {"name": "Atlas", "language": "en"},
        "vision": {"what_it_is": "A useful atlas", "who_it_is_for": "Researchers",
                   "definition_of_done": "Search works"},
        "features": {},
        "decisions": [{"decision": "Output", "choice": "text | json", "rationale": "kept in C:\\Users\\data",
                       "locked_on": "2026-09-22", "adr": True}],
        "open_questions": [{"question": "csv | tsv?", "blocks_gate": "no", "status": "open"}],
        "backlog": [],
        "stages": [{"slug": "search", "title": "Search records", "origin": "escopo-original", "tasks": ["Query"]},
                   {"slug": "export", "title": "Export csv | tsv", "tasks": ["Write"]}],
    }
    out = tmp_path / "discovery.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    return out


def test_discovery_values_with_pipes_and_backslashes_keep_the_tables_whole(tmp_path):
    source = _discovery(tmp_path)
    cmd_init(types.SimpleNamespace(
        path=str(tmp_path), provider=["generic"], language=None, estimation=False, docs=False, tracks=False,
        edd=False, dashboard_ui="static", force=False, yes=True, discovery=str(source)))
    text = (tmp_path / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    (row,) = _decisions.rows(text)
    assert len(row["cells"]) == 6
    assert row["fields"]["choice"] == "text \\| json"
    assert row["fields"]["rationale"] == "kept in C:\\Users\\data"
    assert row["record"].startswith("[ADR-001](")
    assert "| Q-001 | csv \\| tsv? | no | open |" in text
    assert "Export csv \\| tsv; Origin: escopo-original" in text


def test_an_audit_finding_with_a_pipe_in_a_cell_is_still_read(tmp_path):
    audit = tmp_path / "audit.md"
    audit.write_text(
        "## Round 1 — 2026-11-28\n\n- **Verdict:** READY TO LOCK\n\n"
        "| Id | Severity | Lens | Where | State | Pointer |\n"
        "|----|----------|------|-------|-------|---------|\n"
        "| F-01 | BLOCKER | 3 | `a \\| b` in spec.md | fixed | spec.md §4 |\n"
        "| F-02 | MAJOR | 3 \\| 4 | spec.md | dismissed | owner |\n", encoding="utf-8")
    assert _index_checks._audit_record(audit)["states"] == {
        "F-01": ("BLOCKER", "fixed"), "F-02": ("MAJOR", "dismissed")}
