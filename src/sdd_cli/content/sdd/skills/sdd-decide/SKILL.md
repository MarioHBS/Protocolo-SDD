---
name: sdd-decide
description: Runs the DECISION phase of the SDD methodology — the "gate" that must be crossed before any implementation. Use WHENEVER .sdd/constitution.md is in state DECIDING, whenever open questions could break future stages, or when the user wants to "settle the decisions"/"define the architecture" before coding. Also governs the short excursion back to DECIDING when a structural decision surfaces mid-flight during IMPLEMENTING. Asks the right questions, locks structural decisions, and only releases the project when nothing that could disrupt future changes remains open.
---

# Phase DECIDING — the gate

Goal: lock **every** structural decision — the ones whose change would undo work
across several stages. **No production code is written here.**

Write all output in the language set in `constitution.md → Settings → Language`.

## What counts as structural (must be decided now)

A decision is structural if changing it would force rework in more than one
stage. Typical categories (adapt to the project):

- Stack, language, main frameworks/libraries
- Overall architecture (layers, monolith vs services, module boundaries)
- Design system / cross-cutting UI conventions (light/dark theme, component
  library, breakpoints, accessibility baseline), when the project has an interface
- Core data model and its main relationships
- Identity: authentication, authorization, roles/profiles
- Fundamental business rules (pricing, critical flows)
- External integrations with side effects (gateways, third-party APIs)
- Global conventions: naming, error format, logging, i18n
- MVP vs post-MVP boundary
- Non-negotiable constraints: deadline, budget, compliance, hosting

## What is NOT structural (decided inside the stage spec)

- Table/column/index names within an already-locked model
- Internal details of a function, as long as the contract does not change
- Jobs, cron, schedules, validation scripts, quality tooling
- Screen layout, microcopy, field order
- Report/documentation formatting

Do not stall the flow debating local matters — note them and move on.

## Steps

1. **Surface the questions.** From §1 and the initial material, list in §4
   everything that must be decided; mark each "blocks the gate? yes/no", using
   the categories above as a checklist.

2. **Ask in small blocks (1–3 at a time).** Offer concrete options with pros and
   cons when it helps — do not hand the user a raw decision with no guidance.
   Record each answer immediately.

   **External references (bounded).** For a design/UI or architecture decision,
   before presenting the perspectives below, you may look up how comparable
   products or systems solved the same problem, if you have a web search tool.

   - At most 2 queries; stop as soon as you have 2–3 concrete references. This
     is not a survey.
   - Phrase the query as the generic pattern or problem (for example
     "light/dark theme patterns in a marketplace app"), never with text copied
     from the owner's project: a search provider is a third party and the idea
     may be confidential.
   - Cite what you found as input to the options, not as the answer. A search
     result is not authority; the owner's decision is.
   - Without a search tool, ask the owner for references they already know, or
     proceed and note the gap in the decision's rationale. Never block the gate
     for lack of the tool.
   - Cite the references used in the rationale of the `D-NNN` row.

   **Branch before asking.** Do this only for a structural decision with no
   obvious answer, never for every question:

   - Name 2–3 perspectives that matter for the decision's category (for example
     architecture, UX, security; they vary by category, do not use a fixed set)
     and give each option from each perspective, instead of one flat
     pros-and-cons list. A design system, for instance, touches architecture,
     UX and accessibility at once.
   - Only then ask the owner to choose. The owner decides; if they cannot yet,
     keep the question open and blocking.

3. **Lock the decisions.** Each settled structural decision becomes a row in §3
   (`D-NNN`, choice, rationale, date) and/or feeds the principles in §2. Move the
   question to resolved. If the project uses ADRs (§7), reference them following
   that convention.

4. **Verify the gate (cold self-audit).** Before releasing, review as if someone
   else were reading from scratch:
   - Is every question marked "blocks the gate" resolved?
   - Are the decisions mutually consistent?
   - Could an executor start any stage without depending on a structural
     decision that does not yet exist?
   - If subagents are available, delegate this audit to one reading the
     constitution cold.

5. **Open the gate.** With no structural item pending: `State: ROADMAP`,
   `Next action: load the sdd-roadmap skill`, update the date, record in §6.
   A project imported from discovery already has its stage index (§5), so it
   skips `ROADMAP`: `State: SPECIFYING`, keep `Active stage`,
   `Next action: load the sdd-specify skill`.

## Project imported from discovery

`sddkit init --discovery` leaves the project in `DECIDING` with the interview's
decisions in §3 marked `proposed (agreed <date>)` in the `Locked on` column: the
owner agreed to them, but nobody has audited them. Do not repeat the interview.

1. Run only step 4 (cold self-audit) over §3 and §4. Check §3 against the
   categories above (for instance, a project with an interface and no design
   system decision has a gap) and check that the decisions are consistent.
2. Ask the owner only about what the audit finds missing or contradictory, and
   about any question in §4 that blocks the gate.
3. When the audit passes, lock every `proposed` row: replace the marker with
   today's date in `Locked on`. Then open the gate (step 5).

## Structural decision mid-flight (short excursion)

If you are in `IMPLEMENTING` and a new structural decision surfaces:

1. **Stop implementing.** Do not improvise the decision inside the code.
2. Take a **short excursion to DECIDING** for that decision only: lock it in §3
   (using the anti-regression procedure from `sdd-specify` if it touches
   something already delivered) and record it in §6 as a mid-flight excursion.
3. Return to `IMPLEMENTING`. No need to restart the whole cycle.

This is a legitimate, expected path — what matters is that the decision ends up
locked and traceable, not that it never happens.

## Rules

- **Never open the gate with a structural item pending**, even under time
  pressure. Explain which decision is missing and why it blocks the rest.
- Locked decisions are immutable from here on; changing them later requires the
  anti-regression procedure.
