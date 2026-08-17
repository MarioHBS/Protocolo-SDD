"""User-owned-file hygiene checks — shared by `doctor` (report mode) and the
`sdd-reconcile` final check.

These are **audit-only** findings: they surface problems so a human/agent can
fix them, never rewrite files behind the user's back — the same "dumb but
reliable" contract as `_mojibake.py`. Three checks live here:

1. **Closed stage with open `todo.md`** — a stage folder that already has a
   `report.md` (so it is "done" on disk) but whose `todo.md` still has unchecked
   `- [ ]` items. This is the "027 pattern": the stage closed, but the executor
   marked its own ad-hoc list and never reconciled the real `todo.md`. WARNING,
   not error.

2. **CHANGELOG present** — whether `.sdd/CHANGELOG.md` exists (the constitution
   §6 is now an index pointing at it; a project missing it has nowhere for the
   long-form history to grow). Informational on legacy projects, expected on new
   ones.

3. **Stage with spec but no todo** — a spec was written but the `todo.md` was
   never created (executor has no guide). WARNING.

All checks read disk only; none trust the constitution's self-reported state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TodoDivergence:
    """A closed stage whose `todo.md` still has unchecked items."""

    stage: str               # folder name, e.g. "027-billing-rules"
    open_checkboxes: int     # count of `- [ ]` remaining
    total_checkboxes: int    # total `- [ ]` + `- [x]` in the file


@dataclass
class HygieneResult:
    """Aggregated findings over a project's `stages/`."""

    closed_with_open_todo: list[TodoDivergence]   # check 1
    spec_without_todo: list[str]                  # check 3 — stage folder names
    changelog_exists: bool                        # check 2
    notes: list[str]                              # extra, non-fatal observations


_OPEN_BOX_RE = re.compile(r"(?m)^[-*]\s+\[\s\]")
_CLOSED_BOX_RE = re.compile(r"(?m)^[-*]\s+\[[xX]\]")


def _count_boxes(text: str) -> tuple[int, int]:
    """Return (open, closed) markdown checkbox counts."""
    return (len(_OPEN_BOX_RE.findall(text)), len(_CLOSED_BOX_RE.findall(text)))


def scan_hygiene(sdd: Path) -> HygieneResult:
    """Walk `.sdd/stages/` and `.sdd/CHANGELOG.md`. Pure read — writes nothing."""
    closed_open: list[TodoDivergence] = []
    spec_no_todo: list[str] = []
    notes: list[str] = []

    changelog = sdd / "CHANGELOG.md"
    changelog_exists = changelog.is_file()

    stages = sdd / "stages"
    if not stages.is_dir():
        return HygieneResult(closed_open, spec_no_todo, changelog_exists, notes)

    for d in sorted(stages.iterdir()):
        if not d.is_dir():
            continue
        name = d.name
        spec = d / "spec.md"
        todo = d / "todo.md"
        report = d / "report.md"
        closed = report.is_file()

        if spec.is_file() and not todo.is_file():
            spec_no_todo.append(name)

        if closed and todo.is_file():
            text = todo.read_text(encoding="utf-8", errors="replace")
            opened, closed_n = _count_boxes(text)
            if opened:
                closed_open.append(TodoDivergence(
                    stage=name,
                    open_checkboxes=opened,
                    total_checkboxes=opened + closed_n,
                ))
    return HygieneResult(
        closed_with_open_todo=closed_open,
        spec_without_todo=spec_no_todo,
        changelog_exists=changelog_exists,
        notes=notes,
    )
