---
name: sdd-track
description: Cross-cutting SDD utility that opens, governs and merges parallel TRACKS -- two or more stages worked at the same time by separate agent sessions, without git worktrees. Use WHENEVER the user wants to parallelize work ("let's split this into two tracks", "can two of us work on this at once", "open a track for X"), when working inside an already-open track, when a track's stage is finished and needs incorporating back into the canonical queue, or when a downstream stage's constitution row lists "Depends on" tracks that must be checked before it starts. Not a phase -- may be invoked in any state where SPECIFYING/IMPLEMENTING/CLOSING would normally apply.
---

# Utility — parallel tracks (fork / work / join)

Goal: let two or more agent sessions work different stages of the same
project **at the same time**, on the same filesystem, without git worktrees
and without corrupting the single canonical index (§5 of the constitution).

Write all artifacts in the language set in
`constitution.md → Settings → Language`.

## Why this is safe without git worktrees

The project's single canonical index (§5) and its derived `roadmap.md` stay
the ONE source of truth — tracks never get a second permanent index. Each
track gets its own **pre-close scratch area** (`tracks/<slug>/`) that only
the track's own agent session ever writes. The only moment a track's agent
touches shared files (§5, `roadmap.md`) is a narrow, append-only step at
incorporation — never a rewrite of existing rows, never a full regeneration
outside `sdd-reconcile`. Two sessions working two different tracks therefore
almost never contend for the same file; the one place they still could
(structural decisions in §2/§3) is called out explicitly below rather than
pretended away.

## What tracks isolate — and what they do NOT

Tracks isolate the **SDD index** (`tracks/<slug>/` scratch, §5 append-only).
They do **not** isolate the shared things two sessions build on top of:

- the **working tree / source code** — both tracks edit the same files;
- the **build, compiler, and runtime** — one shared buildable state;
- **manual/on-device testing, a running dev server, a physical or emulated
  device, a shared database or external sandbox** — one at a time, really.

So two stages can be perfectly independent *in the index* and still collide
*in reality*. The sharpest form of this — the one that motivated writing it
down — is a **stability-sensitive stage**: a stage whose acceptance needs a
**stable, buildable, runnable shared artifact**. Examples: manual QA on a
mobile build, on-device or end-to-end testing, a release/store build,
performance benchmarking, anything a human validates by *running the app*.

A stability-sensitive stage **cannot** run as a parallel sibling of a track
that is mid-flight mutating shared code, because that track will routinely
leave the build red while it works — exactly when the stability-sensitive
stage needs it green. "Independent slices of work" (the `sdd-roadmap`
parallelization test) means independent in **data/order AND in the shared
build/runtime/device**, not just in the index. If a candidate stage fails
the second half of that test, **do not open it as a parallel track** —
sequence it instead (see "Fork/join" below): after the mutating tracks join
back (a join stage whose `Depends on` lists them), or strictly after the one
specific track stage it validates.

## On-disk layout

```text
.sdd/
+-- tracks/
    +-- <slug>/
        +-- state.md          — free-form, agent-owned, never parsed by the CLI
        +-- stages/
            +-- 001-<slug>/    — same shape as a normal stage folder
            +-- 002-<slug>/       (spec.md, todo.md, report.md, checklist.md)
+-- stages/                    — the canonical queue (unchanged shape)
    +-- NNN[-LETTER]-<slug>/    — the letter suffix here is STILL the existing
                                   "inserted without renumbering" convention;
                                   it has nothing to do with tracks
```

**A track's ID is a slug you choose when opening it** (`login`, `billing`),
not a number or letter. Its stage folders live under
`tracks/<slug>/stages/` with their own local numbering starting at `001` —
this is deliberately a separate numbering space from the canonical
`stages/NNN-<slug>/` queue, so opening tracks never collides with the
existing out-of-order-insertion letter suffix (`010-A`), which keeps its
original, unrelated meaning.

## Steps

0. **Feature gate.** Only usable if `Settings → Parallel tracks` is `on` in
   the constitution. If it is `off`, tell the user how to turn it on (edit
   `## Settings` in `constitution.md`, same as any other toggle) and stop —
   do not open a track.

1. **Opening a track.** Only from a point where the canonical queue is
   between stages (e.g. just closed one, or at the ROADMAP boundary).
   Confirm with the user: which stage is the branch point, what slug each
   track gets, and what each one covers. If this track already sat in §5's
   **Provisional queue** as a `track candidate` row, remove that row now —
   the track's progress is tracked in `### Active tracks` from here on, not
   as a queue entry.
   **Stability check before you fork:** for each candidate track, ask
   whether any of its stages is *stability-sensitive* (needs a stable
   shared build/runtime/device — see "What tracks isolate" above) and
   whether any *sibling* track will be mutating shared code at the same
   time. If both are true for the same time window, that stability-sensitive
   stage **must not** be opened as a parallel sibling — pull it out and
   sequence it instead (a join stage that `Depends on` the mutating tracks,
   or a stage placed strictly after the specific track stage it validates).
   Only genuinely build/runtime-independent work goes into parallel
   siblings. For each track you do open:
   - create `tracks/<slug>/` and seed `tracks/<slug>/state.md` from
     `templates/track-state.template.md`;
   - create `tracks/<slug>/stages/` (empty, ready for the track's own
     numbering);
   - append a row for the track to `## Current state → ### Active tracks`
     in the constitution (this sub-table is additive — create it if it does
     not exist yet).
   Tell the user explicitly: *"Open a separate agent session pointed at
   this same project root for the other track now. Each session must only
   edit its own `tracks/<slug>/state.md` and `tracks/<slug>/stages/*`
   files."*

