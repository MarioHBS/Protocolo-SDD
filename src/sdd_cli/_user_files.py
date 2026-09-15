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
import time
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
_CLOSED_BOX_RE = re.compile(r"(?m)^[-*]\s+\[[xX]\]")

def _count_boxes(text: str) -> tuple[int, int]:
    """Return (open, closed) markdown checkbox counts."""
    return (len(_OPEN_BOX_RE.findall(text)), len(_CLOSED_BOX_RE.findall(text)))


def _scan_tracks(sdd: Path) -> list[TrackDivergence]:
    tracks_dir = sdd / "tracks"
    if not tracks_dir.is_dir():
        return []

    findings: list[TrackDivergence] = []
    now = time.time()

    for d in sorted(tracks_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        slug = d.name
        stages_dir = d / "stages"
        stage_dirs = [s for s in stages_dir.iterdir() if s.is_dir()] \
            if stages_dir.is_dir() else []

        if not stage_dirs:
            findings.append(TrackDivergence(
                track=slug, kind="empty",
                detail=f"no stage folders under tracks/{slug}/stages/ — "
                       "either the track was just opened and nothing has "
                       "started yet, or all its stages were already "
                       "incorporated into stages/. If the track's work is "
                       "done, close the fork via sdd-reconcile and drop its "
                       "row from Current state -> Active tracks.",
            ))
            continue

        for s in sorted(stage_dirs):
            if (s / "report.md").is_file():
                findings.append(TrackDivergence(
                    track=slug, kind="not_incorporated",
                    detail=f"tracks/{slug}/stages/{s.name}/ has a report.md "
                           "but was not incorporated into the canonical "
                           "stages/ queue (see sdd-track, 'closing a stage "
                           "inside a track')",
                ))

        state_md = d / "state.md"
        unfinished = any(not (s / "report.md").is_file() for s in stage_dirs)
        if unfinished and state_md.is_file():
            age_days = (now - state_md.stat().st_mtime) / 86400
            if age_days >= _STALE_TRACK_DAYS:
                findings.append(TrackDivergence(
                    track=slug, kind="stale",
                    detail=f"tracks/{slug}/state.md not updated in "
                           f"{int(age_days)}+ days while stages remain "
                           "unfinished — possibly abandoned",
                ))

    return findings


def _scan_tracks_v4(sdd: Path) -> list[TrackDivergence]:
    """Classify empty tracks deterministically; closed tracks are clean."""
    tracks_dir = sdd / "tracks"
    if not tracks_dir.is_dir():
        return []
    findings: list[TrackDivergence] = []
    for directory in sorted(tracks_dir.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        slug = directory.name
        state = directory / "state.md"
        text = state.read_text(encoding="utf-8", errors="replace") if state.is_file() else ""
        closed = bool(re.search(r"(?im)^[-*]?\s*(?:status|state)\s*:\s*closed\s*$", text)
                      or re.search(r"(?im)^[-*]?\s*incorporated\s*:\s*true\s*$", text))
        stages = directory / "stages"
        stage_dirs = [p for p in stages.iterdir() if p.is_dir()] if stages.is_dir() else []
        if not stage_dirs:
            if not closed:
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
