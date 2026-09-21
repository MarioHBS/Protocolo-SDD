<!--
  PROJECT CONSTITUTION
  The most important file in .sdd/. It holds (a) settings, (b) the current
  state, (c) locked structural decisions, (d) the CANONICAL stage index and
  (e) this project's decision conventions. Every agent reads it right after
  README.md.

  This file is YOURS: the sdd CLI creates it once and never overwrites it.
  Fields in <...> are filled in when the agent is invoked and the project is
  explained. IDs (stages, D-NNN, Q-NNN) are append-only and immutable.
-->

# Constitution — [PROJECT NAME]

## Settings

<!-- Set by `sdd init`. Edit by hand to toggle features later. -->

- **Language:** {{LANGUAGE}}
  <!-- All interactions and generated artifacts use this language.
       The skill instructions stay in English by design. -->
- **Estimation tracking:** {{ESTIMATION}}
  <!-- When turning this ON later: past stages may have coarse metrics.
       Durations are reconstructed from report dates, so early stages can be
       approximate. Say so explicitly rather than presenting them as exact. -->
- **Documentation:** {{DOCUMENTATION}}
  <!-- When on, the sdd-document skill plans the documentation set together
       with the user, based on the actual project. -->
- **Parallel tracks:** {{TRACKS}}
  <!-- Off by default -- turn on only if you actually want two agent
       sessions working stages of this project at the same time. -->
- **Eval Driven Development:** {{EDD}}
  <!-- When on, locked stages carry evals.md and closing stages record
       checklist.md evidence. -->

---

## Current state

<!-- HARD CAP: ~5 lines for the top-level pointer. This field is a POINTER,
     not a diary. All closing narrative goes to the stage's report.md and to
     §6. If parallel tracks are open, list them in "Active tracks" below
     instead of trying to cram more than one active stage into the fields
     above -- each track's own detail lives in tracks/<slug>/state.md. -->

- **State:** INITIALIZING
- **Active stage:** (none)
- **Next action:** load the `sdd-init` skill
- **Last updated:** [date]

> States and flow are in `README.md`. No production code while the state is
> `INITIALIZING` or `DECIDING`. §5 is the canonical index; `roadmap.md` derives
> from it; disk is the truth about what is actually done.

<!-- Only present once `sdd-track` has opened at least one track. Append a
     row here when a track opens; remove a row only when that track's fork is
     merged via `sdd-reconcile` (never mid-flight). One row per track --
     append-only, never rewrite an existing row in place. -->

### Active tracks

<!-- Example (delete once you actually open a track):
| Track   | Branched from | State         | Pointer                  |
|---------|---------------|---------------|---------------------------|
| login   | 010           | IMPLEMENTING  | `tracks/login/state.md`   |
| billing | 010           | SPECIFYING    | `tracks/billing/state.md` |
-->

| Track | Branched from | State | Pointer |
|-------|---------------|-------|---------|

---

## 1. Project vision

- **What it is:** [one to three sentences]
- **Who it is for:** [users / audience]
- **Definition of done:** [what must be true for the project to be complete]
- **Delivery mode:** ( ) MVP first, then evolve  ( ) straight to final product

---

## 2. Inviolable principles

> Rules that hold across every stage and that the executor may never violate.

- **Stack / language:** [...]
- **Architecture patterns:** [...]
- **Code and naming conventions:** [...]
- **Data model — general rules:** [...]
- **Authentication / authorization:** [...]
- **Error handling and logging:** [...]
- **Testing — minimum policy:** [...]
- **External constraints (budget, deadlines, compliance, locale):** [...]

---

## 3. Locked structural decisions

> Decisions whose change would undo work across several stages. Must be settled
> before leaving DECIDING (or cited during bootstrap). Rows are **append-only**;
> display in ascending ID order. Changing one requires the anti-regression
> procedure (see `sdd-specify`) and an entry in `CHANGELOG.md` (refresh §6's
> dated-band index to keep pointing there).

| ID    | Decision                     | Choice | Rationale | Locked on |
|-------|------------------------------|--------|-----------|-----------|
| D-001 | [e.g. database]              | [...]  | [...]     | [date]    |

---

## 4. Open questions

> What is still undecided. Mark whether it blocks the gate. Only **structural**
> questions block; local/business questions are recorded so they are not lost.
> Append-only; display in ascending ID order.

| ID    | Question                     | Blocks the gate? | Status |
|-------|------------------------------|------------------|--------|
| Q-001 | <...>                        | yes / no         | open   |

---

## 5. Stage index (CANONICAL)

