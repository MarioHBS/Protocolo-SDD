# sddkit — usage manual (kit {{VERSION}})

Spec-Driven Development scaffolding for AI coding agents.

`sddkit` installs the method and keeps it honest; it does not think for you. It
copies files, records a manifest and runs **deterministic** checks and repairs.
All the reasoning — understanding your project, asking questions, writing specs —
lives in the skills under `.sdd/skills/` and runs inside your AI agent. The two
meet in a few places where the CLI asks the *user* directly (`sddkit init`,
`sddkit document`).

Commands by purpose:

| Purpose | Commands |
|---------|----------|
| Set up | `sddkit init`, `sddkit providers`, `sddkit update`, `sddkit migrate` |
| Diagnose | `sddkit doctor`, `sddkit fix`, `sddkit health`, `sddkit context`, `sddkit evaluate` |
| Work | `sddkit session`, `sddkit scaffold`, `sddkit track`, `sddkit seq`, `sddkit deps`, `sddkit impact` |
| Document | `sddkit document`, `sddkit manual` |
| Observe | `sddkit dashboard` |
| Feedback | `sddkit proposals` |

Every command accepts `--help` with examples. Commands that report findings accept
`--json` for automation.

---

## Install

The kit is installed from its checkout (it is not published to a package index):

```bash
pipx install .                    # from the sdd-cli folder; or: uv tool install .
pipx install '.[dashboard]'       # add the optional dashboard (rich + textual)
sddkit --version
```

Python 3.12 or newer is required.

The command was called `sdd` before kit 4.5.0. `sdd` is still installed as a deprecated
alias: it behaves exactly like `sddkit`, prints one warning line on stderr (stdout and
`--json` are unchanged) and will be removed in v5. Agent permissions and notes written
as `sdd ...` keep working until then; rewrite them to `sddkit ...` at your own pace.

---

## Set up

### `sddkit init [PATH]`

Installs the kit into a project (default: current directory).

| Flag | Meaning |
|------|---------|
| `--provider KEY` | Agent to install a shim for. Repeatable — several agents can share one `.sdd/`. |
| `--language CODE` | Language for interactions and generated artifacts (e.g. `pt-BR`). |
| `--estimation` | Enable schedule estimate tracking. |
| `--docs` | Enable documentation planning (offers `sddkit document` at the end). |
| `--tracks` | Enable parallel tracks (`sdd-track`). |
| `--edd` | Enable Eval Driven Development. |
| `--discovery FILE.json` | Import a validated `sdd-discovery/v1` pre-project contract; previews and confirms before writing. |
| `--dashboard-ui NAME` | Default dashboard renderer (`static`, one panel, or `interactive`, a live TUI). |
| `--force` | Overwrite managed files and shims. |
| `-y`, `--yes` | Non-interactive; accept defaults. |

```bash
sddkit init                                        # interactive
sddkit init --provider claude --language pt-BR -y  # agent-driven, no prompts
sddkit init --provider claude --provider cursor    # two agents, one .sdd/
sddkit init . --discovery discovery.json -y        # reviewed discovery, non-interactive import
```

`init` never overwrites `constitution.md`, `roadmap.md` or `stages/`. Re-running
on an initialized project tells you to use `update` or `migrate`.

Use the `sdd-discover` skill before initialization to conduct the interview and
produce both `discovery.md` (human review) and `discovery.json` (CLI import).
The JSON contains project, language, features, vision, decisions, open questions,
backlog and an ordered `stages` list. The first stage becomes canonical `001`;
the rest form the provisional queue. `init` never waits for input without a TTY:
an import then requires `--yes` after successful validation.

### `sddkit providers [--plain]`

Lists supported agents. Available: {{PROVIDERS}}. `--plain` prints bare keys, one
per line — for an agent that must discover a valid `--provider` value itself.

### `sddkit update [PATH] [--dry-run] [--major]`

