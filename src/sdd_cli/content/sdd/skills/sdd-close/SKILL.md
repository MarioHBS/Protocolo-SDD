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
   Record divergences from the spec and deliberately deferred debt.

4. **Update the canonical index (§5).** Mark the stage `done` **only because
   `report.md` exists on disk**, with pointers to spec and report.

5. **Regenerate `roadmap.md` from §5.** Never hand-edit the roadmap; derive it so
   statuses, slugs and counts match. (Or invoke `sdd-reconcile`.)

6. **Trim `Current state`.** It is a pointer (~5 lines). All closing narrative
   belongs in `report.md` and, if structural, in §6 — **not** in `Current state`.

7. **Point to the next stage.** If stages remain: `State: SPECIFYING`,
   `Active stage: <next one with satisfied dependencies>`, `Next action: load the
   sdd-specify skill`. If none remain: `State: COMPLETE`. Update the date.

8. **(If the Estimation feature is on)** update `estimates.md` with this stage's
   real duration and adjust the remaining ones. Always record the stage's start
   and end dates in the report even when the feature is off — that is what makes
   estimation reconstructible if it is enabled later.

9. **Final check:** run `sdd-reconcile` to confirm `Current state`, §5,
   `roadmap.md` and disk all agree.

10. **(If the Documentation feature is on)** consider whether this stage changed
    anything the documentation set must reflect; if so, invoke `sdd-document`.

## Rules

- The report must suffice as context: whoever specifies the next stage should not
  need to inspect the code to understand what exists.
- Do not start the next stage's specification here — only point to it.
