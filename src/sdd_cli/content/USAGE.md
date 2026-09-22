# sdd — usage manual (kit {{VERSION}})

Spec-Driven Development scaffolding for AI coding agents.

`sdd` installs the method and keeps it honest; it does not think for you. It
copies files, records a manifest and runs **deterministic** checks and repairs.
All the reasoning — understanding your project, asking questions, writing specs —
lives in the skills under `.sdd/skills/` and runs inside your AI agent. The two
meet in a few places where the CLI asks the *user* directly (`sdd init`,
`sdd document`).

Commands by purpose:

| Purpose | Commands |
|---------|----------|
| Set up | `sdd init`, `sdd providers`, `sdd update`, `sdd migrate` |
| Diagnose | `sdd doctor`, `sdd fix`, `sdd health`, `sdd context`, `sdd evaluate` |
| Work | `sdd session`, `sdd scaffold`, `sdd track`, `sdd seq`, `sdd deps`, `sdd impact` |
| Document | `sdd document`, `sdd manual` |
| Observe | `sdd dashboard` |

Every command accepts `--help` with examples. Commands that report findings accept
`--json` for automation.

---

## Install

The kit is installed from its checkout (it is not published to a package index):

```bash
pipx install .                    # from the sdd-cli folder; or: uv tool install .
pipx install '.[dashboard]'       # add the optional dashboard (rich + textual)
sdd --version
```

Python 3.12 or newer is required.

---

## Set up

### `sdd init [PATH]`

Installs the kit into a project (default: current directory).

| Flag | Meaning |
|------|---------|
| `--provider KEY` | Agent to install a shim for. Repeatable — several agents can share one `.sdd/`. |
| `--language CODE` | Language for interactions and generated artifacts (e.g. `pt-BR`). |
| `--estimation` | Enable schedule estimate tracking. |
| `--docs` | Enable documentation planning (offers `sdd document` at the end). |
| `--tracks` | Enable parallel tracks (`sdd-track`). |
| `--edd` | Enable Eval Driven Development. |
| `--dashboard-ui NAME` | Default dashboard renderer (`static`, one panel, or `interactive`, a live TUI). |
| `--force` | Overwrite managed files and shims. |
| `-y`, `--yes` | Non-interactive; accept defaults. |

```bash
sdd init                                        # interactive
sdd init --provider claude --language pt-BR -y  # agent-driven, no prompts
sdd init --provider claude --provider cursor    # two agents, one .sdd/
```

`init` never overwrites `constitution.md`, `roadmap.md` or `stages/`. Re-running
on an initialized project tells you to use `update` or `migrate`.

### `sdd providers [--plain]`

Lists supported agents. Available: {{PROVIDERS}}. `--plain` prints bare keys, one
per line — for an agent that must discover a valid `--provider` value itself.

### `sdd update [PATH] [--dry-run] [--major]`

Syncs managed files (`README.md`, `skills/`, `templates/`, shims) when the bundled
kit is a **minor or patch** step over what is installed. It diffs old-bundled
against new-bundled per file, touches only what changed and **backs up** any file
you edited by hand under `.sdd/.pre-migrate-backup/<timestamp>/`. New managed
files (a new template, for example) are added. It never touches `constitution.md`,
`roadmap.md`, `stages/`, `backlog.md`, `documentation.json` or any other file of
yours. It refuses to cross a major version — use `migrate` for that (`--major`
routes through the same planner).

### `sdd migrate --to v4 [PATH] [--dry-run] [--provider KEY]`

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

---

## Diagnose

### `sdd doctor [PATH] [--json]`

Audits `.sdd/` **read-only**. It exits non-zero when any finding has severity
`error`. Findings (`code`, severity):

