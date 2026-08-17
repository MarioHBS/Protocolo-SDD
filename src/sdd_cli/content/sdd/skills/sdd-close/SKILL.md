---
name: sdd-close
description: Closes a completed stage under the SDD methodology by producing the stage REPORT and preparing context for the next stage. Use WHENEVER a stage finishes implementation, when the user says "the stage is done", "I finished this part", "close the stage", or when the constitution is in IMPLEMENTING and the work has ended. Verifies claims against ground truth, produces report.md, regenerates the roadmap from §5, and points to the next stage. Trigger when concluding any stage before starting the next.
---

# Phase CLOSING — report and handoff

Goal: record what was built, **verified against reality**, and prepare the next
stage's context. The report becomes input context for the next specification —
so it must contain no unverified claims.

Write all artifacts in the language set in
`constitution.md → Settings → Language`.

## Steps

1. **Confirm the acceptance criteria.** Walk §5 of the `spec.md`. Every criterion
   must be met **with evidence** or carry a recorded divergence. If something is
   pending, do not close — return to `IMPLEMENTING`.

2. **Ground-truth verification (mandatory).** For **each** artifact the report
   will claim was created/changed (migrations by number, functions, deploys,
   endpoints, files, jobs), **confirm it actually exists** — on the filesystem
   and/or in the live system (database, service). Use the operations subagent if
   one exists. Nothing may be "assumed done": an unverified claim is a
   divergence, not a conclusion. This step exists because optimistic reports have
   propagated false "done" into later stages.

3. **Write `report.md`** from `templates/report.template.md`, including the
   **Ground-truth verification** section (each claim → how it was confirmed).
   Record divergences from the spec (§7 of the report) and deliberately deferred
   debt (§8).

4. **Verify `todo.md` is fully checked off.** Walk the stage's `todo.md` and
   confirm every task is `- [x]`. The marking should already be current from
   implementation (skill `sdd-implement`), not done here retroactively.
   - If **all** items are `[x]`: proceed.
   - If **any** item is `- [ ]`: do **not** auto-mark it. If the work for that
     item was actually done and just not checked, mark it now and note it. If the
     work is genuinely incomplete, the stage is not ready to close — **suggest
     returning to IMPLEMENTING** (the divergence belongs in `report.md §7` if it
     is a real scope change, not a silent checkbox fix). The canonical proof of
     "done" remains `report.md` on disk; `todo.md` is its mirror.

5. **Update the canonical index (§5).** Mark the stage `done` **only because
   `report.md` exists on disk**, with pointers to spec and report.

6. **Regenerate `roadmap.md` from §5.** Never hand-edit the roadmap; derive it so
   statuses, slugs and counts match. (Or invoke `sdd-reconcile`.)

7. **Trim `Current state`.** It is a pointer (~5 lines). All closing narrative
   belongs in `report.md` and, if structural, in `CHANGELOG.md` (see step 8) —
   **not** in `Current state`.

8. **Append a `CHANGELOG.md` entry (when structural).** If this stage touched a
   locked decision (§2/§3), took a mid-flight excursion back to DECIDING, or
   renumbered/inserted a stage, append one dated entry under `## Entries` (newest
   at the top) in `.sdd/CHANGELOG.md`, format
   `- [YYYY-MM-DD] — [what changed and why] — affected stages: [NNN, ...]`.
   Write the entry text in the **project language**; keep the date format, em
   dashes and `affected stages:` label as the English skeleton. If nothing
   structural changed (a routine close), **skip** — the changelog is not a diary
   of ordinary closes. Then, if a new dated band is warranted, update §6 of the
   constitution so it keeps pointing at `CHANGELOG.md` (§6 is the index, never
   the long history). Never rewrite the changelog's English skeleton.

9. **Point to the next stage.** If stages remain: `State: SPECIFYING`,
   `Active stage: <next one with satisfied dependencies>`, `Next action: load the
   sdd-specify skill`. If none remain: `State: COMPLETE`. Update the date.

10. **(If the Estimation feature is on)** update `estimates.md` with this stage's
    real duration and adjust the remaining ones. Recalculate **both** forecast
    tables in the same pass:
    1. Update **Closed**/**Remaining**/**Reference date** (today).
    2. Recompute the observed cadence = (today − stage 001 close date) ÷ closed
       stages.
    3. For each remaining block: sumRealistic(block) ÷ cadence → calendar days.
    4. Chain blocks in roadmap order (each starts at the previous block's
       realistic end); the last block's realistic date is the final conclusion.
    5. Overwrite the **Final conclusion forecast** and **Per-block forecast**
       tables; migrate any milestone just reached from "projected" to its real
       date in **Intermediate milestones**.
    No future close should leave the forecasts stale — one close, one recalc.
    Always record the stage's start and end dates in the report even when the
    feature is off — that is what makes estimation reconstructible if it is
    enabled later.

11. **Final check:** run `sdd-reconcile` to confirm `Current state`, §5,
    `roadmap.md`, `todo.md` and disk all agree. (Reconcile's todo audit will flag
    any closed stage that still has open checkboxes.)

12. **(If the Documentation feature is on)** consider whether this stage changed
    anything the documentation set must reflect; if so, invoke `sdd-document`.

## Rules

- The report must suffice as context: whoever specifies the next stage should not
  need to inspect the code to understand what exists.
- Do not start the next stage's specification here — only point to it.
