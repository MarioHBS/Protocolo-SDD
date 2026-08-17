# Changelog — sdd-cli

All notable changes to the sdd-cli kit. Versions follow a pragmatic
`MAJOR.MINOR.PATCH`: breaking changes bump MAJOR, additive changes bump MINOR,
small additive content changes and fixes bump PATCH. Any `estimates.md`
produced by an older version remains valid — the templates are additive.

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