> Keep every table row under 200 bytes. Stage paths are conventional:
> `stages/NNN-slug/spec.md` and `stages/NNN-slug/report.md`; never use absolute
> `file:///` links here. Track-incorporation narrative belongs in `CHANGELOG.md`.
>
> This is the source of truth for progress. `roadmap.md` is generated from here.
> A stage is `done` only if `stages/NNN-<slug>/report.md` exists on disk. Only
> a stage that is active, already worked, or urgently inserted carries a
> canonical `NNN` here — everything else still ahead in the queue lives in the
> **Provisional queue** below, unnumbered, until its turn to be specified
> arrives (normally at `sdd-close` step 9, or sooner if deliberately
> fast-tracked). Promoting a provisional stage means assigning it the next
> free `NNN` and moving its row up here — never a renumbering, since it never
> had a canonical ID before. This is the same promotion pattern parallel
> tracks already use to incorporate a track's stages (see `sdd-track`): both
> draw from the **same shared "next free NNN" pool**, consumed strictly in
> the order stages actually finish, never in the order they were planned. If
> several tracks and a provisional stage are all in flight at once, there is
> no way to know in advance whose stage closes first — so the Provisional
> queue's row order is planning intent for the sequential/solo stretch only,
> not a numbering guarantee.
>
> Prefer a suffix (`010-A`) over renumbering when a stage must still be
> inserted **among already-canonical stages** — that suffix means "inserted
> fix/extra stage without renumbering the queue". Reserve it for: (a) an
> urgent stage needed right at/after one already `in progress`; (b) a late
> adjustment needed right before a stage that already turned canonical, once
> new information surfaces after its promotion. Any other future insertion —
> advancing an independent stage, or adding one ahead of a stage that is
> still provisional — belongs in the Provisional queue instead, where
> reordering costs nothing. The suffix is unrelated to parallel tracks (see
> `sdd-track`), which live in their own `tracks/<slug>/stages/` subtree with
> independent local numbering until incorporated here. Maintained by
> `sdd-roadmap`, `sdd-close`, `sdd-track` and `sdd-reconcile`.
>
> **"Depends on"** is empty by default (today's purely sequential behavior).
> Fill it with one or more track slugs to sequence this stage **after** those
> tracks, for either reason: it **needs their result** (a classic join stage),
> or it is **stability-sensitive** — accepted by running the app (manual/
> on-device QA, a release build, e2e, benchmarking) and so cannot run while a
> listed track keeps the shared build/runtime unstable. Tracks isolate the
> `.sdd/` index, not the shared build/runtime/device, so a stability-sensitive
> stage is sequenced here rather than opened as a parallel track sibling.
> Declared by `sdd-roadmap` when the fork/join shape is planned, checked by
> `sdd-track` when incorporating a track's last stage, and enforced as a
> MUST-NOT-start rule by `sdd-specify`/`sdd-implement`.

| Stage | Slug   | Status                       | Depends on |
|-------|--------|------------------------------|------------|
| 001   | [slug] | pending / in progress / done | —          |

<!-- With Eval Driven Development, add a `Milestone` column and keep each milestone's
     stages contiguous. There are no Spec/Report columns: the paths are conventional. -->

### Provisional queue (not yet numbered)

> Future stages the roadmap already knows about but has not reached yet.
> Listed by slug only, in intended order — freely reorderable, insertable and
> removable, since none of these rows carry a canonical ID yet. A row is a
> plain future stage, or a **track candidate** (`Notes: track candidate`) —
> work planned to become a parallel track later. A plain row leaves this
> table only by **promotion** into the canonical table above, with the next
> free `NNN`. A track-candidate row leaves this table when the track is
> actually opened via `sdd-track`, moving to `## Current state → ### Active
> tracks` instead — it never gets a canonical `NNN` directly; its own stages
> do, one at a time, as `sdd-track` incorporates each.

| Slug   | Status  | Depends on | Notes |
|--------|---------|------------|-------|
| [slug] | pending | —          | —     |

---

## 6. Structural change history

> A dated-band INDEX pointing at `CHANGELOG.md`, which holds the long-form
> narrative. One row per band of changes (a stretch of structural edits over a
> few days/weeks), not one row per edit. Append a row only when a new band ends;
> the detailed entries already live in `CHANGELOG.md`. Never paste the narrative
> here — that lives in `CHANGELOG.md`, never in `Current state`.

| Entries            | Period       | Theme   | Link            |
|--------------------|--------------|---------|-----------------|
| [YYYY-MM-DD]–[…]   | [date range] | [theme] | `CHANGELOG.md`  |

---

## 7. Project decision conventions

> Where THIS project's specific conventions live, so the generic skills can
> reference them abstractly. Fill in as needed; write "not applicable" if unused.

- **Decision records (ADRs):** [where they live, format — e.g. "ADRs in DOC-007;
  amendments as 'Amendment N — ADR-XXX'". If unused, "not applicable".]
- **Migration / artifact versioning:** [convention — e.g. "migrations numbered
  NNNN, versioned, never loose SQL"]
- **Sequences:** none
  <!-- Numbers that parallel tracks share and `sdd seq next` hands out, declared as
       `name` = `dir/NNNN_*.ext` — e.g. `migration` = `db/migrations/NNNN_*.sql`. -->
- **Validation environment:** [where stages are validated before closing]
