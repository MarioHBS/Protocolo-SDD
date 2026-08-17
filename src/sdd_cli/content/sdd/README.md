# SDD — Spec-Driven Development (v3)

This directory is the **single source of truth** for how this project is planned
and built. It is **IDE-agnostic**: nothing here changes when you switch editors.
Each agent has only a thin shim (in `.claude/`, `.github/prompts/`, `.cursor/`,
etc.) pointing back here.

> **You are an AI agent reading this inside an IDE.** Before doing anything,
> read this file, then `constitution.md`. Its `Current state` field tells you
> which phase the project is in and which skill to load. Never skip phases.

**Language rule:** these instructions are written in English for reliability.
All *interactions with the user* and all *generated artifacts* (constitution,
roadmap, specs, todos, reports, changelog, documentation) must be written in the
language configured in `constitution.md → Settings → Language`. Do not switch
the user's language because these instructions are in English. The structural
skeletons (headings, fixed labels, format markers) of templates stay in English;
only the content (the prose the project writes) follows the configured language.

---

## Principle zero — ground truth wins

The code on disk and the live state of databases/services are the **truth**.
The index files (`constitution.md §5`, `roadmap.md`) and the reports are
**caches** of that truth — and caches drift. Two consequences that apply to
every phase:

1. **Never claim "done" without verifying against ground truth.** A report that
   says "migration X applied" or "function Y deployed" is only valid after
   confirming X and Y actually exist. Optimistic reports poison every later
   stage — this is the costliest failure mode of this method.
2. **When an index disagrees with disk, disk wins.** Run the `sdd-reconcile`
   skill to realign the caches with reality.

Corollary for self-audit: **verify empirically, never from memory.** Assertions
about the stack (database behavior, migration numbers, API contracts, what is
actually deployed) must be tested against the real system before entering a spec
or a report.

---

## The inviolable rule (the gate)

**Implementation may not begin while any open decision could break future
stages.**

While the constitution reads `State: DECIDING`, writing production code,
creating project files, or running migrations is forbidden. Only decisions,
questions and planning artifacts are allowed. The gate opens when every
**structural** decision (one that, if changed later, would undo work across
several stages) is recorded and locked.

Decisions that are purely local to one stage — changeable with no impact
elsewhere — do **not** need to be settled at the gate. They are decided inside
that stage's spec.

Two realities v2 acknowledges explicitly:

- **Bootstrap from existing decisions.** If the project already arrives with
  documented decisions (docs, ADRs, schema), the gate may be satisfied by
  *citing* those decisions as `D-NNN` rows in §3, without a from-scratch round
  of questions. What is never allowed is starting to build with §3 empty.
- **Structural decision mid-flight.** If a new structural decision surfaces
  during implementation, take a **short excursion back to DECIDING** to lock it
  (using the anti-regression procedure), then return to IMPLEMENTING. This is
  legitimate and expected — not a process failure — as long as it is recorded.

---

## State machine

The project is always in exactly one state, recorded in `constitution.md`:

