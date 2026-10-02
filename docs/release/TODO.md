# TODO — sdd-cli 4.3.0

Legend: `[x]` done and verified · `[ ]` pending. Details of each item are in [PLAN.md](PLAN.md).
Order: R3-01 first (foundation: `CLI_NAME`, invocation text), then R3-06 and R3-04 (small,
text/message), R3-05 (skill text only), R3-03 (doctor + git check-ignore), R3-02 (track
lifecycle), R3-07 last (needs an explicit design call during implementation).

## Items

- [x] R3-01 — `CLI_NAME` constant; shims/README/skills say `sdd` is a Python binary on PATH, never `npx`/`npm`; `doctor`/`context` print the executable path
- [x] R3-06 — dependency-missing message cites `sys.executable`; manual's `--ui` list reverified (already correct)
- [x] R3-04 — `backlog_orphan` message shows the expected queue-row format; template and skill carry an example
- [x] R3-05 — `sdd-specify`/`sdd-implement`/`sdd-close` gain a short markdown-hygiene checklist (blank lines around headings/lists/fences, language on every fence, heading instead of bold)
- [x] R3-03 — `nested_worktree_copies` consults `git check-ignore`; downgrades to a note and prints the test/lint exclusion snippet when already ignored
- [x] R3-02 — `sdd track close <slug>` (with `--archive`); `track_closed_in_place` doctor note
- [ ] R3-07 — `doctor` requires and validates an explicit `Parallel tracks: on|off` line whenever `Active tracks` or `tracks/*/state.md` exist (cheaper alternative from PLAN.md, not the full concept split — flagged for the owner)

## Gate

- [ ] `python -m pytest -q` and `ruff check src tests` green; one new test per item from a fixture of the real episode
- [ ] `sdd update --dry-run` on a copy of each evaluated project: only managed files change
- [ ] `CHANGELOG.md` entry citing each item ID; version bumped in `pyproject.toml` and `content/VERSION`
- [ ] `docs/release/NOTES.md` with the verification results
- [ ] tag `v4.3.0`, fast-forward `main`, push branch, tag and `main` (each push confirmed by the owner)
