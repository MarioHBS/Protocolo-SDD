"""4.7.0: the weight of a stage (`light` / `full`) in the stage index and in the skills that read it."""

from __future__ import annotations

import json

from sdd_cli.cli import _doctor_payload
from sdd_cli.content import CONTENT_DIR

_SDD = CONTENT_DIR / "sdd"


def _text(relative: str) -> str:
    return " ".join((_SDD / relative).read_text(encoding="utf-8").split())


def test_roadmap_asks_for_the_weight_and_requires_a_reason_for_light():
    text = _text("skills/sdd-roadmap/SKILL.md")
    assert "Decide each stage's weight as you enqueue it" in text
    assert "`full` is the default and needs nothing written" in text
    assert "`light: <one-sentence reason>`" in text
    assert "The reason is mandatory" in text
    assert "never `light`" in text


def test_specify_shortens_a_light_spec_without_dropping_the_acceptance_criteria():
    text = _text("skills/sdd-specify/SKILL.md")
    assert "Read the stage's **weight** in §5" in text
    assert "empty or missing means `full`" in text
    assert "never drops the acceptance criteria or the ground-truth verification" in text


def test_promotion_from_the_queue_carries_the_weight():
    assert "carrying over its slug, `Depends on` and `Weight`" in _text("skills/sdd-close/SKILL.md")


def test_the_index_template_documents_the_optional_weight_column():
    text = _text("constitution.md")
    assert "Optional `Weight` column" in text
    assert "`light: <one-sentence reason>`" in text
    assert "A promoted stage carries its Weight with it" in text


# --------------------------------------------------------------------------- W-02: the doctor

INDEX = """\
## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Depends on | Weight |
|-------|------|--------|------------|--------|
| 001 | typo-fix | done | — | light: only fixes a typo |
| 002 | new-table | done | — | full |

### Provisional queue (not yet numbered)

| Slug | Status | Depends on | Notes |
|------|--------|------------|-------|

## 6. Structural change history
"""


def _edd_project(tmp_path, index: str = INDEX):
    sdd = tmp_path / ".sdd"
    (sdd / "stages").mkdir(parents=True)
    manifest = {"kit_version": "v4.7.0", "language": "en", "providers": ["generic"],
                "features": {"estimation": False, "documentation": False, "edd": True},
                "managed_files": {}, "created_at": "2026-01-01"}
    (sdd / ".sdd-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (sdd / "constitution.md").write_text(index, encoding="utf-8")
    return tmp_path


def _closed_stage(root, name, evals="- [x] E-001\n- [x] E-002\n", report="# Report\n\nE-001 ok\nE-002 ok\n",
                  checklist=None):
    stage = root / ".sdd" / "stages" / name
    stage.mkdir()
    (stage / "spec.md").write_text("# Spec\n\n## 5. Acceptance criteria\n\nSee evals.md.\n", encoding="utf-8")
    (stage / "todo.md").write_text("- [x] check evals.md\n", encoding="utf-8")
    (stage / "evals.md").write_text(evals, encoding="utf-8")
    (stage / "report.md").write_text(report, encoding="utf-8")
    if checklist is not None:
        (stage / "checklist.md").write_text(checklist, encoding="utf-8")


def _codes(root, stage):
    return sorted(f["code"] for f in _doctor_payload(root)["findings"]
                  if f.get("stage") == stage and f["code"].startswith("edd_"))


def test_a_light_stage_keeps_its_evidence_in_the_report_alone(tmp_path):
    root = _edd_project(tmp_path)
    _closed_stage(root, "001-typo-fix")
    _closed_stage(root, "002-new-table")  # same files, but full
    assert _codes(root, "001-typo-fix") == []
    assert _codes(root, "002-new-table") == ["edd_missing_checklist"]


def test_a_light_stage_still_fails_when_a_criterion_has_no_evidence(tmp_path):
    root = _edd_project(tmp_path)
    _closed_stage(root, "001-typo-fix", report="# Report\n\nE-001 ok\n")
    findings = [f for f in _doctor_payload(root)["findings"] if f.get("stage") == "001-typo-fix"]
    codes = sorted(f["code"] for f in findings)
    assert codes == ["edd_eval_uncovered", "edd_missing_checklist"]
    assert {f["eval"] for f in findings if f["code"] == "edd_eval_uncovered"} == {"E-002"}


def test_a_light_stage_with_no_evidence_at_all_fails(tmp_path):
    root = _edd_project(tmp_path)
    _closed_stage(root, "001-typo-fix", report="# Report\n\nDone.\n")
    assert _codes(root, "001-typo-fix") == ["edd_eval_uncovered", "edd_eval_uncovered", "edd_missing_checklist"]


def test_a_light_stage_still_needs_its_evals_file(tmp_path):
    root = _edd_project(tmp_path)
    stage = root / ".sdd" / "stages" / "001-typo-fix"
    stage.mkdir()
    (stage / "spec.md").write_text("# Spec\n", encoding="utf-8")
    assert _codes(root, "001-typo-fix") == ["edd_missing_evals"]


def test_a_light_stage_with_a_checklist_and_full_evidence_is_clean(tmp_path):
    root = _edd_project(tmp_path)
    _closed_stage(root, "001-typo-fix", checklist="# Checklist\n\nE-001 E-002\n")
    assert _codes(root, "001-typo-fix") == []


def test_an_index_without_the_weight_column_keeps_the_old_rule_for_every_stage(tmp_path):
    old = INDEX.replace(" | Weight |", " |").replace("|------|--------|------------|--------|\n", "|------|--------|------------|\n") \
        .replace(" | light: only fixes a typo |", " |").replace(" | full |", " |")
    assert "Weight" not in old
    root = _edd_project(tmp_path, old)
    _closed_stage(root, "001-typo-fix")
    _closed_stage(root, "002-new-table")
    assert _codes(root, "001-typo-fix") == ["edd_missing_checklist"]
    assert _codes(root, "002-new-table") == ["edd_missing_checklist"]


def test_a_closed_stage_whose_evals_file_has_no_criterion_is_flagged_for_any_weight(tmp_path):
    root = _edd_project(tmp_path)
    for name in ("001-typo-fix", "002-new-table"):
        _closed_stage(root, name, evals="# Evals\n\nnothing here\n", report="# Report\n", checklist="# C\n")
        assert _codes(root, name) == ["edd_no_criteria"]


def test_a_light_stage_with_no_criterion_does_not_pass_through_the_report_shortcut(tmp_path):
    root = _edd_project(tmp_path)
    _closed_stage(root, "001-typo-fix", evals="# Evals\n", report="# Report\n")
    assert _codes(root, "001-typo-fix") == ["edd_missing_checklist", "edd_no_criteria"]


def test_close_and_specify_describe_the_light_evidence_rule():
    close = _text("skills/sdd-close/SKILL.md")
    assert "For a **`light`** stage" in close and "`report.md` alone" in close
    assert "Every criterion still needs evidence" in close
    specify = _text("skills/sdd-specify/SKILL.md")
    assert "write `evals.md` with one or two criteria and skip `checklist.md`" in specify
    assert "There is always at least one criterion" in specify


def test_criteria_numbered_in_a_projects_own_style_are_not_flagged_as_missing(tmp_path):
    # LSDI numbers its criteria E1..E7, not E-001: they are criteria, so nothing is missing.
    root = _edd_project(tmp_path)
    _closed_stage(root, "002-new-table", evals="| E1 | identity |\n| E2 | replay |\n", checklist="# C\n")
    assert _codes(root, "002-new-table") == []
