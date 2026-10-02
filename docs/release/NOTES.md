# Notes — sdd-cli 4.3.0

Filled in as each item lands; verification results go here before the tag.

## R3-01 — CLI invocation guidance

All 9 shims (`content/shims/*`) and the installed README now share one
literal clause, checked by a test that folds whitespace and strips blockquote
markers so the README's wrapped blockquote line still compares equal to the
shims' single-line sentence. `doctor`/`context` print the resolved path of
`sys.argv[0]` when it exists on disk, falling back to `shutil.which(CLI_NAME)`
then to a literal "not found" string — never raises. `CLI_NAME` lives in
`content/__init__.py` next to `KIT_VERSION`; `build_parser()`'s `prog=` and
`--version` string are the only two call sites switched so far (the rest of
the CLI's help text still says `sdd` literally — acceptable for now, the
constant's job is to make the 4.5.0 rename a one-line change, not to rewrite
every string today).

## R3-06 — dashboard dependency message

`INSTALL_HINT` now names `sys.executable` before suggesting
`{python} -m pip install rich textual`, so the install command targets the
same interpreter that raised the `ImportError`. Reverified the manual's `--ui`
list against `DASHBOARD_RENDERERS`/the argparse `choices` in `cli.py`: both
already say `static`/`interactive`/`plain`/`web` with `rich`/`textual` as
deprecated aliases — this half of the item needed no change, just
confirmation that the 4.2.1 rename held.

## R3-04 — backlog_orphan format

The real episode: a bullet list with the slug in backticks, then a
`backlog.md#slug` anchor link, neither parsed, because `_queue_rows` only
reads markdown TABLE rows under the Provisional queue heading with a literal
`slug` column (`_index_checks.py`'s `_tables`/`_queue_rows`). The finding's
hint, `backlog.template.md` and the `sdd-roadmap` skill now all show the same
concrete row, `| my-slug | pending | — | See backlog.md#my-slug |`, so the
contract is visible in the three places someone would look.

## R3-05 — markdown hygiene checklist

Same short checklist, repeated (not pointed-to) in `sdd-specify`,
`sdd-implement` and `sdd-close`, since each is loaded independently and none
assumes the others were read in the same session. A test normalizes
whitespace (the checklist line wraps inside the Markdown source) and checks
all three files for the same core clause, plus the explicit "no line-length
rule" sentence — P4 wraps at ~80 columns, P2 disables MD013, so the kit
cannot pick a side. The automatic linter/fixer this episode also suggested
stays deferred (A-04): this item is the cause (nobody told the agent the
rules), not the backstop.

## R3-03 — nested worktree, git check-ignore

`_git_already_ignores` wraps `git check-ignore -q` and returns `True`/`False`
for a real answer, `None` for "could not tell" (no `git`, not a repository,
any other failure) — callers must treat `None` like the pre-existing
behavior, never like "not ignored". When it returns `True`, the finding code
changes from `nested_worktree_copies` (warn) to `nested_worktree_copies_ignored`
(note), whose hint names the three tool configs (`vitest.config`
`test.exclude`, `eslint.config` `globalIgnores`, `tsconfig` `exclude`) instead
of repeating "run `sdd fix --gitignore`" when that step is already done.

Chose to print the snippet in the hint rather than have `sdd fix` write into
`vitest.config`/`eslint.config`/`tsconfig` directly: those are arbitrary
JS/TS files (`.js`/`.ts`/`.mjs`, different export shapes), and `fix` is
documented as deterministic repairs only — editing them safely is a bigger,
separate capability, not a one-line fix.

## R3-02 — track lifecycle, `sdd track close`

`_tracks.close()` mirrors `incorporate()`'s shape: same lock
(`.sdd/tracks/.lock`), same refuse-instead-of-guess discipline (local stages
not incorporated, or claims still recorded, are errors, not warnings). It
marks `state.md` CLOSED by substituting the template's own `**State:**` and
`**Last updated:**` fields in place — a `state.md` that does not use that
field (truly free-form) is left untouched rather than guessed at — and drops
the track's row from `### Active tracks` via the same EN/PT heading lookup
R2-02 already uses. `--archive` moves the folder with plain `shutil.move`,
the same primitive `incorporate` already uses for stage folders, into a new
`tracks/_closed/` bucket that `_scan_tracks_v4` now skips entirely (its
contents are history, not a track to audit).

The finding code ended up `track_closed_in_place` (matching the sibling
codes `track_not_started`/`track_not_incorporated`) rather than the plan's
literal `closed_track_in_place` — consistency with the established
`track_<kind>` convention seemed more valuable than the exact string in the
plan, which was a working label, not a contract. Severity is `note`, not
`warn`: nothing is wrong, the folder just was not archived yet.

Three existing tests encoded the old silence as correct (`test_doctor.py`,
two in `test_tracks.py`) — updated, since that silence was exactly IP-008's
complaint, not a behavior to protect. Cross-file text references to
`tracks/<slug>/state.md` (reports, CHANGELOG) are **not** rewritten by
`--archive` — flagged as a known gap in the plan, unchanged here; the
command's own output names the old and new path so whoever archives can
grep for the rest by hand.
