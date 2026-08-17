# sdd — usage manual (kit {{VERSION}})

Spec-Driven Development scaffolding for AI coding agents.

`sdd` is a **dumb installer**: it only copies files and records a manifest. All
the reasoning — understanding your project, asking questions, writing specs —
lives in the skills under `.sdd/skills/` and runs inside your AI agent.

---

## Install

```bash
pipx install sdd-cli          # or: uv tool install sdd-cli
sdd --version
```

---

## Commands

### `sdd init [PATH]`

Installs the kit into a project (default: current directory).

| Flag | Meaning |
|------|---------|
| `--provider KEY` | Agent to install a shim for. Repeatable — several agents can share one `.sdd/`. |
| `--language CODE` | Language for interactions and generated artifacts (e.g. `pt-BR`). |
| `--estimation` | Enable schedule estimate tracking. |
| `--docs` | Enable documentation generation. |
| `--force` | Overwrite managed files and shims. |
| `-y`, `--yes` | Non-interactive; accept defaults. |

Run with no flags for an interactive prompt. Examples:

```bash
sdd init                                        # interactive
sdd init --provider claude --language pt-BR -y  # agent-driven, no prompts
sdd init --provider claude --provider cursor    # two agents, one .sdd/
```

`init` is idempotent: it never overwrites `constitution.md`, `roadmap.md` or
`stages/`. Re-running on an initialized project tells you to use `migrate`.

### `sdd providers [--plain]`

Lists supported agents. Available: {{PROVIDERS}}.

`--plain` prints bare keys, one per line — use this when an agent needs to
discover the valid `--provider` value for itself before calling `sdd init`.

### `sdd docs [--md [FILE]]`

Prints this manual. `--md` writes it to a file (default `SDD-USAGE.md`).

An agent that has never seen this tool can run `sdd docs` to learn the workflow
before acting.

### `sdd doctor [PATH]`

Audits the project's `.sdd/` tree in read-only mode. It reports:

- deterministic double-encoding mojibake (v2, ERROR)
- ambiguous accent-loss `?` hints (v1, WARN)
- hygiene issues such as closed stages with open `todo.md` checkboxes, stages
  with `spec.md` but no `todo.md`, and whether `.sdd/CHANGELOG.md` exists

The command exits non-zero when v2 mojibake is present, which makes it suitable
for quick pre-flight checks before a migration.

### `sdd migrate --to v2 [PATH] [--dry-run]`

Upgrades an existing `.sdd/` to a newer kit.

- **Replaces** managed files: `.sdd/README.md`, `.sdd/skills/**`,
  `.sdd/templates/**`, and the provider shims.
- **Never touches** your files: `constitution.md`, `roadmap.md`, `stages/**`.
- Hand-edited managed files are detected via the manifest and backed up as
  `<file>.bak` before replacement.
- `--dry-run` shows what would change without writing.

After migrating, a few constitution edits remain manual (the CLI will list
them) — then run the `sdd-reconcile` skill in your agent.

---

## What gets installed

```text
.sdd/
+-- README.md            the methodology (managed)
+-- constitution.md      settings, state, decisions, canonical index (yours)
+-- roadmap.md           high-level stage view, derived from the index (yours)
+-- skills/              one skill per phase + utilities (managed)
+-- templates/           spec, todo, roadmap, report, checklist (managed)
+-- stages/              your per-stage artifacts (yours)
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
| IMPLEMENTING | (executor) | Builds the stage from the spec |
| CLOSING | `sdd-close` | Verifies against ground truth; writes the report; points to the next stage |

Cross-cutting, any time: `sdd-reconcile` (realign indexes with disk),
`sdd-document` (plan and produce docs — only when that feature is on).

**The gate:** no production code while the state is `INITIALIZING` or
`DECIDING`. Implementation waits until every structural decision — anything
whose later change would undo work across stages — is locked.

**Ground truth:** disk and live services are the truth; the indexes and reports
are caches. Nothing is marked done without verification.

---

## Features and language

Both are recorded in `.sdd/constitution.md` under `Settings`, and can be toggled
by editing that block directly — no command needed.

- **Language** — every interaction and artifact uses it. The skill instructions
  stay in English by design (more reliable instruction-following across agents);
  your specs, reports and docs come out in your language.
- **Estimation** — off by default. Stage start/end dates are recorded in every
  report regardless, so enabling it later reconstructs past durations from those
  dates. Early stages may be approximate; the agent will say so rather than
  present them as exact.
- **Documentation** — off by default. When on, the `sdd-document` skill reads
  your project and recommends a documentation depth, then agrees the concrete
  document list with you before writing anything.

---

## Multiple agents on one project

Install several shims; they all point at the same `.sdd/`. The methodology,
artifacts and history are shared — only the trigger differs per agent.

```bash
sdd init --provider claude --provider cursor --provider copilot
```
