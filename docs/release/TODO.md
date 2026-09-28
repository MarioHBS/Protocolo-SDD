# TODO — sdd-cli 4.2.2

Legend: `[x]` done and verified · `[ ]` pending. Details of each item are in [PLAN.md](PLAN.md).
Order: R2-01 first (protects data), then R2-02 and R2-03 (same family), then the texts and notes.

## Items

- [x] R2-01 — roadmap backup and warning before Task 7; full diff and explicit confirmation before removing unique content
- [x] R2-02 — one table of EN/PT heading aliases used by every detector; `ENCERRADA` marker; empty "no track" row
- [ ] R2-03 — `track incorporate` refuses an empty row before moving the folder; localized headers; clearer `verify`
- [ ] R2-04 — separate message for `manual` managed entries in `migrate`
- [ ] R2-05 — version labels derived from the kit (README title, `Migration TODO — <from> -> <to>`, omitted-task note)
- [ ] R2-06 — `doctor` note `migration_todo_pending`
- [ ] R2-07 — UTF-8 `stdout`/`stderr` at the start of `main()`

## Gate

- [ ] `python -m pytest -q` and `ruff check src tests` green; one new test per item from a fixture of the real episode
- [ ] `sdd migrate --dry-run` and `sdd update --dry-run` on a copy of a real project: no user file changes outside the preview
- [ ] `migrate --dry-run` on a copy of the roadmap of P4 lists what would be dropped
- [ ] `CHANGELOG.md` entry citing each item ID; version bumped in `pyproject.toml` and `content/VERSION`
- [ ] `docs/release/NOTES.md` with the verification results
- [ ] tag `v4.2.2`, fast-forward `main`, push branch, tag and `main` (each push confirmed by the owner)
