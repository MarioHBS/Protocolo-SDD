---
name: sdd-track
description: Cross-cutting SDD utility that opens, governs and merges parallel TRACKS -- two or more stages worked at the same time by separate agent sessions on the same working tree, without git worktrees, with declared and CLI-verified footprints so that stages in different tracks cannot affect each other. Use WHENEVER the user wants to parallelize work ("let's split this into two tracks", "can two of us work on this at once", "open a track for X"), when working inside an already-open track, when a track's stage is finished and needs incorporating back into the canonical queue, or when a downstream stage's constitution row lists "Depends on" tracks that must be checked before it starts. Not a phase -- may be invoked in any state where SPECIFYING/IMPLEMENTING/CLOSING would normally apply.
---

# Utility — parallel tracks (fork / claim / work / join)

Goal: let two or more agent sessions work different stages of the same
project **at the same time**, on the same filesystem, without git worktrees
and without corrupting the single canonical index (§5 of the constitution) —
and without one track silently breaking another.

Write all artifacts in the language set in
`constitution.md → Settings → Language`.

## The rule that makes tracks safe

**Two stages may live in different tracks only if they cannot affect each other
in any way** — not through the files they edit, not through the numbers they
take from a shared sequence (canonical stage numbers, database migrations), and
not through the runtime resources they need exclusively (dev server, database,
device). Tracks share one working tree, so nothing physical keeps the sessions
apart; the separation has to be **declared and checked**:

| Tool | What it guarantees |
|---|---|
| `sdd track claim` | records a track's footprint in `tracks/<slug>/claims.json` |
| `sdd track check` | fails when two active tracks' footprints overlap |
| `sdd track verify <slug>` | fails when real Git changes fall outside every claim (or inside two) |
| `sdd seq next <name>` | hands out the next number of a shared sequence, once |
| `sdd track incorporate` | moves a closed stage into the canonical queue under a lock |
| `sdd doctor` | reports `track_overlap`, `sequence_duplicate`, `session_branch_mismatch` |

If a candidate stage collides with a sibling, **do not open it in parallel**:
sequence it after the colliding stage (fill its §5 `Depends on`) or put both in
the same track, one after the other. A collision seen only after the fact —
two sessions editing the same 1,700-line file, a stage implemented twice, two
migrations with the same number — is the failure this skill exists to prevent.

## Why the index is safe without git worktrees

The project's single canonical index (§5) and its derived `roadmap.md` stay
the ONE source of truth — tracks never get a second permanent index. Each
track gets its own **pre-close scratch area** (`tracks/<slug>/`) that only
the track's own agent session ever writes. The only moment a track's agent
touches shared files (§5, `roadmap.md`) is a narrow, append-only step at
incorporation — never a rewrite of existing rows, never a full regeneration
outside `sdd-reconcile`. The one place two sessions could still contend
(structural decisions in §2/§3) is called out below rather than pretended away.

## What tracks isolate — and what they do NOT

Tracks isolate the **SDD index** (`tracks/<slug>/` scratch, §5 append-only).
They do **not** isolate the shared things two sessions build on top of:

- the **working tree / source code** — both tracks edit the same files (this is
  what `claims` make checkable);
- the **build, compiler, and runtime** — one shared buildable state;
- **manual/on-device testing, a running dev server, a physical or emulated
  device, a shared database or external sandbox** — one at a time, really.

So two stages can be perfectly independent *in the index* and still collide
*in reality*. The sharpest form is a **stability-sensitive stage**: a stage whose
acceptance needs a **stable, buildable, runnable shared artifact** (manual QA on
a build, on-device or end-to-end testing, a release build, benchmarking). It
**cannot** run as a parallel sibling of a track that is mid-flight mutating shared
code, because that track routinely leaves the build red. Declare it with
`--stability-sensitive`; `sdd track check` then refuses it next to any track that
claims paths. Sequence it instead: after the mutating tracks join back (a join
stage whose `Depends on` lists them), or strictly after the one stage it validates.

## On-disk layout

```text
.sdd/
+-- tracks/
    +-- <slug>/
        +-- state.md          — free-form, agent-owned, never parsed by the CLI
        +-- claims.json       — the track's declared footprint, written by `sdd track claim`
        +-- .session.json     — (optional) resumable work context, `sdd session`
        +-- stages/
            +-- 001-<slug>/    — same shape as a normal stage folder
            +-- 002-<slug>/       (spec.md, todo.md, report.md, checklist.md)
+-- stages/                    — the canonical queue (unchanged shape)
    +-- NNN[-LETTER]-<slug>/    — the letter suffix here is STILL the existing
                                   "inserted without renumbering" convention;
                                   it has nothing to do with tracks
+-- .reservations.json         — shared numbers already handed out (`sdd seq`, `incorporate`)
```

**A track's ID is a slug you choose when opening it** (`login`, `billing`),
not a number or letter. Its stage folders live under
`tracks/<slug>/stages/` with their own local numbering starting at `001` —
deliberately a separate numbering space from the canonical `stages/NNN-<slug>/`
queue.

## Branches

By default, tracks share the working tree **and the current branch**. A track
that needs its own branch is allowed, but the choice is recorded — in its
`state.md` and with `sdd track claim <slug> --branch <name>` — so `sdd doctor`
can report `session_branch_mismatch` when a session runs on the wrong one. A
session on the wrong branch is how a stage ends up implemented twice.

## Git worktrees created by your agent tool

Some agents (Kilo Code, Claude Code with worktrees, Cursor) create a git
worktree on their own. A worktree is a **full copy of the project, including its
own `.sdd/`** — a second, stale source of truth — and it duplicates every file
(and, after an install, every dependency). It also pollutes test, lint and
type-check globs with copies of the code.

