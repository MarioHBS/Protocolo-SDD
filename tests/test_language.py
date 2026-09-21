"""The v1 language heuristic only *proposes* a language; it must not be brittle."""

from __future__ import annotations

import pytest

from sdd_cli.cli import _detect_language


def _detect(tmp_path, text: str):
    sdd = tmp_path / ".sdd"
    sdd.mkdir(exist_ok=True)
    (sdd / "constitution.md").write_text(text, encoding="utf-8")
    return _detect_language(tmp_path)


@pytest.mark.parametrize(("text", "expected"), [
    ("# Constituição\n\n## Estado atual\n\nDecisões travadas do projeto.", "pt-BR"),
    ("# Constitución\n\n## Estado actual\n\nDecisiones del Proyecto, ¿verdad?", "es"),
    ("# Constitution\n\n## Current state\n\nProject vision and open questions.", "en"),
    ("# 项目宪法\n\n当前状态", "zh"),
])
def test_language_is_detected_regardless_of_case(tmp_path, text, expected):
    assert _detect(tmp_path, text) == (expected, "detected")
    assert _detect(tmp_path, text.upper()) == (expected, "detected")


def test_a_spanish_heading_is_not_mistaken_for_portuguese(tmp_path):
    # "## Estado" heading is shared by both languages; the words around it decide.
    assert _detect(tmp_path, "## Estado\n\nEl Proyecto y sus decisiones.")[0] == "es"


def test_ambiguous_or_empty_text_falls_back_to_the_default(tmp_path):
    assert _detect(tmp_path, "# Notes\n\nnothing telling here") == ("pt-BR", "default")
    assert _detect(tmp_path, "etapas") == ("pt-BR", "default")  # shared PT/ES word alone decides nothing
