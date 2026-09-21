# Changelog — sdd-cli

All notable changes to the sdd-cli kit. Versions follow a pragmatic
`MAJOR.MINOR.PATCH`: breaking changes bump MAJOR, additive changes bump MINOR,
small additive content changes and fixes bump PATCH. Any `estimates.md`
produced by an older version remains valid — the templates are additive.

## [4.1.0] — Unreleased

Driven by two real projects (Antologias Biló, kit 3.3.0, 102 stages; KNN Warehouse,
kit 4.0.0) and their improvement proposals. Minor release: additive, nothing in the
CLI or the manifest format breaks; `sdd update` (from 4.0.0) or
`sdd migrate --to v4` (from v2/v3) brings a project up to date.

### Added

- **Smaller sessions.** `sdd context [--budget] [--json]` prints only Settings and
  Current state, the active stage's files and what each file costs (hot vs cold).
  Shims and the kit README now say: read the constitution *through `## 1.`*, load
  `sdd-track` only when tracks are on, keep `roadmap.md`, `estimates.md`,
  `CHANGELOG.md` and inactive `tracks/*/state.md` cold. On the Biló project the
  startup read drops from ~25k to ~5k estimated tokens; on KNN from ~12k to ~4.7k.
  Section 5 rows carry no per-row links (paths are conventional) and stay under
  200 bytes; narrative belongs in `CHANGELOG.md`, not in sections 5 or 6.
- **Parallel tracks are checked, not trusted.** Stages in different tracks must be
  unable to affect each other. `sdd track claim|check|verify|incorporate` declares
  each track's footprint (paths, shared sequences, exclusive runtime resources),
  fails on overlap, compares real Git changes with the claims and moves a closed
  stage into the queue **atomically** (file lock, next free number).
  `sdd seq next <name>` hands out shared numbers (database migrations) once;
  sequences are declared in the constitution. `doctor` reports `track_overlap`,
  `sequence_duplicate`, `session_branch_mismatch`, a linked git worktree and nested
  agent worktree copies (Kilo creates full copies with their own stale `.sdd/`);
  `sdd fix --gitignore` ignores them. `sdd-track` is rewritten around this.
- **`sdd document`** — documentation as an active tool. It interviews the user (depth
  recommended from the real project, audience, where files live — outside `.sdd/`
  and even outside the project after confirmation — document list, numbering and
  header conventions, which stages refresh each document, existing docs to adopt),
  is resumable (`--resume`), accepts `--answers FILE` for agents and writes
  `.sdd/documentation.json`. `sdd init --docs` offers it.
- **Eval Driven Development and backlog in the skills.** `evals.md` is the single
  source of a stage's criteria; `[-]` (not applicable) and `[!]` (evaluated, not
  met) count as resolved; mid-stage evals get the next `E-NNN`; `backlog.md` is a
  first-class artifact (one section per provisional stage); a frozen-scope gate and
  an `Origin` field in the spec; an optional cross-cutting checklist; a credentials
  audit when adopting the kit on an existing project. The README lists the
  artifacts. New `doctor` findings: `edd_eval_uncovered`,
  `edd_milestone_without_evaluation`, `milestone_not_contiguous`, `backlog_orphan`,
  `queue_row_without_section`.
- **Sturdier diagnostics.** Findings for an oversized constitution, duplicate
  section headings, over-long table rows, absolute `file:///` links,
  constitution/manifest feature drift, unmanaged provider shims and a CLI older than
  its project. `sdd fix --links` writes links relative to `.sdd/`; `--features`
  syncs the manifest from the constitution.
- **`sdd dashboard`** has real views (overview and health, constitution sizes, stages
  and tracks, EDD gaps, findings with their fix, session) in rich, textual or plain
  (no dependencies) form. `--ui plain` needs no extras; a missing extra is an
  explained error and textual without a terminal refuses instead of hanging.
- Tests for `init`, `migrate`, `update` and `main`; headless dashboard tests; a CI job
  that installs the dashboard extras and fails on any skipped dashboard test.

### Changed

