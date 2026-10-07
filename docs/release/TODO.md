# TODO — sdd-cli 4.3.1

Legend: `[x]` done and verified · `[ ]` pending. Details of each item are in [PLAN.md](PLAN.md).

## Items

- [x] M-06 — "Who rules when artifacts disagree" in the kit README; `sdd-close`, `sdd-document` and the report template cite it by heading

## Gate

- [x] `python -m pytest -q` and `ruff check src tests` green; new test for the precedence table
- [x] `sdd update --dry-run` on each real project: only managed files change
- [x] `CHANGELOG.md` entry citing M-06; version bumped in `pyproject.toml` and `content/VERSION`
- [x] `docs/release/NOTES.md` with the verification results
- [x] tag `v4.3.1`, fast-forward `main`, push branch, tag and `main` (each push confirmed by the owner)
