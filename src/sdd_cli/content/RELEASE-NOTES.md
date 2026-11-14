# Release notes

One section per version, newest first. `sddkit update` prints the sections between the installed
kit and the bundled one; `sddkit update --notes` prints them again without changing anything.
A line starting with `Manual action:` is something the project has to do by hand, because the
kit never edits the constitution or any other file you own.

## 4.8.1

- `sddkit doctor` notes a kit backup folder that Git still sees (`backup_not_ignored`: `.sdd/.pre-fix-backup/` from `fix --weight`, `.sdd/.pre-migrate-backup/` from `migrate`); `sddkit fix --gitignore` adds the missing lines to `.gitignore` without touching the rest of the file.
- The manifest now records a hash that does not depend on line endings, so `manifest_eol_drift` stops coming back after a Git checkout. Manual action: if `sddkit doctor` still notes `manifest_eol_drift`, run `sddkit fix --manifest` once; manifests written by older kits keep working.
- `lock_without_audit` no longer asks for an audit of a stage that is already in `CLOSING` or whose `todo.md` has no open item: the spec was locked before the gate existed and is already implemented.
- `mojibake_v1` no longer reads the `?` of a URL query string (`/reports?range=2026-13`) as a lost accent.

## 4.8.0

- `sddkit update` now prints these notes, and `sddkit update --notes` reads them again.
- Manual action: if the stage index (section 5) has no `Weight` column, `sddkit fix --weight --dry-run` shows the column it would add; drop `--dry-run` to apply it (a backup is kept in `.sdd/.pre-fix-backup/`).
- New skill `sdd-audit` and template `audit.md`: a stage that is not `light` is audited cold before `Status: locked`, and the spec records it in a `Locked-by-audit:` line. `sddkit doctor` reports a locked, still-open stage without it (`lock_without_audit`, a note) or with a line that disagrees with `audit.md` (`lock_audit_mismatch`).
- Claude Code gets a read-only subagent, `.claude/agents/sdd-audit.md`, added only when it does not exist yet. An agent of your own is never overwritten.
- Manual action: project-specific audit lenses and the paths that force a full audit go in `.sdd/audit-lenses.md` (a file you own; the kit never creates or edits it).
- A `light` criterion is now checkable (files touched, no new test, no contract, data or security change) and `sdd-close` re-weighs the rest of the queue.
- `sddkit doctor` notes a stale global `sdd` skill (`global_skill_stale`); `sddkit update --global-skill` rewrites `~/.claude/skills/sdd/SKILL.md` (with a backup).

## 4.7.0

- Optional `Weight` column in the stage index: `light: <reason>` marks a trivial stage; empty or `full` is the default.
- Manual action: the kit never edits your constitution, so add the `Weight` column yourself if you want to use it (4.8.0 adds `sddkit fix --weight` to do it for you).
- `sddkit doctor` relaxes only the EDD checklist check on a `light` stage and reports `edd_no_criteria` for a closed stage whose `evals.md` has no criterion.

## 4.6.0

- Design system / cross-cutting UI conventions became a structural decision category in `sdd-decide` and `sdd-discover`.
- `sdd-decide` weighs a contested decision from 2-3 perspectives and may suggest a bounded web search for references.
- `sddkit init --discovery` starts in `DECIDING` instead of jumping to `SPECIFYING`.

## 4.5.0

- The executable is now `sddkit`; `sdd` stays as a deprecated alias removed in v5.
- Manual action: replace `sdd <command>` with `sddkit <command>` in your own scripts, CI and notes.

## 4.4.0

- `sddkit proposals collect|list|show|send` gathers the improvement proposals of your projects and packages them for the kit.

## 4.3.2

- A hand-edited managed file stays visible after the first update (`doctor` and `update` keep reporting it).

## 4.3.1

- A precedence table (who rules when documentation, a locked decision and the code disagree) was added to the kit README.

## 4.3.0

- Every shim and the kit README say that the CLI is a Python binary already on PATH, never `npx`/`npm`.
- Track lifecycle and hygiene improvements in the doctor.