- **`sdd doctor` (human mode) lists every finding**, grouped by code with the command
  that fixes it, and exits non-zero on any error. It used to print "clean." while
  `--json` listed problems.
- **`--help` and the manual are complete.** Every command and subcommand has a
  description and runnable examples; `USAGE.md` documents all commands, the doctor
  codes and exit codes; `sdd manual` is the name of the manual and `sdd docs` a
  deprecated alias (removed in v5). INSTALL (en, pt-BR, es) requires Python 3.12 and
  shows the dashboard extras.
- The v1 language heuristic scores language-specific markers case-insensitively.
- Ruff rules are pinned in `pyproject.toml` so a new ruff release cannot turn CI red.

### Fixed

- `sdd context` no longer fails when `Active stage` is prose (`Etapa 091 (`slug`) ...`).
- Concluded tracks (dropped from `Active tracks`) are no longer reported as
  `track_not_started`; a dead track scanner that referenced an undefined constant
  (`NameError` since 3.2.0) was removed.
- The Kilo shim's opening sentence had become a heading.

### Deferred

Not in this release, recorded with the reason and the trigger to resume in the
maintainer's notes (`ADIADOS-SDD-CLI.md`): a `sdd-discover` phase, splitting the
kit README into a session card plus reference, a live edit guard for tracks (hook),
an opt-in worktree mode, `sdd ws doctor`, a type-checker, per-major migrator matrix,
and the package-distribution decision (PyPI or npm).

## [4.0.0] — 2026-09-15

### Added

- Structured sessions (`sdd session`), JSON diagnostics (`sdd doctor --json`),
  `sdd fix`, optional dashboard, EDD templates, stage scaffolding
  (`sdd scaffold`), local dependencies (`sdd deps`), decision impact
  (`sdd impact`) and a health score (`sdd health`).
- Major migration support from v2/v3 (`sdd migrate --to v4`,
  `sdd update --major`) with safer provider refresh.

### Changed

- The package requires Python 3.12 (PEP 701 f-strings); dashboard
  dependencies are extras.

## [3.3.0] — 2026-08-31

### Added
- **Kilo Code provider.** New `kilo` entry in `providers.py`, with its own
  content shim (`content/shims/kilo.md`, same `/sdd` trigger pattern as the
  other providers). The stale-shim cleanup in `sdd migrate` was generalized
  from a single hardcoded case (`AGENTS.md`/`generic`) into a loop that
  covers any registered provider, `kilo` included.
- **Provisional queue for stage numbering.** Mitigates the letter-suffix
  convention (`010-A`): future stages not yet up for specification are now
  recorded by slug alone, with no canonical `NNN`, in a new "Provisional
  queue" subsection of §5. A stage only receives its canonical number at
  **promotion** — normally when `sdd-close` points to the next stage, or
  sooner if the user deliberately fast-tracks an independent one. This
  removes the need for renumbering or letter suffixes to advance an
  independent stage, or to insert one ahead of another that has no number
  yet. The letter suffix stays reserved for inserting **among
  already-canonical stages**: an urgent stage next to one already `in
  progress`, or a late adjustment right before a stage that just turned
  canonical. The canonical-number pool is explicitly shared with parallel
  tracks: a promoted solo stage and an incorporated track stage draw from
  the same "next free `NNN`", assigned strictly in the order stages actually
  finish — never in planning order. A whole future track can also sit in the
  Provisional queue as a `track candidate` row until it is actually opened
  via `sdd-track`. Touches `README.md`, `constitution.md` (§5),
  `roadmap.md` + `templates/roadmap.template.md`, and the `sdd-roadmap`,
  `sdd-close`, `sdd-track` skills.
- **Parallel tracks become an opt-in feature.** Follows the same pattern as
  `Estimation tracking`/`Documentation`: a new `--tracks` flag and
  interactive prompt in `sdd init`, a `Parallel tracks` line in the
  constitution's `## Settings` (off by default), and a matching feature gate
  in the `sdd-track` skill (refuses to open a track when the setting is
  off). Lets projects that want a simpler flow skip tracks entirely.

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