2. **Working inside a track.** Behaves exactly like the normal
   SPECIFYING → IMPLEMENTING → CLOSING flow — delegate the actual mechanics
   to `sdd-specify` / `sdd-implement` / `sdd-close` — except stage folders
   are created under `tracks/<slug>/stages/NNN-<slug-etapa>/` (local
   numbering, never directly under the canonical `stages/`). Hard rules:
   - **MUST NOT** write to any `tracks/<other-slug>/` path.
   - **MUST NOT** write to `constitution.md` or `roadmap.md` except via the
     narrow incorporation step (next item) — no trimming `Current state`,
     no touching another track's `### Active tracks` row, no regenerating
     `roadmap.md` (that is `sdd-reconcile`'s job, run once all tracks of
     interest have reached a stable point — step 4).
   - Track-local progress (what's active *within this track*, what's next)
     lives in `tracks/<slug>/state.md`, not in the shared `Current state`.

3. **Closing a stage inside a track / incorporating it.** Run `sdd-close`
   normally for the stage's `report.md`/`todo.md` mechanics. Then:
   1. Move/rename the finished folder from
      `tracks/<slug>/stages/NNN-<slug-etapa>/` to
      `stages/<next-free-number>-<slug-etapa>/` in the canonical queue — an
      isolated rename, never a renumbering of the existing queue.
   2. Append (never rewrite) the corresponding row to §5.
   3. **Do not** regenerate `roadmap.md` here — that stays deferred to
      `sdd-reconcile` (step 4), specifically to avoid two tracks racing on
      that file if they incorporate around the same time.
   4. If §5 has a **join stage** whose `Depends on` column lists this
      track's slug, check whether every track listed there now has all its
      stages incorporated. If so, note in `tracks/<slug>/state.md` (and
      tell the user) that the join stage is unblocked — do not start it
      yourself; that is `sdd-specify`'s job, and only once its own
      `Depends on` check (see that skill) confirms it.
   5. Update `tracks/<slug>/state.md` freely — it is exclusively owned by
      this track's session.

4. **Merging tracks back / closing the fork.** Once every stage of interest
   across a family of sibling tracks is incorporated, invoke
   `sdd-reconcile` (extended for tracks — see its own SKILL.md) to: verify
   §5 against disk for every incorporated track stage; regenerate
   `roadmap.md` from the now-complete §5 (the single deferred regeneration
   point); if a join stage was waiting on these tracks, confirm it is now
   unblocked; decide with the user the single next `Active stage`. Do
   **not** delete the finished `tracks/<slug>/` directories — leave them as
   historical evidence (same "never silently discard user content" ethos
   the CLI's own backup logic follows).

## Fork/join — declaring a stage that depends on tracks finishing

The queue is not always "sequential → one fork → merge → sequential" a
single time. It can fork and join repeatedly: sequential stages, then N
tracks, then a **join stage** that must wait for all of them, then possibly
another fork later. This is declared in §5's **Depends on** column:

- Empty (default) = today's plain sequential behavior, unchanged.
- Filled with one or more track slugs = this stage is a join stage; it must
  not move to SPECIFYING/IMPLEMENTING until every listed track has all its
  stages incorporated into the canonical queue.

`Depends on` sequences a stage after tracks for **either** reason, with the
same mechanism:

- **needs the result** — the stage consumes what those tracks produce
  (data/order dependency); or
- **needs the stability** — the stage is stability-sensitive (manual/on-device
  QA, a release build, e2e, benchmarking) and cannot tolerate those tracks
  breaking the shared build while it runs. This is how a stage that would
  otherwise have been dropped into a parallel sibling gets safely sequenced
  after the code-mutating tracks instead. When the reason is stability, note
  it beside the stage (e.g. in its slug or a spec line) so a later reader
  knows the dependency is about build stability, not consumed output.

`sdd-roadmap` declares a join stage's `Depends on` cell when the fork/join
shape is planned (even before the tracks are actually opened via
`sdd-track`). `sdd-specify` and `sdd-implement` both carry a short
MUST-NOT-start rule checking that column before beginning a stage. `sdd
doctor` flags (WARNING, never blocking) a join stage that was started while
a listed track dependency is still pending — catch-early, not a gate.

This composes: nothing prevents a new fork being declared after a join
stage — it is just another set of tracks opened via `sdd-track` and another
`Depends on` cell filled in later, with no different mechanism per nesting
level.

## Rules

- One track, one agent session, one `state.md` — never two sessions editing
  the same `tracks/<slug>/state.md`.
- **Tracks isolate the index, not the build.** A stability-sensitive stage
  (needs a stable shared build/runtime/device) is never a parallel sibling of
  a track that mutates shared code in the same window — sequence it after via
  `Depends on`. Parallel siblings must be independent in the shared
  build/runtime/device, not only in the index.
- `constitution.md §5` remains the ONLY canonical index; a track's
  `state.md` is disposable scratch, never a second source of truth.
- The next-free-number a track stage gets at incorporation (step 3.1) comes
  from the **same pool** §5's Provisional queue draws from when it promotes a
  solo stage — whichever closes first gets the next `NNN`, regardless of
  planning order.
- `roadmap.md` regeneration only happens via `sdd-reconcile`, never inside a
  track's own incorporation step.
- **Mid-flight structural decisions are the one real collision risk this
  design does not fully close.** If a structural decision surfaces inside a
  track (per `sdd-decide`'s "structural decision mid-flight"), it touches
  §2/§3 of the constitution — those sections are **not** append-only the
  way §5 is. Warn the user explicitly and ask the other track's session to
  pause (or be aware) before editing §2/§3 while two sessions are live.
