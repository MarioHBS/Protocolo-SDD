"""4.10.0, M-03: the discovery contract may ask for a record, and the import writes it as a proposal.

`sdd-discovery/v1` gains three optional fields per decision (`adr`, `context`, `alternatives`); a
v1 file without them keeps importing exactly as before.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from sdd_cli import _adr, _decisions
from sdd_cli.cli import _doctor_payload, cmd_discover, cmd_init

DECISIONS = [
    {"decision": "Storage", "choice": "SQLite", "rationale": "portable", "locked_on": "2026-09-22",
     "adr": True, "context": "One user, one machine, no server to run.",
     "alternatives": ["PostgreSQL: needs a server", "Flat files: no queries"]},
    {"decision": "Language", "choice": "Python", "rationale": "team knows it", "locked_on": "2026-09-22"},
]


def _discovery(tmp_path: Path, decisions: list | None = None) -> Path:
    data = {
        "schema_version": "sdd-discovery/v1",
        "project": {"name": "Atlas", "language": "en"},
        "vision": {"what_it_is": "A useful atlas", "who_it_is_for": "Researchers", "definition_of_done": "Search works"},
        "features": {},
        "decisions": DECISIONS if decisions is None else decisions,
        "open_questions": [],
        "backlog": [],
        "stages": [{"slug": "search", "title": "Search records", "origin": "escopo-original", "tasks": ["Add query"]}],
    }
    out = tmp_path / "discovery.json"
    out.write_text(json.dumps(data), encoding="utf-8")
    return out


def _init(tmp_path: Path, source: Path) -> Path:
    cmd_init(types.SimpleNamespace(
        path=str(tmp_path), provider=["generic"], language=None, estimation=False, docs=False, tracks=False,
        edd=False, dashboard_ui="static", force=False, yes=True, discovery=str(source)))
    return tmp_path


def test_a_decision_with_adr_true_gets_a_proposed_record_and_the_others_only_a_row(tmp_path):
    root = _init(tmp_path, _discovery(tmp_path))
    records = _adr.list_adrs(root)
    assert [r.path.name for r in records] == ["ADR-001-storage-sqlite.md"]
    (record,) = records
    assert record.meta["status"] == "proposta" and record.meta["decision"] == "D-001"
    assert record.meta["source"] == "discovery.json" and record.meta["reconstructed"] is False
    assert record.meta["date"] == "2026-09-22"
    assert "One user, one machine" in record.body and "PostgreSQL: needs a server" in record.body
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    rows = {r["id"]: r for r in _decisions.rows(text)}
    assert set(rows) == {"D-001", "D-002"}
    assert rows["D-001"]["record"] == "[ADR-001](decisions/ADR-001-storage-sqlite.md)"
    assert rows["D-002"]["record"] == ""
    assert all("proposed (agreed 2026-09-22)" in r["cells"][4] for r in rows.values())


def test_the_record_and_its_row_are_proposals_together_and_the_project_starts_deciding(tmp_path):
    root = _init(tmp_path, _discovery(tmp_path))
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    assert "**State:** DECIDING" in text
    assert (root / ".sdd" / "decisions" / "README.md").is_file()
    assert "| proposta |" in (root / ".sdd" / "decisions" / "README.md").read_text(encoding="utf-8")


def test_the_doctor_is_quiet_about_a_freshly_imported_project(tmp_path):
    root = _init(tmp_path, _discovery(tmp_path))
    codes = [f["code"] for f in _doctor_payload(root)["findings"]]
    assert not [c for c in codes if c.startswith(("adr_", "decision_row", "decisions_dir"))]


def test_a_v1_file_without_the_new_fields_imports_as_before(tmp_path):
    plain = [{"decision": "Storage", "choice": "SQLite", "rationale": "portable", "locked_on": "2026-09-22"}]
    root = _init(tmp_path, _discovery(tmp_path, plain))
    assert not (root / ".sdd" / "decisions").exists()
    assert not (root / ".sdd" / ".reservations.json").exists()
    row = next(line for line in (root / ".sdd" / "constitution.md").read_text(encoding="utf-8").splitlines()
               if line.startswith("| D-001 |"))
    assert row.rstrip().endswith("| proposed (agreed 2026-09-22) |  |")


def test_a_project_with_no_decisions_keeps_a_six_cell_placeholder_row(tmp_path):
    root = _init(tmp_path, _discovery(tmp_path, []))
    text = (root / ".sdd" / "constitution.md").read_text(encoding="utf-8")
    (row,) = _decisions.rows(text)
    assert row["cells"][1] == "[none recorded]" and len(row["cells"]) == 6 and row["placeholder"]


def test_adr_false_means_no_record(tmp_path):
    root = _init(tmp_path, _discovery(tmp_path, [{**DECISIONS[0], "adr": False}]))
    assert not (root / ".sdd" / "decisions").exists()


@pytest.mark.parametrize("patch, message", [
    ({"adr": "yes"}, "decisions[1].adr must be true or false"),
    ({"context": 3}, "decisions[1].context must be a string"),
    ({"alternatives": "SQLite"}, "decisions[1].alternatives must be a list of strings"),
    ({"alternatives": ["ok", 2]}, "decisions[1].alternatives must be a list of strings"),
])
def test_bad_optional_fields_are_refused_by_the_check(tmp_path, capsys, patch, message):
    source = _discovery(tmp_path, [{**DECISIONS[0], **patch}])
    with pytest.raises(SystemExit):
        cmd_discover(types.SimpleNamespace(path=str(tmp_path), check=str(source), against=None))
    assert message in capsys.readouterr().err


def test_a_decision_that_is_not_an_object_is_refused(tmp_path, capsys):
    source = _discovery(tmp_path, ["just text"])
    with pytest.raises(SystemExit):
        cmd_discover(types.SimpleNamespace(path=str(tmp_path), check=str(source), against=None))
    assert "decisions[1] must be an object" in capsys.readouterr().err


def test_the_summary_says_how_many_records_will_be_written(tmp_path, capsys):
    source = _discovery(tmp_path)
    cmd_discover(types.SimpleNamespace(path=str(tmp_path), check=str(source), against=None))
    assert "decisions: 2 (1 with a record in .sdd/decisions/, status proposta)" in capsys.readouterr().out


def test_the_summary_of_a_plain_v1_file_is_unchanged(tmp_path, capsys):
    source = _discovery(tmp_path, [{"decision": "A", "choice": "B", "rationale": "C", "locked_on": "2026-01-01"}])
    cmd_discover(types.SimpleNamespace(path=str(tmp_path), check=str(source), against=None))
    out = capsys.readouterr().out
    assert "  decisions: 1\n" in out and "with a record" not in out
