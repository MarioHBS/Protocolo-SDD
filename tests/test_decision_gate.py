"""4.6.0: the structural-decision checklist is one list, in every skill that carries it."""

from __future__ import annotations

from pathlib import Path

from sdd_cli.content import CONTENT_DIR

_SKILLS = CONTENT_DIR / "sdd" / "skills"
_COPIES = {
    "sdd-decide": _SKILLS / "sdd-decide" / "SKILL.md",
    "sdd-discover": _SKILLS / "sdd-discover" / "SKILL.md",
    "standalone": Path(__file__).parents[1] / "sdd-discover.standalone" / "SKILL.md",
}


def _structural_categories(path: Path) -> list[str]:
    """Bullets of the first list under a `What counts as structural` heading, whitespace-collapsed."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.lstrip("# ").startswith("What counts as structural"))
    items: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif line.startswith(" ") and items:
            items[-1] += " " + line.strip()
        elif line.strip() and items:
            break
    return [" ".join(item.split()) for item in items]


def test_every_copy_of_the_checklist_has_the_same_categories():
    lists = {name: _structural_categories(path) for name, path in _COPIES.items()}
    assert len(lists["sdd-decide"]) >= 10
    for name, categories in lists.items():
        assert categories == lists["sdd-decide"], f"{name} diverges from sdd-decide"


def test_design_system_is_a_structural_category_when_there_is_an_interface():
    for name, path in _COPIES.items():
        categories = _structural_categories(path)
        design = [c for c in categories if c.startswith("Design system")]
        assert len(design) == 1, name
        assert "light/dark theme" in design[0] and "accessibility baseline" in design[0]
        assert "when the project has an interface" in design[0]
