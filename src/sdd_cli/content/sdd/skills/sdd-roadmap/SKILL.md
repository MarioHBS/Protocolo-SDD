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
   that comes later), and carry a short slug (`NNN-<slug>`). If the vision says
   **MVP first**, arrange the earliest stages as the minimum MVP and mark the
   "end of MVP" boundary. If **straight to final product**, sequence through to
   the definition of done. Sizing heuristic: if a stage looks like more than ~5
   ideal days, or does not fit into finite acceptance criteria, split it.

   If part of the plan can genuinely proceed in parallel, it is fine to note
   that here as a candidate for `sdd-track` later — but do not open the
   tracks yet; that happens when the user actually wants to start parallel
   work, via `sdd-track`. **Parallel-safe means independent in two ways:**
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

3. **Fill the canonical index (§5 of the constitution).** One row per stage,
   status `pending`. **This is the source of truth.** If a stage must be
   sequenced after two or more parallel tracks — either a **join stage** that
   waits for their result, or a **stability-sensitive stage** that needs the
   shared build/runtime stable (see step 2) — fill that stage's `Depends on`
   column with the track slug(s) it must follow (the tracks themselves are
   opened later via `sdd-track`; declaring the dependency here is what lets
   `sdd-specify`/`sdd-implement` refuse to start it early).

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
- When inserting stages later, **prefer a suffix** (`010-A`) over renumbering;
  update §5 and regenerate the roadmap from it. Record the change in §6.
