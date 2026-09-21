---
name: sdd-init
description: Starts a project under this repository's SDD (Spec-Driven Development) methodology. Use WHENEVER the user begins a new project, asks for an "SDD plan", hands over a .md file with TODOs or an initial description to turn into a plan, or when .sdd/constitution.md is still in state INITIALIZING. Ingests the initial material, converses to understand the project, and prepares the .sdd/ structure. Trigger even if the user never says "SDD" — any request to "plan/structure this project before coding" belongs here.
---

# Phase INITIALIZING — ingest and bootstrap

Goal: capture the initial context and leave `.sdd/` ready for the decision
phase. **No production code is written here.**

Write all output in the language set in `constitution.md → Settings → Language`.

## Steps

1. **Read the context that already exists.**
   - If the user attached or pointed to a `.md` with TODOs/description, read it
     in full.
   - If the project already has documentation (docs, ADRs, schema, prior specs),
     read what is relevant. Extract everything inferable: goal, audience,
     features, constraints, stack, and **decisions already made**. Do not invent
     what is not there.

2. **Confirm and fill the gaps with the user.** Few questions at a time. The
   minimum before moving on:
   - In one sentence, what is the project and who is it for?
   - What is the definition of done?
   - MVP first, or straight to the final product?
   - Any non-negotiable constraints already known (deadline, budget, stack,
     compliance, locale)?

   Summarize your understanding and ask for confirmation before writing.

   **Adopting the kit on an existing project** (code and Git history already
   there): before the first stage, do a one-time **credentials audit** of the
   working tree and the Git history — committed `.env*` files, private keys,
   service-account files, tokens. Record only **where** (paths, commit ids), never
   the secret values, in chat, logs or artifacts. Feed the result into the
   security decision (`Q-NNN`/`D-NNN`) so an exposed credential is handled before
   any stage builds on top of it.

3. **Bootstrap the structure** (if missing): ensure `.sdd/constitution.md`,
   `.sdd/roadmap.md`, `.sdd/CHANGELOG.md` and `.sdd/stages/` exist. Fill **§1
   Project vision** with what was confirmed. Fill **§7 Project decision
   conventions** if the project already uses ADRs or its own versioning scheme.
   `CHANGELOG.md` is seeded from its template (English skeleton, one
   placeholder entry); the constitution's **§6 is born as an empty dated-band
   index pointing at it** — never a long narrative. The first real entry is
   appended by `sdd-close` when a structural change lands.

4. **Choose the exit path:**
   - **Normal path** — the project has no structural decisions settled yet. Set
     `State: DECIDING`, `Next action: load the sdd-decide skill`.
   - **Bootstrap path** — the project **already arrives with documented
     decisions** (docs/ADRs/schema). You may go straight to `ROADMAP`, **only
     if** you record those decisions as `D-NNN` rows in §3 citing their source.
     The gate is satisfied by citation, not by from-scratch questioning. Record
     this in §6. Jumping to ROADMAP with §3 empty is forbidden.

5. **Update the date** and hand over control, telling the user which path was
   taken and why.

## Rules

- If the user tries to jump to code, remind them of the gate (see `README.md`).
- This kit is generic on purpose: never assume domain, stack or architecture
  without confirmation. Project-specific conventions go into §7 of the
  constitution, never inside the skills.
