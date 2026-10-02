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
