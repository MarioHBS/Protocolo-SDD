# Notes — sdd-cli 4.2.2

## R2-01 — roadmap content during migration

`migrate --dry-run` now reports the roadmap's physical line count and the
number of nonempty lines outside Markdown tables. The latter is a conservative
review indicator: it includes headings and boilerplate and does not count text
inside custom table cells. The preview also shows the backup destination.

The real migration saves the exact original bytes in
`.sdd/.pre-migrate-backup/<timestamp>/.sdd/roadmap.md`, including the path in
the manifest backup ledger. Task 7 and the installed skills direct the agent
to compare the full proposed roadmap with the current one. Removing content
that exists only in the roadmap requires the owner's explicit confirmation.

The regression fixture has block grouping, a custom `Habilita` column and
1,132 lines of stage detail. The test checks the preview writes nothing,
the original roadmap and backup match byte for byte, and Task 7 gives the
review instruction. Verification results for the full release remain pending.

## R2-02 — localized constitution headings

Track, stage-index and backlog detectors share exact EN/PT heading aliases.
The Portuguese fixtures cover an incorporated track absent from `Trilhas
ativas`, `Status: ENCERRADA`, `em espera`, and the explicit "nenhuma trilha
aberta hoje" row. A separate fixture covers `Índice de etapas` and `Fila
provisória`, including the boundary between their tables.

## R2-03 — track incorporation and claims

The stage-index row is built and checked under the incorporation lock before
the stage is moved, the constitution is updated or a number is reserved. The
regression fixtures verify a complete row with Portuguese column names and no
persistent writes for an unrecognized header. A track without path claims now
passes `verify` when it changed only `.sdd/`; an unclaimed external file is
reported by path with a prompt to declare a claim if that track owns it.

## R2-04 — `manual` entries in the migrate preview

An entry whose recorded value is `manual` is a file the kit does not manage, so
`migrate` never replaces it. It now has its own line in the preview and in the
real run; the "will be backed up before replacing" text is left for kit files
only. The safety copy of a `manual` file is kept: it costs nothing and the
backup ledger stays a complete list of what was saved. The fixture is a project
whose manifest records a Copilot instructions file as `manual`; the tests check
the wording of both messages, that the file is untouched and that the ledger
lists its copy.

## R2-05 — version labels

The README title lost its `(v3)` suffix: the file is copied verbatim and hashed,
so a per-version title would have needed templating for no reader benefit. The
TODO generator now receives the version the project was at (`v1 (no manifest)`
for a legacy project) and appends "Tasks omitted from this file: 1-3 and 5
(precondition already satisfied at migration time)", derived from the tasks it
actually wrote. A second `migrate` run therefore rewrites the TODO as
`v4.x -> v4.x`; `test_migrating_twice_is_a_no_op` allows that one file to
change.

## R2-06 — migration TODO left behind

`migration_todo_pending` is a `note` (it never changes the exit code) and
disappears with the file, so an owner who deleted the TODO on purpose sees
nothing. It is listed in the manual's finding table, which
`test_manual_mentions_every_doctor_finding_code` requires.
