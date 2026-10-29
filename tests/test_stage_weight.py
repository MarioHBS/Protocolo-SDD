"""4.7.0: the weight of a stage (`light` / `full`) in the stage index and in the skills that read it."""

from __future__ import annotations

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
