# Notes — sdd-cli 4.3.1

## Verification

- `python -m pytest -q`: 219 passed. `ruff check src tests`: clean.
- `sdd update --dry-run` (writes nothing) against two real projects, 2026-10-07:
  - K-entre-nos orchestrator (installed v4.0.0): only managed files listed (shims, `.sdd/README.md`,
    skills, templates); three templates and the `sdd-discover` skill would be added. No file of the
    project outside `.sdd/` managed content is touched. The jump spans 4.1 to 4.3, not only 4.3.1.
  - LSDI InterSCity (installed v4.2.2): only managed files (shims, README, six skills, two
    templates) and the `kit_version` bump.

## Left for later

- The rest of stage 12 (ADR in `.sdd/decisions/`) and stage 13 (documentation level) stay planned;
  the Settings-reader preparation of L-01 is the first commit of stage 13.
