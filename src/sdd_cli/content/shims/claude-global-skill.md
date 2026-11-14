---
name: sdd
description: >
  Use ONLY when the user invokes /sdd or mentions SDD, especificação,
  constitution, roadmap, etapa, estado da maquina de estados, or when the
  project's AGENTS.md or .sdd/ directory is referenced. This skill loads
  the Specification-Driven Development workflow that governs this project:
  reads .sdd/README.md, .sdd/constitution.md (current state), and the
  matching skill from .sdd/skills/.
---
<!-- sddkit-shim: v4.8.0 -->

# SDD — Spec-Driven Development

This project uses **Spec-Driven Development (SDD)**. The whole methodology is
IDE-agnostic and lives in `.sdd/`. Where this skill and the project's
`.sdd/README.md` disagree, the project's README wins: it is the copy the project
actually installed.

## Mandatory flow

When activated, do this in order:

1. Run `sddkit context`. `sddkit` is a Python binary already on PATH: never use
   `npx` or `npm` for it (the npm package named `sdd` is unrelated code), and if
   it is not found, check `where sddkit` / `which sddkit` before assuming it is
   missing. The command prints only Settings and Current state plus the active
   stage's files. If it is unavailable, read only `Settings` and `Current state`
   in `.sdd/constitution.md` (through `## 1.`), not the whole file.
2. Note `Settings > Language` and `Current state` (State, Active stage, Next
   action). Read `.sdd/README.md` only when you need the methodology details
   (first activation in a session, or when a state skill points to it).
3. Load and follow the skill matching the current state, from `.sdd/skills/`:

   | State          | Skill                                      |
   |----------------|--------------------------------------------|
   | INITIALIZING   | `.sdd/skills/sdd-init/SKILL.md`            |
   | DECIDING       | `.sdd/skills/sdd-decide/SKILL.md`          |
   | ROADMAP        | `.sdd/skills/sdd-roadmap/SKILL.md`         |
   | SPECIFYING     | `.sdd/skills/sdd-specify/SKILL.md`         |
   | IMPLEMENTING   | `.sdd/skills/sdd-implement/SKILL.md`       |
   | CLOSING        | `.sdd/skills/sdd-close/SKILL.md`           |

   Cross-cutting utilities (valid in any state): `sdd-reconcile` (realign the
   indexes with disk), `sdd-document` (only when the Documentation feature is
   on), `sdd-track` (only when `Parallel tracks: on`), `sdd-discover`
   (re-check the project's scope) and `sdd-audit` (cold audit of a spec before
   it is locked).

## Inviolable rule (the gate)

**No production code while the state is `INITIALIZING` or `DECIDING`.** The gate
opens when every structural decision is recorded and locked in
`constitution.md §3`.

## Principle zero — ground truth wins

Disk and live services are the truth; indexes (`constitution.md §5`,
`roadmap.md`) and reports are caches. Never claim "done" without verifying
against ground truth. When an index disagrees with disk, disk wins — run
`sdd-reconcile` to realign.

If the working directory is a linked git worktree (`.git` is a file, not a
folder), `.sdd/` there is a stale copy: stop and continue from the main checkout.

Language: skill instructions are in English, but talk to the user and write every
artifact in the language set in `Settings > Language`.