| State          | What happens                                   | Skill              |
|----------------|------------------------------------------------|--------------------|
| `INITIALIZING` | Ingest initial context, bootstrap `.sdd/`      | `sdd-init`         |
| `DECIDING`     | Ask questions, lock structural decisions       | `sdd-decide`       |
| `ROADMAP`      | Produce the high-level stage plan              | `sdd-roadmap`      |
| `SPECIFYING`   | Spec + detailed todo for the active stage      | `sdd-specify`      |
| `IMPLEMENTING` | Build the active stage (todo.md discipline; method itself is outside SDD's scope) | `sdd-implement` |
| `CLOSING`      | Stage report and handoff to the next stage     | `sdd-close`        |

Normal flow plus the two legitimate detours:

```text
INITIALIZING -> DECIDING -> ROADMAP -> +- SPECIFYING -> IMPLEMENTING -> CLOSING -+
      |            ^                   +------------ (repeat per stage) ---------+
      |            |
      +-- (bootstrap: decisions already exist) --> ROADMAP
                   |
     IMPLEMENTING -- (structural decision mid-flight) --> DECIDING -> IMPLEMENTING
```

Three skills are **cross-cutting utilities**, not phases, and may be invoked in
any state:

- `sdd-reconcile` — realign the indexes with disk.
- `sdd-document` — plan and produce project documentation (only when the
  Documentation feature is on; see Settings).
- `sdd-track` — open, govern and merge **parallel tracks**: two or more
  stages worked at the same time by separate agent sessions, without git
  worktrees. See "Parallel tracks" below.

---

## Single index (synchronization rule)

The whole method depends on **one** canonical index:

- **`constitution.md §5` is the canonical index** of stages and their status.
- **`roadmap.md` is derived from §5** — never hand-edited. `sdd-close` and
  `sdd-reconcile` regenerate it from §5.
- **A stage is `done` only if `stages/NNN-<slug>/report.md` exists on disk.**
  No stage is marked done by assertion.

This exists because keeping two hand-maintained indexes makes them diverge (one
marks a stage complete that never closed, or lists different future stages). One
canonical index + one derived view + disk as arbiter eliminates that entire bug
class.

---

## Artifacts

Everything is Markdown, versioned in Git. The artifacts **are the project's
memory**: a spec must carry all the context needed to implement it without
anyone re-explaining what happened before.

```text
.sdd/
+-- README.md            — this file (the methodology)
+-- constitution.md      — settings + state + decisions + CANONICAL index (§5)
+-- roadmap.md           — high-level stage view (DERIVED from §5, never by hand)
+-- CHANGELOG.md         — long-form structural change history (§6 is an index here)
+-- skills/              — one skill per phase + cross-cutting utilities
+-- templates/           — models for spec, todo, roadmap, report, checklist, changelog
+-- stages/
    +-- NNN-<slug>/
        +-- spec.md          — the already-decided technical detail of the stage
        +-- todo.md          — detailed task list for the stage
        +-- report.md        — closing report (becomes context for the next stage)
        +-- checklist.md     — (optional) verification log, one scenario per section
+-- tracks/              — (optional) parallel work; see "Parallel tracks" below
    +-- <slug>/
        +-- state.md          — free-form, owned only by that track's agent session
        +-- stages/NNN-<slug>/  — same shape as a normal stage folder, local numbering
```

Optional management artifacts (created only when the matching feature is on):

- `estimates.md` — living schedule estimate, updated by `sdd-close` with each
  stage's real duration.
- documentation set — shape decided with the user by `sdd-document`.

Stage numbering: `001`, `002`, … **IDs are append-only and immutable** (stages,
`D-NNN`, `Q-NNN`). To insert a stage between existing ones, **prefer a suffix**
(`010-A`) over renumbering — renumbering leaves stale references in specs already
written. Always display tables in ascending ID order.

---

## Parallel tracks

Two or more stages can be worked **at the same time**, by separate agent
sessions, without git worktrees (some projects using this kit are not under
version control at all) — see the `sdd-track` skill for the full protocol.
In short:

- Each track gets its own `tracks/<slug>/` scratch area (own `state.md`, own
  `stages/` with local numbering) that only its own agent session writes to.
- §5 stays the single canonical index — a track's stages are only appended
  there (moved into the shared `stages/` queue) at incorporation, never a
  second permanent index.
- A downstream stage can declare in §5's `Depends on` column that it must
  wait for one or more tracks to finish (a **join stage**) — `sdd-specify`/
  `sdd-implement` refuse to start it early.
- The queue can fork into tracks and join back to sequential as many times
  as the roadmap needs — each fork/join is independent of the others.

---

## Process guarantees

- **Ground truth above all.** Status and "done" claims are verified against
  disk/services, not against what another file says.
- **Single index.** §5 canonical, `roadmap.md` derived, `report.md` on disk as
  proof of completion. `todo.md` is the mirror of a stage's task progress —
  kept current during implementation (skill `sdd-implement`), verified at close.
- **Structural history in one place.** The long-form narrative of structural
  changes lives in `CHANGELOG.md`; the constitution's §6 is only a dated-band
  index pointing there. `CHANGELOG.md` is user-owned: seeded once by `sdd-init`,
  appended by `sdd-close`, never overwritten by a migrate.
- **Self-contained specs.** Each `spec.md` embeds the relevant locked decisions
  and the pertinent parts of earlier reports. The executor needs no outside
  context.
- **Anti-regression.** No stage undoes what another delivered. Changes touching
  locked decisions require `Supersedes (partially):` in the spec, an entry in
  `CHANGELOG.md` (and a refresh of §6's dated-band index), and a check of
  affected stages — never a silent edit.
- **Calibrated atomicity.** A spec is the smallest slice that delivers
  end-to-end verifiable value. Heuristic lives in `skills/sdd-specify/`.
- **`Current state` is a pointer, not a diary.** Hard cap ~5 lines. All closing
  narrative belongs in the stage's `report.md` and, if structural, in
  `CHANGELOG.md` (§6's index points there).

---

## Markdown linting — mandatory rules

Every Markdown file created or modified inside `.sdd/` (and any project docs
folder) must pass the checks below. A file with these violations **is not
ready** — fix it before locking a spec or closing a stage.

| Code  | Rule | Bad example | Fix |
|-------|------|-------------|-----|
| MD001 | Heading increment: h1→h2→h3, never skip a level | `# A` straight to `### C` | Restore the hierarchy |
| MD005 | Consistent indentation for same-level list items | `* item` then a differently indented `* item` | Uniform indentation |
| MD024 | No duplicate headings in one document | two `## Introduction` sections | Rename or merge |
| MD025 | Exactly **one** `# Title` (h1) per document | two `#` in the same file | Use `##` for the rest |
| MD032 | Lists surrounded by blank lines | text glued directly to `* item` | Blank line before and after |
| MD040 | Fenced code blocks declare a language | bare ``` fence | ```json |
| MD060 | Well-formed table pipes, spaces on both sides | `\|Col\|Value\|` | `\| Col \| Value \|` |

These follow the [markdownlint](https://github.com/DavidAnson/markdownlint)
(MD0XX) standard and can be checked with any compatible linter
(`markdownlint-cli`, IDE integration, etc.).

### File hygiene (beyond markdownlint)

| Check | Rule | Why |
|-------|------|-----|
| Encoding | **valid UTF-8**, always | Tools that save as ASCII/latin-1 replace accents with `?` or produce mojibake — silent content loss |
| Line endings | **LF** throughout `.sdd/` | Avoids mixed CRLF+LF files that pollute diffs and hide edits |
| Accents | Correct, consistent spelling in the project language | Never "fix" encoding by stripping accents — normalize to UTF-8 instead |

A `.gitattributes` with `* text=auto eol=lf` is installed by the CLI. A
pre-commit hook running markdownlint plus a UTF-8/LF check over `.sdd/` is
recommended.

---

## Optional adaptations

- **Isolate high-risk operations in a subagent.** If your IDE supports
  subagents, centralize irreversible or sensitive actions (database migrations,
  deploys, external calls with side effects) in a dedicated subagent that
  carries the safety checklist and the locked domain decisions. This prevents
  loose action in the main conversation and keeps the main context clean. IDEs
  without subagents replicate the same checklist manually.
- **Cold-read self-audit via subagent.** Delegating spec/constitution audits to
  a subagent that reads cold catches assumptions the author cannot see.
