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