| Area | Code | Meaning |
|------|------|---------|
| Encoding | `mojibake_v2` (error) | Deterministic double-encoding; `sdd fix --mojibake` repairs it. |
| | `mojibake_v1` (warn) | Possible lost accent (`?`); ambiguous, never auto-fixed. |
| | `invalid_utf8` (error) | File is not UTF-8. |
| Stages | `spec_without_todo`, `closed_open_todo` | Spec with no todo; closed stage with open checkboxes (`[x]`, `[-]`, `[!]` count as resolved). |
| Size | `constitution_oversized`, `long_table_cell`, `cold_file_oversized` | Files or rows that inflate every session. |
| Structure | `duplicate_h2`, `abs_file_links` | Repeated section heading; machine-specific `file:///` links (`sdd fix --links`). |
| Settings | `feature_mismatch` | Constitution and manifest disagree on a feature (`sdd fix --features`). |
| Kit | `provider_shim_unmanaged`, `cli_older_than_project` | A shim on disk the manifest does not manage; the CLI is older than the project's kit. |
| EDD | `edd_missing_evals`, `edd_missing_checklist`, `edd_eval_uncovered`, `edd_missing_performance_doc`, `edd_milestone_without_evaluation`, `milestone_not_contiguous` | Evals without evidence; milestone problems. |
| Backlog | `backlog_orphan`, `queue_row_without_section` | Backlog and provisional queue disagree. |
| Documentation | `docs_missing_file`, `docs_missing_header`, `docs_path_outside_project` | The documentation plan versus disk. |
| Session | `session_inconsistent`, `session_state_mismatch`, `session_branch_mismatch` | A saved session that no longer fits reality. |
| Tracks | `track_not_started`, `track_not_incorporated`, `track_overlap` (error), `track_claims_invalid`, `sequence_duplicate` (error) | Track hygiene, colliding footprints, two files with the same number. |
| Worktrees | `inside_linked_worktree`, `nested_worktree_copies` | A stale copy of `.sdd/` (see `sdd track`). |
| Dependencies | `dependency_inconsistent` | `sdd deps` records that no longer hold. |

### `sdd fix [PATH] [--dry-run] [--json]`

Repairs **deterministic** problems only; run with `--dry-run` first.

| Flag | Repairs |
|------|---------|
| `--mojibake` | v2 double-encoding. |
| `--eol` | CRLF/BOM to LF in `.sdd/` files. |
| `--links` | `file:///` links in the constitution become links relative to `.sdd/`. |
| `--features` | Manifest features follow the constitution's Settings (the file you edit by hand). |
| `--gitignore` | Opt-in: ignore agent worktree folders (`.kilo/worktrees`, ...) in `.gitignore`. |
| `--all` | Everything except `--gitignore` (the default with no flag). |

Exit status: `0` nothing to repair, `1` repairs applied (or, with `--dry-run`,
would be), `2` something needs a human.

### `sdd health [PATH] [--json]`

A score from the doctor findings: 100 minus 25 per error and 5 per warning.

### `sdd context [PATH] [--budget] [--json]`

Prints what a session needs to start — Settings and Current state, the active
stage's files — and **nothing more**. `--budget` adds each file's size and token
estimate (bytes/4), split into **hot** (read at startup) and **cold** (read only
when a task needs it), and what reading the whole constitution would have cost.
Agent shims call it at startup.

### `sdd evaluate [PATH] [--write] [--json]`

Captures local, sanitized evidence about how the kit behaved in this project.
`--write` saves `.sdd/kit-evaluation/snapshot.json`; the folder is normally
ignored by Git.

---

## Work

### `sdd session <resume|status|pause|close|sync>`

A resumable work context (`.sdd/.session.json`, or per track with `--track`) so
interrupted implementation continues where it stopped. `sync` creates or
refreshes it while the state is IMPLEMENTING and records the Git branch;
`pause --reason planned|emergency|context_switch --context TEXT --task ID` records
why work stopped; `resume` shows it; `close` deletes it once the report exists.

### `sdd scaffold STAGE [PATH] [--track SLUG] [--dry-run]`

