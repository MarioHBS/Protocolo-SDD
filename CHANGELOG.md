# Changelog — sdd-cli

All notable changes to the sdd-cli kit. Versions follow a pragmatic
`MAJOR.MINOR.PATCH`: breaking changes bump MAJOR, additive changes bump MINOR,
small additive content changes and fixes bump PATCH. Any `estimates.md`
produced by an older version remains valid — the templates are additive.

## [3.2.1] — 2026-08-27

### Changed
- **Tracks isolate the index, not the build — made explicit.** The parallel
  tracks feature (3.2.0) isolates each track's `.sdd/` scratch area, but two
  tracks still share one working tree, build, runtime and device. That
  boundary was never stated, so a **stability-sensitive stage** (manual/
  on-device QA, a release build, e2e, benchmarking — anything accepted by
  *running the app*) could be opened as a parallel sibling of a track that
  mutates shared code, and then get blocked by that track leaving the build
  red. `sdd-track` now spells out what tracks do and do not isolate, and
  classifies such stages.
- **Parallelization test in `sdd-roadmap` corrected.** "Independent slices of
  work" now explicitly means independent in **data/order AND in the shared
  build/runtime/device** — not just data/order. A stability-sensitive stage
  is planned as a *sequenced* stage, never a parallel sibling of a mutating
  track.
- **`Depends on` (§5) documented for both reasons.** The existing join-stage
  column now also carries stability sequencing: a stage may depend on tracks
  because it needs their *result* or because it needs the shared build
  *stable*. Same MUST-NOT-start enforcement in `sdd-specify`/`sdd-implement`,
  no new mechanism.
- **Opening a track gained a stability check** (`sdd-track` step 1): before
  forking, confirm no candidate track's stage needs a stable build while a
  sibling mutates shared code in the same window — if it does, sequence it
  instead of parallelizing it.
- **`track-state.template.md`** gained "Mutates shared code / build" and
  "Needs build stability" fields so the collision is declared up front.

## [3.2.0] — 2026-08-17

### Added
- **Parallel tracks** — two or more stages can now be worked at the same
  time by separate agent sessions, without git worktrees (not every project
  using this kit is under version control). Governed by the new
  `sdd-track` skill (a third cross-cutting utility, alongside
  `sdd-reconcile`/`sdd-document`). Each track gets its own scratch area
  (`.sdd/tracks/<slug>/state.md` + `.sdd/tracks/<slug>/stages/` with local
  numbering) that only its own agent session writes to; `constitution.md
  §5` stays the single canonical index — a track's stages are only
  appended there (moved into the shared `stages/` queue) at incorporation,
  never a second permanent index. `sdd init` now scaffolds an empty
  `.sdd/tracks/` alongside `.sdd/stages/`.
- **Fork/join** — a stage in §5 can declare (`Depends on` column) that it
  must wait for one or more tracks to finish before starting. `sdd-roadmap`
  declares the dependency when the plan is drawn; `sdd-specify` and
  `sdd-implement` both refuse to start a join stage while a listed track is
  still open. This composes: the queue can fork into tracks and join back
  to sequential as many times as the roadmap needs.
- **Track hygiene checks** in `sdd doctor` / `sdd-reconcile` — an opened
  track with no stage ever started, a track idle 14+ days with unfinished
  stages, or a completed stage still sitting under `tracks/<slug>/stages/`
  instead of being incorporated. Report-only, never blocking; produces zero
  output for a project that has never opened a track.

### Changed
- `sdd-close` (step 5) and `sdd-reconcile` (steps 1-3) gained conditional
  notes for the tracked-stage case: incorporation (move + append to §5)
  replaces a plain index update, and `roadmap.md` regeneration is
  deliberately deferred from per-track close to `sdd-reconcile`'s single
  pass, so two tracks incorporating around the same time never race on
  that file. The untracked path (stages living directly under `stages/`,
  with or without the existing out-of-order letter suffix) is unaffected.
- `constitution.md`'s `## Current state` gained an optional `### Active
  tracks` sub-table, only present once a track is opened — a project that
  never opens one keeps the exact same `Current state` shape as before.

## [3.1.0] — 2026-08-17

### Added
- **`sdd update`** — new command for syncing patch/minor kit changes within
  the same major version, as an alternative to `sdd migrate` for small
  bumps. Unlike `migrate` (which always does a full `.sdd/skills/` +
  `.sdd/templates/` wipe and recopy), `update` diffs each managed file's
  old-bundled vs. new-bundled content and only touches files that actually
  changed: hand-edited files are detected and preserved (backed up under
  `.sdd/.pre-migrate-backup/<timestamp>/`, never silently overwritten),
  files removed upstream are flagged rather than deleted, and files added
  upstream (e.g. a new template) are copied in. Requires an existing
  `.sdd/.sdd-manifest.json` as a diff baseline — legacy v1 projects should
  run `sdd migrate --to v2` first. Refuses to run across a major-version
  boundary, pointing at `sdd migrate --to vN` instead. Supports `--dry-run`.
- `manifest.parse_version()` — small stdlib-only semver tuple parser/compare
  used by `sdd update` to decide major vs. minor/patch (no new dependency).
- `tests/test_update.py` — first automated test coverage for the
  upgrade-path commands (`migrate` had none); also adds a regression guard
  asserting `pyproject.toml`'s version and `content/VERSION` never drift
  apart again (this exact drift happened once before, see 3.0.1).

## [3.0.2] — 2026-08-11

### Added
- **`templates/estimates.template.md`** — canonical living-estimate template.
  Until v3.0.1 the skills (`sdd-roadmap` step 5, `sdd-close` step 10) referenced
  `estimates.md` but no template existed; each project built its own. Now the
  kit ships the structure: per-stage projection (by effort block), accumulated
  closed, pending, calendar projection, and three forecast tables —
  **final conclusion**, **per-block** and **intermediate milestones**.
- **Per-block forecast** in the estimates template — granular intermediate
  between per-stage and final-conclusion. Chained in roadmap order; each block
  starts at the previous block's realistic end, so the last block's realistic
  date matches the final-conclusion realistic date. Recalculated in the same
  pass as the final conclusion.

### Changed
- **`sdd-roadmap` step 5** now points to `templates/estimates.template.md` and
  seeds the two forecast tables for `sdd-close`/`sdd-reconcile` to keep alive.
- **`sdd-close` step 10** spells out the recalculation (cadence, per-block sum,
  chaining, milestone migration) and makes explicit that both forecast tables
  are overwritten on every close — one close, one recalc; no stale forecasts.

### Fixed
- None.

## [3.0.1]

- Maintenance release. `content/VERSION` marker aligned with `pyproject.toml`.

## [3.0.0]

- Kit v3 baseline (skills, templates, constitution settings, language-aware
  generation, mojibake tooling, `sdd doctor`).