Syncs managed files (`README.md`, `skills/`, `templates/`, shims) when the bundled
kit is a **minor or patch** step over what is installed. It diffs old-bundled
against new-bundled per file, touches only what changed and **backs up** any file
you edited by hand under `.sdd/.pre-migrate-backup/<timestamp>/`. Provider shims
(for example `.claude/commands/sdd.md`) are refreshed the same way when they still
match what the manifest recorded; an edited shim is kept. New managed
files (a new template, for example) are added. It never touches `constitution.md`,
`roadmap.md`, `stages/`, `backlog.md`, `documentation.json` or any other file of
yours. It refuses to cross a major version — use `migrate` for that (`--major`
routes through the same planner).

### `sddkit migrate --to v4 [PATH] [--dry-run] [--provider KEY]`

Upgrades an older `.sdd/` (v1, v2, v3) to the current major.

- **Replaces** managed files: `.sdd/README.md`, `.sdd/skills/**`,
  `.sdd/templates/**`, and the provider shims.
- **Never touches** your files: `constitution.md`, `roadmap.md`, `stages/**`.
- Hand-edited managed files are detected via the manifest and backed up before
  replacement.
- `--provider KEY` (repeatable) replaces the recorded providers; shims of a
  provider you drop are removed only if they are byte-identical to the kit's own.
- `--fix-mojibake` repairs deterministic double-encoding before migrating.
- `--dry-run` shows what would change without writing.

After migrating, a few constitution edits remain manual: the CLI writes
`.sdd/.migration-todo.md`, which the agent walks the owner through one confirmed
step at a time, ending with the `sdd-reconcile` skill.

### `sddkit migrate --edd-source-of-truth [PATH] [--dry-run] [-y]`

An opt-in migration for existing EDD stages. It plans the conversion, prints the
stages and E-NNN IDs, and asks for confirmation before writing (or requires `-y`
without a TTY). It preserves unambiguous criteria in `evals.md`, replaces spec
section 5 with `See \`evals.md\`.`, and changes TODO final verification to point at
that source. A conflict between an existing eval list and the spec blocks all
writes and is listed for a human decision. Re-running after success is idempotent.

---

## Diagnose

### `sddkit doctor [PATH] [--json]`

Audits `.sdd/` **read-only**. It exits non-zero when any finding has severity
`error`. Findings (`code`, severity):

