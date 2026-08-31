---
name: sdd-roadmap
description: Produces the high-level stage plan (roadmap) for the project under the SDD methodology — the overall TODO split into stages, without extensive detail. Use WHENEVER .sdd/constitution.md is in state ROADMAP, when the user asks for "the overall plan", "the project stages", "the roadmap" or a "high-level TODO", or right after structural decisions have been locked. Fills the CANONICAL index (§5 of the constitution) and generates roadmap.md derived from it. Also trigger when the user wants to review or reorder stages.
---

# Phase ROADMAP — the overall plan

Goal: turn locked decisions into a sequence of high-level **stages**. No
extensive technical detail here — that belongs to the specification phase.

Write all output in the language set in `constitution.md → Settings → Language`.

## Steps

1. **Re-read** the constitution (vision, principles, locked decisions).

2. **Break the project into stages.** Each stage must deliver an end-to-end
   verifiable slice of value, respect dependencies (never depend on something
   that comes later), and carry a short slug. Only the first stage gets a
   canonical `NNN-<slug>` at this point (step 3) — every other stage is
   planned by slug alone and stays provisional until its turn. If the vision
   says **MVP first**, arrange the earliest stages as the minimum MVP and mark
   the "end of MVP" boundary. If **straight to final product**, sequence
   through to the definition of done. Sizing heuristic: if a stage looks like
   more than ~5 ideal days, or does not fit into finite acceptance criteria,
   split it.

   If part of the plan can genuinely proceed in parallel, note that here as a
   **track candidate** — but do not open the tracks yet; that happens when
   the user actually wants to start parallel work, via `sdd-track`. **Parallel-safe means independent in two ways:**
   no data/order dependency **and** no contention on a shared
   build/runtime/device. A **stability-sensitive stage** — one that is
   accepted by *running the app* (manual/on-device QA, a release build,
   end-to-end testing, benchmarking) — is not parallel-safe against any
   track that mutates shared code at the same time, even when it is
   data-independent: the mutating track keeps the shared build red exactly
   when the stability-sensitive stage needs it green. Plan such a stage as a
   **sequenced** stage instead — after the fork joins back (declare its §5
   `Depends on` with the track slugs it must follow), or after the specific
   stage it validates — never as a parallel sibling of the mutating tracks.

3. **Fill the canonical index and the Provisional queue (§5 of the
   constitution).** Only the first stage — the one about to become `Active
   stage` in step 6 — gets a canonical row (`001`, status `pending`). Every
   other stage goes into the **Provisional queue** table beneath it, by slug
   only, in intended order, status `pending`; a stage noted as a track
   candidate in step 2 gets its row there too, with `Notes: track candidate`,
   representing the whole future track (not its internal stages — those are
   decided only when the track is actually opened, per `sdd-track` step 1).
   **This is the source of truth.** If a stage must be sequenced after two or
   more parallel tracks — either a **join stage** that waits for their
   result, or a **stability-sensitive stage** that needs the shared
   build/runtime stable (see step 2) — fill that stage's `Depends on` column
   (in whichever table it currently sits in) with the track slug(s) it must
   follow (the tracks themselves are opened later via `sdd-track`; declaring
   the dependency here is what lets `sdd-specify`/`sdd-implement` refuse to
   start it early).

4. **Generate `roadmap.md` from §5** (using `templates/roadmap.template.md`).
   The roadmap is a **derivation** of §5 — same statuses, same slugs, same
   counts. It adds only the macro view (goal, dependencies, what each stage
   delivers). Never hand-edit it into disagreement with §5.

5. **(If the Estimation feature is on)** create `estimates.md` from
   `templates/estimates.template.md`, classifying stages by effort into
   blocks that match the roadmap (e.g. MVP, post-MVP, per feature). Fill the
   per-stage projection; the **final conclusion forecast**, **per-block
   forecast** and **intermediate milestones** tables are seeded from the same
   cadence assumption and left for `sdd-close`/`sdd-reconcile` to keep alive.
   Mark it "living" — `sdd-close` (step 10) recalculates both forecast tables.

6. **Transition:** `State: SPECIFYING`, `Active stage: 001-<slug>` (first pending
   stage with satisfied dependencies), `Next action: load the sdd-specify skill`,
   update the date.

7. Present the roadmap and ask the user to validate the ordering before
   specifying the first stage.

## Rules

- Keep the roadmap lean: it is the map, not the manual. Detail lives in specs.
- No circular dependencies. If a cycle appears, regroup.
- Do not pre-assign canonical numbers to the whole plan — only the active
  stage is canonical at roadmap time; the rest stays in the Provisional
  queue until `sdd-close` promotes the next one (or the user asks to
  fast-track a specific provisional stage out of order). Reordering or
  inserting rows in the Provisional queue needs no suffix — just edit the
  table.
- When inserting a stage **among already-canonical stages**, **prefer a
  suffix** (`010-A`) over renumbering; update §5 and regenerate the roadmap
  from it. Record the change in §6.
