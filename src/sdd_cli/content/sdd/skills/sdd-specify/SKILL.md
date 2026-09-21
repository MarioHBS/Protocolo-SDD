---
name: sdd-specify
description: Produces the technical SPEC and detailed todo for ONE stage under the SDD methodology — the self-contained guide the executor agent will follow to implement. Use WHENEVER .sdd/constitution.md is in state SPECIFYING, when the user asks for "the stage spec", "the technical detail", "what to implement now", or when a roadmap stage must become an implementation plan. This skill also governs CHANGES to already-locked decisions (anti-regression procedure). Trigger before any stage implementation.
---

# Phase SPECIFYING — stage spec and todo

Goal: produce, for the **active stage**, two artifacts in `stages/NNN-<slug>/`:

- `spec.md` — all the already-decided technical detail of the stage;
- `todo.md` — the detailed, actionable task list.

The spec must be **self-contained**: the executor implements from it alone, with
no external context.

Write all artifacts in the language set in
`constitution.md → Settings → Language`.

## Steps

1. **Identify the active stage** in the constitution (`Active stage`).
   **Check §5's `Depends on` column for this stage.** If it lists one or
   more track slugs, this is a **join stage** — confirm via
   `### Active tracks` / `tracks/<slug>/` that every listed track has all
   its stages incorporated into the canonical queue before proceeding.
   **MUST NOT** start specifying a join stage while any listed track is
   still open. If blocked, stop and tell the user which track(s) are still
   pending (or invoke `sdd-track`/`sdd-reconcile` to check current status).

2. **Gather the context and embed it in the spec** (copied/summarized, not just
   referenced):
   - the locked decisions from §3 relevant to this stage;
   - the pertinent parts of the `report.md` of stages this one depends on — what
     already exists, with **real names** (files, contracts, functions). Trust a
     report only to the extent it was verified (see empirical verification); if
     in doubt about a critical claim, confirm it against ground truth now;
   - the logical links: what this stage consumes from others and what it
     delivers to future ones.

3. **Decide what was local to this stage** (deferred during DECIDING) and record
   the choices in the spec itself.

4. **Write the spec** from `templates/spec.template.md`. Set `Status: draft`.

5. **Write the todo** from `templates/todo.template.md`: small, ordered tasks,
   each with a verifiable outcome.

   If **Eval Driven Development** is on, also create `evals.md` and
   `checklist.md`. Assign stable `E-NNN` IDs; an evaluation added later receives
   the next free ID, never a renumbered one. `evals.md` is the source of truth;
   the closing checklist records evidence against those IDs. Read any matching
   entry in `backlog.md`, embed the relevant context in the spec, then remove
   that backlog entry so it cannot be implemented twice.

6. **Empirical verification + cold self-audit.** Before locking, review as if you
   had never seen the project:
   - Could an executor with no other context implement from this spec alone?
   - Are the acceptance criteria objectively verifiable?
   - **Has every assertion about the stack been tested against the real system
     rather than recalled from memory?** (database behavior, migration numbers,
     API contracts, what is actually deployed). Actually verify — do not assume.
   - Does anything here contradict or undo an earlier stage? (see anti-regression)
   - If subagents exist, delegate the audit to one reading the spec cold. If a
     high-risk operation is involved, isolate it in a dedicated subagent.

   Fix until it passes, then set `Status: locked`.

7. **Release implementation.** Only with the spec `locked`: `State: IMPLEMENTING`,
   `Next action: implement the active stage following stages/NNN-<slug>/spec.md`,
   mark the stage "in progress" in §5, update the date.
   Immediately run `sdd session sync` so the resumable work context is created.

## Atomicity — the calibration

Scope should be **the smallest slice that delivers end-to-end verifiable
value**. Signs of bad calibration:

- **Too atomic** (stalls the flow): the task delivers nothing testable on its
  own. → Group it.
- **Too broad** (loses focus): it mixes independent capabilities and touches many
  modules. → Split it. Rule of thumb: if you cannot write finite, clear
  acceptance criteria, it is too broad.

## Anti-regression — changing something already locked

If the stage requires changing a decision in §2/§3, or altering something an
earlier stage delivered, **never do it silently**:

1. Stop and tell the user the impact.
2. In the spec, add the header `Supersedes (partially): <stage/decision>` and
   describe exactly what changes and what remains.
3. Update the decision in the constitution and record it in `CHANGELOG.md`
   (and refresh §6's dated-band index to keep pointing there), listing affected
   stages. If the project uses ADRs (§7), amend the ADR following the project's
   convention — do not invent a format here.
4. Verify that completed stages remain valid; if one broke, register a
   reconciliation stage instead of leaving an inconsistency.

## Rules

- One stage at a time. Never specify the next before closing the current one.
- The spec is the truth of the implementation; the executor should never have to
  guess or ask for extra context.
