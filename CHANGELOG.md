# Changelog — sdd-cli

All notable changes to the sdd-cli kit. Versions follow a pragmatic
`MAJOR.MINOR.PATCH`: breaking changes bump MAJOR, additive changes bump MINOR,
small additive content changes and fixes bump PATCH. Any `estimates.md`
produced by an older version remains valid — the templates are additive.

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
