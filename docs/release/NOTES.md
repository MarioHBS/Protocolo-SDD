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
