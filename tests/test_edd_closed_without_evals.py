"""K-07: a stage closed before the project turned EDD on is a note, not two warnings.

Real case: a project adopted EDD "from stage 005 on" and decided not to reopen 001-004, all done.
With `features.edd` on, the doctor reported `edd_missing_evals` and `edd_missing_checklist` for each
of the four, and no weight or fix could silence them.
"""
from __future__ import annotations

from test_stage_weight import _closed_stage, _codes, _edd_project

from sdd_cli._findings import describe
from sdd_cli.cli import _doctor_payload

INDEX = """\
## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Depends on |
|-------|------|--------|------------|
| 001 | old-closed | done | — |
| 002 | still-open | in progress | 001 |
| 003 | closed-pt | concluída | 002 |
| 004 | with-evals | done | 003 |

### Provisional queue (not yet numbered)

| Slug | Status | Depends on | Notes |
|------|--------|------------|-------|

## 6. Structural change history
"""


def _pre_edd_stage(root, name, report=True):
    stage = root / ".sdd" / "stages" / name
    stage.mkdir()
    (stage / "spec.md").write_text("# Spec\n\n## 5. Acceptance criteria\n\n- it works\n", encoding="utf-8")
    (stage / "todo.md").write_text("- [x] done\n", encoding="utf-8")
    if report:
        (stage / "report.md").write_text("# Report\n\nall good\n", encoding="utf-8")


def test_a_done_stage_with_a_report_and_no_evals_is_one_note(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _pre_edd_stage(root, "001-old-closed")
    assert _codes(root, "001-old-closed") == ["edd_closed_without_evals"]
    finding = next(f for f in _doctor_payload(root)["findings"] if f["code"] == "edd_closed_without_evals")
    assert finding["severity"] == "note"


def test_the_portuguese_done_status_counts(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _pre_edd_stage(root, "003-closed-pt")
    assert _codes(root, "003-closed-pt") == ["edd_closed_without_evals"]


def test_an_open_stage_keeps_both_warnings(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _pre_edd_stage(root, "002-still-open")
    assert _codes(root, "002-still-open") == ["edd_missing_checklist", "edd_missing_evals"]


def test_a_done_row_without_a_report_keeps_the_warning(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _pre_edd_stage(root, "001-old-closed", report=False)
    assert _codes(root, "001-old-closed") == ["edd_missing_evals"]


def test_a_stage_missing_from_the_index_keeps_both_warnings(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _pre_edd_stage(root, "009-not-listed")
    assert _codes(root, "009-not-listed") == ["edd_missing_checklist", "edd_missing_evals"]


def test_a_done_stage_with_evals_keeps_its_format_warnings(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _closed_stage(root, "004-with-evals")
    spec = root / ".sdd" / "stages" / "004-with-evals" / "spec.md"
    spec.write_text("# Spec\n\n## 5. Acceptance criteria\n\n- repeats the criteria\n", encoding="utf-8")
    assert _codes(root, "004-with-evals") == ["edd_missing_checklist", "edd_spec_not_pointer"]


def test_the_note_does_not_change_the_exit_status_and_says_what_to_do(tmp_path):
    root = _edd_project(tmp_path, INDEX)
    _pre_edd_stage(root, "001-old-closed")
    payload = _doctor_payload(root)
    assert payload["status"] == 0
    message, hint = describe(next(f for f in payload["findings"] if f["code"] == "edd_closed_without_evals"))
    assert "001-old-closed" in message and "evals.md" in hint