- If the working directory is a **linked worktree** (`.git` is a file, not a
  folder), **stop**: continue from the main checkout. Never read or edit `.sdd/`
  inside a worktree.
- `sdd doctor` reports `inside_linked_worktree` and `nested_worktree_copies`;
  `sdd fix --gitignore` adds the folders to `.gitignore`; also exclude them from
  the test, lint and type-check globs of the project.
- Tracks are the kit's answer to parallel work: same tree, checked footprints.
  Worktree-per-track is not managed by the kit; if you truly need an isolated
  build/runtime, create the worktree **outside** the project folder and keep the
  `.sdd/` index single.

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
   **Collision check before you fork.** For each candidate ask three questions:
   (a) which files/directories will it change? (b) which shared numbers will it
   consume (migrations, canonical stage numbers)? (c) which exclusive resources
   does it need (dev server, database, device) — and is any stage
   *stability-sensitive*? Then declare and check:

   ```text
   sdd track claim <slug> --stage <local stage> --path "src/billing/**" [--seq migration] [--runtime db-write] [--stability-sensitive]
   sdd track check
   ```

   **MUST NOT** open the tracks while `sdd track check` fails. Pull the colliding
   stage out and sequence it (`Depends on`). For each track you do open:
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
   files, and only the paths its track has claimed."*

2. **Working inside a track.** Behaves exactly like the normal
   SPECIFYING → IMPLEMENTING → CLOSING flow — delegate the actual mechanics
   to `sdd-specify` / `sdd-implement` / `sdd-close` — except stage folders
   are created under `tracks/<slug>/stages/NNN-<slug-etapa>/` (local
   numbering, never directly under the canonical `stages/`). Hard rules:
   - **MUST NOT** write to any `tracks/<other-slug>/` path.
   - **MUST NOT** edit files claimed by another track. Need a file outside your
     claim? Amend the claim (`sdd track claim`), re-run `sdd track check`, and
     only then edit.
   - **MUST NOT** write to `constitution.md` or `roadmap.md` except via the
     narrow incorporation step (next item) — no trimming `Current state`,
     no touching another track's `### Active tracks` row, no regenerating
     `roadmap.md` (that is `sdd-reconcile`'s job, run once all tracks of
     interest have reached a stable point — step 4).
   - Get shared numbers with `sdd seq next <name> --track <slug>`; never guess
     "the next migration number".
   - Track-local progress (what's active *within this track*, what's next)
     lives in `tracks/<slug>/state.md`, not in the shared `Current state`.

3. **Closing a stage inside a track / incorporating it.** Run `sdd-close`
   normally for the stage's `report.md`/`todo.md` mechanics. Then:
   1. `sdd track verify <slug>` — every changed file must fall inside a claim.
   2. `sdd track incorporate <slug> <stage>` (add `--dry-run` to preview). Under a
      lock it takes the **next free number** (checking disk, §5 and
      `.reservations.json`), moves the folder from
      `tracks/<slug>/stages/NNN-<slug-etapa>/` to
      `stages/<next-free-number>-<slug-etapa>/`, appends the §5 row and releases
      the stage's claims. It is an isolated rename, never a renumbering of the
      existing queue. Without the CLI, do the same by hand.
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
   unblocked; decide with the user the single next `Active stage`; and drop the
   finished tracks' rows from `### Active tracks` (a track absent from that table
   is treated as concluded). Do **not** delete the finished `tracks/<slug>/`
   directories — leave them as historical evidence.

A track parked on purpose (waiting for the client, another team, a decision) stays in
`### Active tracks` with its State set to `on hold` (or `em espera`); the doctor then
does not report it as `track_not_started`. Set the State back when work resumes.

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
  breaking the shared build while it runs. When the reason is stability, note
  it beside the stage (e.g. in its slug or a spec line) so a later reader
  knows the dependency is about build stability, not consumed output.

A **footprint collision** is a third reason: two stages that touch the same
files, numbers or exclusive resources are chained with `Depends on` too.

`sdd-roadmap` declares a join stage's `Depends on` cell when the fork/join
shape is planned (even before the tracks are actually opened via
`sdd-track`). `sdd-specify` and `sdd-implement` both carry a short
MUST-NOT-start rule checking that column before beginning a stage. `sdd
doctor` flags (WARNING, never blocking) a join stage that was started while
a listed track dependency is still pending — catch-early, not a gate.

## Rules

- One track, one agent session, one `state.md` — never two sessions editing
  the same `tracks/<slug>/state.md`.
- **Stages in different tracks must be unable to affect each other.** Footprints
  are declared before the spec is locked and verified before the stage is
  incorporated; a failing `sdd track check` is never overridden.
- **Tracks isolate the index, not the build.** A stability-sensitive stage
  (needs a stable shared build/runtime/device) is never a parallel sibling of
  a track that mutates shared code in the same window — sequence it after via
  `Depends on`.
- `constitution.md §5` remains the ONLY canonical index; a track's
  `state.md` is disposable scratch, never a second source of truth.
- The next-free-number a track stage gets at incorporation comes from the
  **same pool** §5's Provisional queue draws from when it promotes a solo
  stage — whichever closes first gets the next `NNN`, regardless of planning
  order. `sdd track incorporate` serializes that pool.
- `roadmap.md` regeneration only happens via `sdd-reconcile`, never inside a
  track's own incorporation step.
- **Mid-flight structural decisions are the one real collision risk the
  footprints do not close.** If a structural decision surfaces inside a
  track (per `sdd-decide`'s "structural decision mid-flight"), it touches
  §2/§3 of the constitution — those sections are **not** append-only the
  way §5 is. Warn the user explicitly and ask the other track's session to
  pause (or be aware) before editing §2/§3 while two sessions are live.
