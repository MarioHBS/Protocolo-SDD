# Release notes

One section per version, newest first. `sddkit update` prints the sections between the installed
kit and the bundled one; `sddkit update --notes` prints them again without changing anything.
A line starting with `Manual action:` is something the project has to do by hand, because the
kit never edits the constitution or any other file you own.

## 4.10.0

- Decision records (ADRs) now live in `.sdd/decisions/`, one file per record, whether or not the Documentation feature is on. `sddkit adr new "<title>" --decision D-NNN` creates the next one (status `proposta`; numbers are never reused) and `sddkit adr index` regenerates the index.
- The decision table (section 3) of a new constitution has a `Record` column that links each decision's record, and section 7 says where records live with `Decision records: internal` or `external — <path>`. Your constitution is not rewritten by `update`.
- New `sddkit doctor` checks read the records against section 3, section 7 and the index. A project that keeps no ADRs only gets one note (`decisions_dir_missing`).
- A discovery decision may carry `adr: true` (with `context` and `alternatives`); `init --discovery` then writes its record as a proposal next to its row, and `sdd-decide` accepts it with the row.
- The skills `sdd-decide`, `sdd-specify`, `sdd-close`, `sdd-init`, `sdd-document` and `sdd-discover` now say when a decision gets a record and how to create it with `sddkit adr`.
- Manual action: if your project already has decisions in section 3 (or ADRs kept elsewhere), run `sddkit adr init --dry-run`, then `sddkit adr init`. It asks what the project does not say, never invents it, and only creates files; it adds the `Record` column and the section 7 field after copying the constitution to `.sdd/.pre-fix-backup/`. Without a terminal, pass `--answers FILE` (see `sddkit manual`). Doing nothing is also fine: the doctor only notes it.

## 4.9.6

- The kit now writes LF into your project even when the package was built on Windows. Files already in CRLF stay that way until you run `sddkit fix --eol --manifest --dry-run` and then the same without `--dry-run`; the doctor notes them as `eol_crlf`.
- `sddkit track close` keeps what `State:` and `Last updated:` said (on a `Previous state:` / `Previous update:` line) instead of cutting multi-line bullets, and `--archive` lists the links it leaves behind.
- `sddkit hooks install --dry-run` shows what it would write, and says when `.claude/settings.json` is versioned in Git (`--local` keeps it out of the repository).
- `sddkit doctor --all` lists every occurrence of a repeated finding; run from a subfolder, `doctor` and `context` find the project above.
- `constitution_oversized` now measures what a session reads at start (Settings and Current state; 8 KiB). A big constitution is a `cold_file_oversized` note with its sizes. Set your own ceilings in Settings (`- **Constitution max size:** 75 KB`, `- **Cold file max size:** 60 KB`).
- `sddkit doctor --slim` lists the lines to move out of a big constitution and where each goes; `sddkit fix --slim` removes only template comments you never edited. The kit moves none of your text.
- Manual action: if the stage index has no `Weight` column and the doctor notes `weight_column_missing`, run `sddkit fix --weight --dry-run`, then without `--dry-run`.

## 4.9.1

- `sddkit doctor` notes when this project's kit is older than the installed `sddkit` (`kit_behind`). It is only a note; read `sddkit update --notes` and try `sddkit update --dry-run` before updating.
- With EDD on, a stage closed before EDD was turned on (it has a `report.md`, no `evals.md`, and its section 5 row says `done`) is now one note, `edd_closed_without_evals`, instead of two warnings. Nothing to do if the stage predates EDD.

## 4.9.0

- New `sddkit hooks install` registers two Claude Code hooks in `.claude/settings.json` (`--local`: `.claude/settings.local.json`), next to yours. It is opt-in: `init` and `update` never register a hook, and `sddkit hooks uninstall` removes only what the kit wrote.
- Before an edit, the `pre-edit` hook asks you to confirm when two active tracks claim the file, and warns when the session's track does not claim it. It never denies. After a stage `report.md` is written, the `post-edit` hook runs `doctor` and reports the count to the agent.
- The registered hook line ends in `|| true` and runs under bash, so a teammate whose `sddkit` is older than 4.9.0 (it exits 2 on an unknown command, which Claude Code treats as a block) can still edit; without bash installed the hook does not run.
- New `sddkit track guard FILE` gives the same answer by hand, so a project without hooks (or on another provider: only Claude Code has a tool hook) loses nothing.
- Manual action: to let the hooks tell which track a session works for, run `sddkit track claim <slug> ... --branch <name>` for a track on its own branch, or set `SDD_TRACK=<slug>` in that session; without either, only a collision is reported.

## 4.8.2

- `sddkit doctor` tells a kit backup folder Git already tracks (`backup_tracked`) from one Git merely sees (`backup_not_ignored`), because `.gitignore` does not stop a folder that is already committed. `sddkit fix --gitignore` no longer appends the same line again, and lists a tracked folder as unfixable.
- Manual action: if `sddkit doctor` notes `backup_tracked`, run `git rm -r --cached .sdd/.pre-migrate-backup` (or the folder it names) and commit; the kit does not edit your Git index.

## 4.8.1

- `sddkit doctor` notes a kit backup folder that Git still sees (`backup_not_ignored`: `.sdd/.pre-fix-backup/` from `fix --weight`, `.sdd/.pre-migrate-backup/` from `migrate`); `sddkit fix --gitignore` adds the missing lines to `.gitignore` without touching the rest of the file.
- The manifest now records a hash that does not depend on line endings, so `manifest_eol_drift` stops coming back after a Git checkout; manifests written by older kits keep working.
- Manual action: if `sddkit doctor` still notes `manifest_eol_drift`, run `sddkit fix --manifest` once.
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
