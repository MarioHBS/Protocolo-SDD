"""K-12: every table the kit installs has the same number of cells in each row.

P2 (IP-016): `templates/audit.template.md` held bare `|` inside a comment in a cell, and a project
that lints Markdown failed (MD056) on a file it must not edit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sdd_cli import _index_checks

CONTENT = Path(__file__).resolve().parent.parent / "src" / "sdd_cli" / "content"


def _broken_rows(text: str) -> list[tuple[int, int, int]]:
    """``(line, cells, expected)`` for each table row that does not match its header. A bare `|`
    counts even inside backticks or a comment, as markdownlint counts it."""
    broken, width, fenced = [], None, False
    lines = text.split("\n")
    for number, line in enumerate(lines, 1):
        stripped = line.strip().removeprefix(">").strip()
        if stripped.startswith(("```", "~~~")):
            fenced = not fenced
        if fenced or not stripped.startswith("|"):
            width = None
            continue
        cells = len(_index_checks._BARE_PIPE_RE.findall(stripped)) - 1
        if width is None:
            following = lines[number].strip().removeprefix(">").strip() if number < len(lines) else ""
            width = cells if _index_checks._SEPARATOR_RE.match(following) else None
        elif cells != width:
            broken.append((number, cells, width))
    return broken


def test_the_check_sees_the_case_it_was_written_for():
    assert _broken_rows("| a | b |\n|---|---|\n| x | y <!-- one | two --> |\n") == [(3, 3, 2)]


@pytest.mark.parametrize("path", sorted(CONTENT.rglob("*.md")), ids=lambda p: p.relative_to(CONTENT).as_posix())
def test_bundled_markdown_tables_are_whole(path):
    assert _broken_rows(path.read_text(encoding="utf-8")) == []
