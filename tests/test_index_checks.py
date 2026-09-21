"""Backlog and milestone cross-checks (read-only, audit findings)."""

from __future__ import annotations

from sdd_cli import _index_checks
from sdd_cli.cli import _doctor_payload

CONSTITUTION = """\
## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Milestone |
|-------|------|--------|-----------|
| 001 | audit | done | Marco A |
| 002 | secrets | done | Marco A |
| 003 | auth | pending | Marco B |

### Provisional queue (not yet numbered)

| Slug | Status | Depends on | Notes |
|------|--------|------------|-------|
| deploy-frontend | pending | 001 | Pick a host. Details in backlog.md. |
| lint-cleanup | pending | 001 | Small debts. |
| missing-detail | pending | 001 | See backlog.md for the tasks. |

## 6. Structural change history
"""


def _project(tmp_path, backlog: str, constitution: str = CONSTITUTION):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(constitution, encoding="utf-8")
    (sdd / "backlog.md").write_text(backlog, encoding="utf-8")
    return sdd


def test_backlog_section_without_a_queue_row_is_an_orphan(tmp_path):
    sdd = _project(tmp_path, "# Backlog\n\n## Provisória — deploy-frontend\n\n- [ ] x\n\n"
                             "## Provisória — gone-stage\n\n- [ ] y\n\n## Items\n")
    codes = {(f["code"], f.get("section") or f.get("slug")) for f in _index_checks.backlog_findings(sdd)}
    assert ("backlog_orphan", "Provisória — gone-stage") in codes
    assert not any(c == "backlog_orphan" and "deploy-frontend" in (s or "") for c, s in codes)
    assert not any("Items" in (s or "") for _, s in codes)  # a generic heading is not a section


def test_queue_row_citing_the_backlog_needs_its_section(tmp_path):
    sdd = _project(tmp_path, "## deploy-frontend\n\ntext\n")
    findings = _index_checks.backlog_findings(sdd)
    assert [(f["code"], f["slug"]) for f in findings] == [("queue_row_without_section", "missing-detail")]


def test_no_backlog_means_no_findings(tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(CONSTITUTION, encoding="utf-8")
    assert _index_checks.backlog_findings(sdd) == []


def test_finished_milestone_needs_an_evaluation_file(tmp_path):
    sdd = _project(tmp_path, "")
    (sdd / "milestones" / "marco-a-base").mkdir(parents=True)
    findings = _index_checks.milestone_findings(sdd)
    assert [f["code"] for f in findings] == ["edd_milestone_without_evaluation"]
    (sdd / "milestones" / "marco-a-base" / "avaliacao.md").write_text("ok", encoding="utf-8")
    assert _index_checks.milestone_findings(sdd) == []


def test_milestone_split_across_the_queue_is_flagged(tmp_path):
    constitution = CONSTITUTION.replace("| 003 | auth | pending | Marco B |",
                                        "| 003 | auth | pending | Marco B |\n| 004 | more | pending | Marco A |")
    sdd = _project(tmp_path, "", constitution)
    codes = [(f["code"], f.get("milestone")) for f in _index_checks.milestone_findings(sdd)]
    assert ("milestone_not_contiguous", "Marco A") in codes


def test_doctor_includes_the_index_findings(tmp_path):
    _project(tmp_path, "## Provisória — gone-stage\n")
    codes = {f["code"] for f in _doctor_payload(tmp_path)["findings"]}
    assert "backlog_orphan" in codes
