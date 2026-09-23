"""User-owned-file hygiene checks — shared by `doctor` (report mode) and the
`sdd-reconcile` final check.

These are **audit-only** findings: they surface problems so a human/agent can
fix them, never rewrite files behind the user's back — the same "dumb but
reliable" contract as `_mojibake.py`. Checks live here:

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

4. **Track divergences** (parallel-tracks feature, see the `sdd-track` skill) —
   an opened track with no stage ever started under it, a track that has been
   idle for a while with unfinished stages, or a completed stage still sitting
   under `tracks/<slug>/stages/` instead of being incorporated into the
   canonical `stages/` queue. A project with no `.sdd/tracks/` directory (or an
   empty one) produces no track findings at all — this check is purely
   additive and never fires for a project that has never opened a track.

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
class TrackDivergence:
    """A hygiene finding about a `.sdd/tracks/<slug>/` directory."""

    track: str    # slug, e.g. "login"
    kind: str     # "not_started" | "not_incorporated"
    detail: str   # human-readable specifics
    track_state: str = "in_progress"  # "not_started" | "in_progress" | "closed"


@dataclass
class HygieneResult:
    """Aggregated findings over a project's `stages/` and `tracks/`."""

    closed_with_open_todo: list[TodoDivergence]   # check 1
    spec_without_todo: list[str]                  # check 3 — stage folder names
    changelog_exists: bool                        # check 2
    track_divergences: list[TrackDivergence]       # check 4
    notes: list[str]                              # extra, non-fatal observations


_OPEN_BOX_RE = re.compile(r"(?m)^[-*]\s+\[\s\]")
_CLOSED_BOX_RE = re.compile(r"(?m)^[-*]\s+\[[xX!\-]\]")

def _count_boxes(text: str) -> tuple[int, int]:
    """Return (open, closed) markdown checkbox counts."""
    return (len(_OPEN_BOX_RE.findall(text)), len(_CLOSED_BOX_RE.findall(text)))


_HTML_COMMENT_RE = re.compile(r"(?s)<!--.*?-->")


def active_track_slugs(sdd: Path) -> set[str] | None:
    """Slugs listed in the constitution's ``### Active tracks`` table.

    Returns ``None`` when the table is absent or has no rows (unknown), so
    callers fall back to per-track markers. A track that is *not* listed in a
    populated table has been concluded and dropped from the index.
    """
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        return None
    text = _HTML_COMMENT_RE.sub("", constitution.read_text(encoding="utf-8", errors="replace"))
    heading = re.search(r"(?m)^###\s+Active tracks\s*$", text)
    if not heading:
        return None
    rest = text[heading.end():]
    end = re.search(r"(?m)^#{1,3}\s", rest)
    block = rest[:end.start()] if end else rest
    slugs = set(re.findall(r"(?m)^\|\s*`([^`|]+)`\s*\|", block))
    return slugs or None


_ON_HOLD_RE = re.compile(r"(?i)\b(on[ -]hold|paused|em espera|pausad[ao])\b")


def on_hold_track_slugs(sdd: Path) -> set[str]:
    """Tracks the owner parked on purpose: 'on hold' / 'em espera' in their ``Active tracks`` row."""
    constitution = sdd / "constitution.md"
    if not constitution.is_file():
        return set()
    text = _HTML_COMMENT_RE.sub("", constitution.read_text(encoding="utf-8", errors="replace"))
    heading = re.search(r"(?m)^###\s+Active tracks\s*$", text)
    if not heading:
        return set()
    rest = text[heading.end():]
    end = re.search(r"(?m)^#{1,3}\s", rest)
    block = rest[:end.start()] if end else rest
    return {m.group(1) for m in re.finditer(r"(?m)^\|\s*`([^`|]+)`\s*\|(.*)$", block)
            if _ON_HOLD_RE.search(m.group(2))}


def _scan_tracks_v4(sdd: Path) -> list[TrackDivergence]:
    """Classify empty tracks deterministically; closed tracks are clean."""
    tracks_dir = sdd / "tracks"
    if not tracks_dir.is_dir():
        return []
    active = active_track_slugs(sdd)
    on_hold = on_hold_track_slugs(sdd)
    findings: list[TrackDivergence] = []
    for directory in sorted(tracks_dir.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        slug = directory.name
        state = directory / "state.md"
        text = state.read_text(encoding="utf-8", errors="replace") if state.is_file() else ""
        closed = bool(re.search(r"(?im)^[-*]?\s*(?:status|state)\s*:\s*closed\s*$", text)
                      or re.search(r"(?im)^[-*]?\s*incorporated\s*:\s*true\s*$", text)
                      or (active is not None and slug not in active))
        stages = directory / "stages"
        stage_dirs = [p for p in stages.iterdir() if p.is_dir()] if stages.is_dir() else []
        if not stage_dirs:
            if not closed and slug not in on_hold:
                findings.append(TrackDivergence(
                    slug, "not_started",
                    f"no stage folders under tracks/{slug}/stages/; the track has not started",
                    "not_started"))
            continue
        for stage in sorted(stage_dirs):
            if (stage / "report.md").is_file():
                findings.append(TrackDivergence(
                    slug, "not_incorporated",
                    f"tracks/{slug}/stages/{stage.name}/ has report.md but is not incorporated",
                    "in_progress"))
    return findings


def scan_hygiene(sdd: Path) -> HygieneResult:
    """Walk `.sdd/stages/`, `.sdd/tracks/` and `.sdd/CHANGELOG.md`. Pure read
    — writes nothing."""
    closed_open: list[TodoDivergence] = []
    spec_no_todo: list[str] = []
    notes: list[str] = []

    changelog = sdd / "CHANGELOG.md"
    changelog_exists = changelog.is_file()

    track_divergences = _scan_tracks_v4(sdd)

    stages = sdd / "stages"
    if not stages.is_dir():
        return HygieneResult(closed_open, spec_no_todo, changelog_exists,
                             track_divergences, notes)

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
        track_divergences=track_divergences,
        notes=notes,
    )