For a stage with a **locked** `spec.md`, creates the missing `todo.md` (from the
spec's acceptance criteria) and, with Eval Driven Development on, `evals.md` and
`checklist.md`. Never overwrites.

### `sdd track <claim|check|verify|incorporate>`

Parallel tracks share **one working tree**, so nothing physical keeps two agent
sessions apart. The CLI makes the separation checkable: two stages may live in
different tracks only if they cannot affect each other — not through the files
they edit, the numbers they take from a shared sequence, or the runtime resources
they need exclusively.

- `sdd track claim SLUG --stage ID --path GLOB... [--seq NAME] [--runtime NAME] [--stability-sensitive] [--branch NAME]`
  records the track's footprint in `.sdd/tracks/<slug>/claims.json`.
- `sdd track check [--json]` fails (exit 1) when two active tracks' footprints
  overlap. The fix is to sequence the stages with `Depends on`, not to tolerate it.
- `sdd track verify SLUG [--since REV]` fails when real Git changes (untracked
  files included) fall outside every claim, or inside two. A file that only a
  sibling track claims is that track's work and is ignored.
- `sdd track incorporate SLUG STAGE [--dry-run]` moves a **closed** track stage into
  the canonical queue: under a lock it takes the next free number (disk, section 5
  and the ledger), renames the folder, appends the index row and releases the
  claims. Two sessions can no longer take the same number.

Agents such as Kilo Code create git **worktrees** on their own: each is a full
copy including a stale `.sdd/`. `sdd doctor` reports them; `sdd fix --gitignore`
ignores them; exclude them from your test, lint and type-check globs too.

### `sdd seq next NAME [PATH] [--track SLUG] [--json]`

Reserves the next number of a shared sequence (for example database migrations)
exactly once, in `.sdd/.reservations.json`. Sequences are declared in the
constitution's section 7 as `` `migration` = `db/NNNN_*.sql` ``; `migration`
defaults to `supabase/migrations/NNNN_*.sql` when that folder exists.

### `sdd deps <add|remove|list|graph>`

Records dependencies on other local projects (`--kind requires|provides`,
`--stage`, `--description`); `graph --format mermaid` draws them.

### `sdd impact DECISION [PATH] [--json]`

Lists every `.sdd/` artifact that mentions a locked decision such as `D-013` —
read it before changing the decision.

---

## Document

### `sdd document [PATH] [--resume] [--answers FILE] [--create-stubs] [--dry-run]`

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
`sdd document --answers plan.json --dry-run`, then again without `--dry-run`.
`sdd doctor` keeps the plan honest (missing files, missing headers).

### `sdd manual [--md [FILE]]`

Prints this manual; `--md` writes it to a file. An agent that has never seen the
tool can run it to learn the workflow. `sdd docs` is a deprecated alias, removed in
v5.

---

## Observe

### `sdd dashboard [PATH] [--ui static|interactive|plain] [--set-default]`

A read-only dashboard over the same data as `doctor` and `context`: overview,
constitution section sizes, stages and tracks, EDD, doctor findings with the
command that fixes each, and the session. `static` prints one panel and exits;
`interactive` is a live TUI that needs a real terminal; both need the optional
extras (`pipx install '.[dashboard]'`, or `pip install rich textual`) — `plain`
needs nothing. `rich`/`textual` still work as deprecated aliases for
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
+-- documentation.json   the documentation plan from `sdd document` (yours)
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
inactive `tracks/*/state.md` are **cold**. `sdd context --budget` shows the
numbers; `sdd doctor` flags what makes them grow (an oversized constitution, long
table rows, absolute links, narrative in sections 5 and 6).

---

## Features and language

Recorded in `.sdd/constitution.md` under `Settings`; toggle by editing that block.
`sdd fix --features` then brings the manifest in line, and `sdd doctor` reports a
disagreement (`feature_mismatch`).

- **Language** — every interaction and artifact uses it. The skill instructions
  stay in English by design; your specs, reports and docs come out in your language.
- **Estimation** — off by default. Stage start/end dates are recorded in every
  report regardless, so enabling it later reconstructs past durations.
- **Documentation** — off by default. `sdd document` plans it with you; the
  `sdd-document` skill produces and maintains it.
- **Parallel tracks** — off by default; see `sdd track`.
- **Eval Driven Development** — off by default. `evals.md` is the single source of
  a stage's acceptance criteria (`E-NNN`); items may be `[x]` met, `[-]` not
  applicable, `[!]` evaluated and not met.

---

## Multiple agents on one project

Install several shims; they all point at the same `.sdd/`. The methodology,
artifacts and history are shared — only the trigger differs per agent.

```bash
sdd init --provider claude --provider cursor --provider copilot
```
