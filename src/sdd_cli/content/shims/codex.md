---
name: sdd
description: Drive this project through the SDD methodology defined in .sdd/. Use whenever planning, specifying, implementing or closing a stage of this project.
---

This project uses Spec-Driven Development (SDD). The whole methodology is
IDE-agnostic and lives in `.sdd/`.

Do this, in order:

1. Read `.sdd/README.md` (methodology, ground-truth principle, state machine).
2. Run `sdd context` when available; otherwise read only `Settings` and `Current state` in `.sdd/constitution.md` (through `## 1.`).
3. Load and follow the skill matching the current state, from `.sdd/skills/`:
   - INITIALIZING -> `sdd-init`
   - DECIDING     -> `sdd-decide`
   - ROADMAP      -> `sdd-roadmap`
   - SPECIFYING   -> `sdd-specify`
   - IMPLEMENTING  -> (executor agent builds; load `sdd-close` when the stage is done)
   - CLOSING      -> `sdd-close`

Cross-cutting utilities, valid in any state: `sdd-reconcile` (realign the
indexes with disk) and `sdd-document` (only when the Documentation feature is
on).
Load `sdd-track` only when `Parallel tracks: on`; cold files stay unread unless needed.
If the working directory is a linked git worktree (`.git` is a file, not a folder), `.sdd/` here is a stale copy: stop and continue from the main checkout.

Inviolable rule: **no production code while the state is INITIALIZING or
DECIDING.** Disk and live services are the truth; indexes and reports are caches.

Language: skill instructions are in English, but you must talk to the user and
write every artifact in the language set in `Settings > Language`.
