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


def test_backlog_orphan_hint_names_the_format_the_detector_reads(tmp_path):
    # R3-04: a list with the slug in backticks, or a `backlog.md#slug` anchor,
    # both looked right to a person but were not parsed -- only a table row
    # with a literal `slug` column is. The hint must say so, not just "fix it".
    from sdd_cli import _findings

    _, hint = _findings.describe({"severity": "warn", "code": "backlog_orphan", "section": "x"})
    assert "slug" in hint and "table" in hint


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


def test_portuguese_stage_and_queue_headings_bound_the_canonical_table(tmp_path):
    from sdd_cli import _tracks

    constitution = CONSTITUTION.replace("Stage index", "Índice de etapas") \
        .replace("Provisional queue", "Fila provisória")
    sdd = _project(tmp_path, "## deploy-frontend\n", constitution)
    assert "audit" in _index_checks.stage_slugs(sdd)
    assert _index_checks.stage_slugs(sdd)["deploy-frontend"] == "provisional queue"
    assert any(f["code"] == "queue_row_without_section"
               for f in _index_checks.backlog_findings(sdd))
    span = _tracks._stage_index_span(constitution)
    assert span is not None
    assert constitution[span[0]:span[1]].startswith("| 003 | auth")


WEIGHTED = """\
## 5. Stage index (CANONICAL)

| Stage | Slug | Status | Depends on | Weight |
|-------|------|--------|------------|--------|
| 001 | typo-fix | done | — | light: only fixes a typo |
| 002 | new-table | pending | — | full |
| 003 | no-column-value | pending | — |  |

### Provisional queue (not yet numbered)

| Slug | Status | Depends on | Weight | Notes |
|------|--------|------------|--------|-------|
| copy-tweak | pending | — | light — copy change only | — |
| big-feature | pending | — | | — |

## 6. Structural change history
"""


def _weighted_project(tmp_path, constitution: str = WEIGHTED):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    (sdd / "constitution.md").write_text(constitution, encoding="utf-8")
    return sdd


def test_light_and_full_stages_are_read_side_by_side_from_both_tables(tmp_path):
    weights = _index_checks.stage_weights(_weighted_project(tmp_path))
    assert weights == {"001-typo-fix": "light", "002-new-table": "full", "003-no-column-value": "full",
                       "copy-tweak": "light", "big-feature": "full"}


def test_an_index_without_the_weight_column_reads_everything_as_full(tmp_path):
    # P-old: a constitution written before 4.7.0 has no Weight column at all.
    weights = _index_checks.stage_weights(_weighted_project(tmp_path, CONSTITUTION))
    assert weights and set(weights.values()) == {"full"}


def test_no_constitution_means_no_weights_and_no_findings(tmp_path):
    sdd = tmp_path / ".sdd"
    sdd.mkdir()
    assert _index_checks.stage_weights(sdd) == {}
    assert _index_checks.weight_findings(sdd) == []


def test_portuguese_spellings_are_accepted_and_anything_unknown_is_full(tmp_path):
    constitution = WEIGHTED.replace("| Weight |", "| Peso |").replace(
        "light: only fixes a typo", "leve: so corrige um typo").replace("| full |", "| completo |").replace(
        "light — copy change only", "ligth: typo in the weight itself")
    weights = _index_checks.stage_weights(_weighted_project(tmp_path, constitution))
    assert weights["001-typo-fix"] == "light"
    assert weights["002-new-table"] == "full"
    assert weights["copy-tweak"] == "full"  # a misspelled weight never relaxes anything


def test_parse_weight_separates_the_word_from_the_reason():
    assert _index_checks.parse_weight("light: only fixes a typo") == ("light", "only fixes a typo")
    assert _index_checks.parse_weight("`light` — copy change") == ("light", "copy change")
    assert _index_checks.parse_weight("Leve - so um typo") == ("light", "so um typo")
    assert _index_checks.parse_weight("full") == ("full", "")
    assert _index_checks.parse_weight("") == ("full", "")
    assert _index_checks.parse_weight("light") == ("light", "")
    assert _index_checks.parse_weight("full: light work, heavy risk") == ("full", "")


def test_a_light_stage_must_give_its_reason(tmp_path):
    constitution = WEIGHTED.replace("light: only fixes a typo", "light").replace("light — copy change only", "light")
    findings = _index_checks.weight_findings(_weighted_project(tmp_path, constitution))
    assert [(f["code"], f["stage"]) for f in findings] == [
        ("weight_light_without_reason", "001-typo-fix"), ("weight_light_without_reason", "copy-tweak")]


def test_a_light_stage_with_its_reason_raises_nothing(tmp_path):
    assert _index_checks.weight_findings(_weighted_project(tmp_path)) == []


def test_the_doctor_reports_a_light_stage_without_a_reason(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    _weighted_project(root, WEIGHTED.replace("light: only fixes a typo", "light"))
    codes = [f["code"] for f in _doctor_payload(root)["findings"]]
    assert codes.count("weight_light_without_reason") == 1