| Area | Code | Meaning |
|------|------|---------|
| Encoding | `mojibake_v2` (error) | Deterministic double-encoding; `sddkit fix --mojibake` repairs it. |
| | `mojibake_v1` (warn) | Possible lost accent (`?`); ambiguous, never auto-fixed. |
| | `invalid_utf8` (error) | File is not UTF-8. |
| Stages | `spec_without_todo`, `closed_open_todo` | Spec with no todo; closed stage with open checkboxes (`[x]`, `[-]`, `[!]` count as resolved). |
| Size | `constitution_oversized`, `long_table_cell`, `cold_file_oversized` | Files or rows that inflate every session. |
| Structure | `duplicate_h2`, `abs_file_links` | Repeated section heading; machine-specific `file:///` links (`sddkit fix --links`). |
| Settings | `feature_mismatch` | Constitution and manifest disagree on a feature (`sddkit fix --features`). |
| Settings | `tracks_setting_missing` | Real track activity but no explicit `Parallel tracks:` line in Settings — add `on` or `off` by hand. |
| Kit | `manifest_eol_drift` (note; `sddkit fix --manifest`), `managed_file_edited`, `readme_anchor_missing`, `migration_todo_pending` (note), `provider_shim_unmanaged`, `cli_older_than_project` | A managed file edited by hand that `sddkit update` kept (it stays listed after the version bump); a skill or template citing a README section the project's `.sdd/README.md` lacks; a shim on disk the manifest does not manage; a `.migration-todo.md` left behind by `sddkit migrate`; the CLI is older than the project's kit. |
| EDD | `edd_missing_evals`, `edd_missing_checklist`, `edd_eval_uncovered`, `edd_spec_not_pointer`, `edd_todo_not_evals`, `edd_missing_performance_doc`, `edd_milestone_without_evaluation`, `milestone_not_contiguous` | Evals without evidence, duplicate criteria, or milestone problems. |
| Backlog | `backlog_orphan`, `queue_row_without_section` | Backlog and provisional queue disagree. |
| Documentation | `docs_missing_file`, `docs_missing_header`, `docs_path_outside_project` | The documentation plan versus disk. |
| Session | `session_inconsistent`, `session_state_mismatch`, `session_branch_mismatch` | A saved session that no longer fits reality. |
| Tracks | `track_not_started`, `track_not_incorporated`, `track_closed_in_place` (note; `sddkit track close`), `track_overlap` (error), `track_claims_invalid`, `sequence_duplicate` (error) | Track hygiene, colliding footprints, two files with the same number. |
| Worktrees | `inside_linked_worktree`, `nested_worktree_copies`, `nested_worktree_copies_ignored` (note; already `.gitignore`'d, but a test/lint tool still scans it by path) | A stale copy of `.sdd/` (see `sddkit track`). |
| Dependencies | `dependency_inconsistent` | `sddkit deps` records that no longer hold. |

### `sddkit fix [PATH] [--dry-run] [--json]`

Repairs **deterministic** problems only; run with `--dry-run` first.

| Flag | Repairs |
|------|---------|
| `--mojibake` | v2 double-encoding. |
| `--eol` | CRLF/BOM to LF in `.sdd/` files. |
| `--links` | `file:///` links in the constitution become links relative to `.sdd/`. |
| `--features` | Manifest features follow the constitution's Settings (the file you edit by hand). |
| `--manifest` | Re-records the hash of managed files that differ from the manifest only by line endings (`manifest_eol_drift`). |
| `--gitignore` | Opt-in: ignore agent worktree folders (`.kilo/worktrees`, ...) in `.gitignore`. |
| `--all` | Everything except `--gitignore` (the default with no flag). |

Exit status: `0` nothing to repair, `1` repairs applied (or, with `--dry-run`,
would be), `2` something needs a human.

### `sddkit health [PATH] [--json]`

A score from the doctor findings: 100 minus 25 per error and 5 per warning.

### `sddkit discover [PATH] [--check FILE] [--against PROJECT]`

Explains the discovery flow and prints where the `sdd-discover` skill file lives
(this project's copy and the installed kit's), so it can be given to any AI
provider: the skill interviews you and writes `discovery.md` (for review) and
`discovery.json` (contract `sdd-discovery/v1`). `--check FILE` validates the JSON
and prints its summary without writing anything. `--against PROJECT` also compares
the planned stage slugs with the project's canonical index and provisional queue:
which planned stages are missing, and which project stages the discovery does not
cover. It is a comparison by name (a renamed or split stage appears on both lists).
Import into a new project with `sddkit init PATH --discovery FILE`.

### `sddkit context [PATH] [--budget] [--json]`

Prints what a session needs to start — Settings and Current state, the active
stage's files — and **nothing more**. `--budget` adds each file's size and token
estimate (bytes/4), split into **hot** (read at startup) and **cold** (read only
when a task needs it), and what reading the whole constitution would have cost.
Agent shims call it at startup.

### `sddkit evaluate [PATH] [--write] [--json]`

Captures local, sanitized evidence about how the kit behaved in this project.
`--write` saves `.sdd/kit-evaluation/snapshot.json`; the folder is normally
ignored by Git.

---

## Work

### `sddkit session <resume|status|pause|close|sync>`

A resumable work context (`.sdd/.session.json`, or per track with `--track`) so
interrupted implementation continues where it stopped. `sync` creates or
refreshes it while the state is IMPLEMENTING and records the Git branch;
`pause --reason planned|emergency|context_switch --context TEXT --task ID` records
why work stopped; `resume` shows it; `close` deletes it once the report exists.

### `sddkit scaffold STAGE [PATH] [--track SLUG] [--dry-run]`

For a stage with a **locked** `spec.md`, creates the missing `todo.md` (from the
spec's acceptance criteria) and, with Eval Driven Development on, `evals.md` and
`checklist.md`. Never overwrites.

### `sddkit track <claim|check|verify|incorporate|close>`

Parallel tracks share **one working tree**, so nothing physical keeps two agent
sessions apart. The CLI makes the separation checkable: two stages may live in
different tracks only if they cannot affect each other — not through the files
they edit, the numbers they take from a shared sequence, or the runtime resources
they need exclusively.

- `sddkit track claim SLUG --stage ID --path GLOB... [--seq NAME] [--runtime NAME] [--stability-sensitive] [--branch NAME]`
  records the track's footprint in `.sdd/tracks/<slug>/claims.json`.
- `sddkit track check [--json]` fails (exit 1) when two active tracks' footprints
  overlap. The fix is to sequence the stages with `Depends on`, not to tolerate it.
- `sddkit track verify SLUG [--since REV]` fails when real Git changes (untracked
  files included) fall outside every claim, or inside two. A file that only a
  sibling track claims is that track's work and is ignored.
- `sddkit track incorporate SLUG STAGE [--dry-run]` moves a **closed** track stage into
  the canonical queue: under a lock it takes the next free number (disk, section 5
  and the ledger), renames the folder, appends the index row and releases the
  claims. Two sessions can no longer take the same number.
- `sddkit track close SLUG [--archive] [--dry-run]` finishes a track once every
  local stage is incorporated and no claim remains: marks `state.md` CLOSED,
  drops its row from `Active tracks`. `--archive` also moves the folder to
  `.sdd/tracks/_closed/<slug>` (a closed track left in place is reported as
  the note `track_closed_in_place`).

Agents such as Kilo Code create git **worktrees** on their own: each is a full
copy including a stale `.sdd/`. `sddkit doctor` reports them; `sddkit fix --gitignore`
ignores them; exclude them from your test, lint and type-check globs too.

### `sddkit seq next NAME [PATH] [--track SLUG] [--json]`

Reserves the next number of a shared sequence (for example database migrations)
exactly once, in `.sdd/.reservations.json`. Sequences are declared in the
constitution's section 7 as `` `migration` = `db/NNNN_*.sql` ``; `migration`
defaults to `supabase/migrations/NNNN_*.sql` when that folder exists.

### `sddkit proposals <collect|list|show|send>`

Each project records friction with the kit in `.sdd/improvement-proposals.md`, one
`## IP-NNN — title` entry per episode. Ids restart at `IP-001` in every project, so
an entry is identified by (project, id).

- `sddkit proposals collect [PROJECT...] [--scan ROOT] [--json]` copies every entry
  into a local inbox, one file per entry named `<project>-IP-NNN.md`, where the
  project is its folder name. `--scan ROOT` adds every folder under `ROOT` that has a
  `.sdd/`. An entry ends at the next `##` heading of any kind, so `## Resolvidas`
  never leaks into the previous entry. Run it again at any time: a changed entry is
  updated, an unchanged one is left alone, and an entry that disappeared from its
  source stays in the inbox. A project that has a `.sdd/` but no
  `improvement-proposals.md` (the name is exact) gets an informational `note:` line, not
  an error, since it may simply have nothing to report. It never writes to, moves or deletes anything in the
  projects. The inbox is the user data folder (`%APPDATA%\sdd-cli\proposals` on
  Windows, `$XDG_DATA_HOME` or `~/.local/share` on Linux, `~/Library/Application
  Support` on macOS) unless `SDD_PROPOSALS_INBOX` points elsewhere.
- `sddkit proposals list [--all] [--json]` prints one line per collected proposal:
  `<project>-IP-NNN`, date, status keyword and title. Proposals the kit already
  absorbed are hidden unless `--all` is given.
- `sddkit proposals show <project>-IP-NNN [--json]` prints one proposal in full. A bare
  `IP-001` works only while a single project has it.
- `sddkit proposals send [ID...] --via file|url|issue [--all] [--output FILE] [--snapshot FILE]`
  packages the collected proposals for the kit maintainer. By default it takes every
  proposal not yet absorbed; give ids to pick some, or `--all` for everything. Each
  project is replaced by its anonymous code (`P1`, `P2`...), which lives only in the
  inbox. Before anything leaves, it scans the text for e-mails, absolute system paths
  (`C:\Users\...`, `/home/...`), secret-looking words (`api key`, `token`, `secret`,
  `password`) and the real project names, and asks about every hit; `--yes` never skips
  those questions. The scan is a heuristic, so read the package yourself.
  - `--via file` writes a Markdown package (`sdd-proposals.md` unless `--output` says
    otherwise, never overwriting) and sends nothing.
  - `--via url` prints the exact text, asks, then opens a pre-filled issue in the
    browser; you still press the button there.
  - `--via issue` does the same but creates the issue with `gh`. Without `gh`, without a
    login, or when it fails, it says why and writes the file instead.
  - `--snapshot FILE` appends a `sddkit evaluate --write` `snapshot.json`.
  Projects and the inbox are never changed.

### `sddkit deps <add|remove|list|graph>`

Records dependencies on other local projects (`--kind requires|provides`,
`--stage`, `--description`); `graph --format mermaid` draws them.

### `sddkit impact DECISION [PATH] [--json]`

Lists every `.sdd/` artifact that mentions a locked decision such as `D-013` —
read it before changing the decision.

---

## Document

### `sddkit document [PATH] [--resume] [--answers FILE] [--create-stubs] [--dry-run]`

Documentation as an **active** tool: the CLI interviews you, one question at a
time, until the plan is detailed:

1. depth — minimal, medium or comprehensive — with a recommendation drawn from
   the real project (stages, tracks, stacks, existing docs, the vision's subject);
2. who reads it and what a wrong document costs; the documents' language;
3. **where the files live**: a base folder (default `docs/`, it may be outside
   `.sdd/`), an optional location per document, and a place outside the project
   folder only after you explicitly confirm it;
4. the list of documents (name, purpose, owner stage) — add, remove, edit;
5. numbering (`DOC-001`…) and the header every document carries (version, date,
   "planned" marker);
6. which stages must refresh each document when they close;
7. documentation that already exists: adopt it into the plan or ignore it.

It saves `.sdd/documentation.json` (yours: `update`/`migrate` never touch it),
turns the Documentation feature on in the constitution **and** the manifest, and
leaves a one-line pointer in section 7. Answers are saved after every step:
`--resume` continues an interrupted interview. `--create-stubs` creates the
missing files (existing files are never overwritten).

Without a terminal — an agent session — pass the same answers as JSON:
`sddkit document --answers plan.json --dry-run`, then again without `--dry-run`.
`sddkit doctor` keeps the plan honest (missing files, missing headers).

### `sddkit manual [--md [FILE]]`

Prints this manual; `--md` writes it to a file. An agent that has never seen the
tool can run it to learn the workflow. `sddkit docs` is a deprecated alias, removed in
v5.

---

## Observe

### `sddkit dashboard [PATH] [--ui static|interactive|plain|web] [--out FILE] [--set-default]`

A read-only dashboard over the same data as `doctor` and `context`: overview,
constitution section sizes, stages and tracks, EDD, doctor findings with the
command that fixes each, and the session. `static` prints one panel and exits;
`interactive` is a live TUI that needs a real terminal; both need the optional
extras (`pipx install '.[dashboard]'`, or `pip install rich textual`) — `plain`
needs nothing. `web` writes a self-contained HTML snapshot (default
`.sdd/dashboard.html`, or `--out FILE`), with no server and no dependencies: open
the file in the IDE or a browser and re-run the command to refresh it.
`rich`/`textual` still work as deprecated aliases for
`static`/`interactive`. `--set-default` records the renderer in the manifest.

---

## What gets installed

```text
.sdd/
+-- README.md            the methodology (managed)
+-- constitution.md      settings, state, decisions, canonical index (yours)
+-- roadmap.md           high-level stage view, derived from the index (yours)
+-- CHANGELOG.md         long-form structural history (yours)
+-- skills/              one skill per phase + utilities (managed)
+-- templates/           spec, todo, report, checklist, evals, backlog... (managed)
+-- stages/              your per-stage artifacts (yours)
+-- tracks/              parallel tracks: state.md, claims.json, stages/ (yours)
+-- backlog.md           detail of stages still in the provisional queue (yours)
+-- documentation.json   the documentation plan from `sddkit document` (yours)
+-- .sdd-manifest.json   version, language, flags, file hashes (managed)

<provider shim>          e.g. .claude/commands/sdd.md (managed)
.gitattributes           enforces LF (only if absent)
```

---

## The workflow

Once installed, everything happens inside your agent. Trigger the shim (`/sdd`
in Claude Code, Copilot, OpenCode; an always-on rule in Cursor, Trae, Windsurf)
and the agent reads `.sdd/`, finds the current state, and loads the right skill.

```text
INITIALIZING -> DECIDING -> ROADMAP -> +- SPECIFYING -> IMPLEMENTING -> CLOSING -+
                                       +----------- (repeat per stage) ----------+
```

| State | Skill | What it does |
|-------|-------|--------------|
| INITIALIZING | `sdd-init` | Ingests your description or TODO file; bootstraps `.sdd/` |
| DECIDING | `sdd-decide` | Asks the right questions; locks structural decisions (**the gate**) |
| ROADMAP | `sdd-roadmap` | Splits the project into stages; fills the canonical index |
| SPECIFYING | `sdd-specify` | Writes a self-contained spec + detailed todo for one stage |
| IMPLEMENTING | `sdd-implement` | Builds the stage from the spec, keeping `todo.md` honest |
| CLOSING | `sdd-close` | Verifies against ground truth; writes the report; points to the next stage |

Cross-cutting, any time: `sdd-reconcile` (realign indexes with disk),
`sdd-document` (plan and produce docs — only when that feature is on),
`sdd-track` (parallel tracks — only when that feature is on).

**The gate:** no production code while the state is `INITIALIZING` or
`DECIDING`. Implementation waits until every structural decision is locked.

**Ground truth:** disk and live services are the truth; the indexes and reports
are caches. Nothing is marked done without verification.

---

## Keeping sessions small

A session that reads everything pays for everything. At startup an agent reads
its shim, `.sdd/README.md` and the constitution **through `## 1.`** (Settings and
Current state); the rest of the constitution, prior reports and skills load only
when the task needs them, and `roadmap.md`, `estimates.md`, `CHANGELOG.md` and
inactive `tracks/*/state.md` are **cold**. `sddkit context --budget` shows the
numbers; `sddkit doctor` flags what makes them grow (an oversized constitution, long
table rows, absolute links, narrative in sections 5 and 6).

---

## Features and language

Recorded in `.sdd/constitution.md` under `Settings`; toggle by editing that block.
`sddkit fix --features` then brings the manifest in line, and `sddkit doctor` reports a
disagreement (`feature_mismatch`).

- **Language** — every interaction and artifact uses it. The skill instructions
  stay in English by design; your specs, reports and docs come out in your language.
- **Estimation** — off by default. Stage start/end dates are recorded in every
  report regardless, so enabling it later reconstructs past durations.
- **Documentation** — off by default. `sddkit document` plans it with you; the
  `sdd-document` skill produces and maintains it.
- **Parallel tracks** — off by default; see `sddkit track`.
- **Eval Driven Development** — off by default. `evals.md` is the single source of
  a stage's acceptance criteria (`E-NNN`); items may be `[x]` met, `[-]` not
  applicable, `[!]` evaluated and not met.

---

## Multiple agents on one project

Install several shims; they all point at the same `.sdd/`. The methodology,
artifacts and history are shared — only the trigger differs per agent.

```bash
sddkit init --provider claude --provider cursor --provider copilot
```
