---
name: sdd-reconcile
description: Cross-cutting SDD utility that re-derives the project's real status from DISK and realigns the indexes (Current state, §5 of the constitution, roadmap.md) with reality. Use WHENEVER there is any suspicion that the files disagree with what actually exists, when resuming a project after time away, when the user asks "where are we?"/"is the status right?", or as the final check when closing a stage. This is not a phase — it can be invoked in any state.
---

# Utility — reconcile with ground truth

Goal: ensure the three progress trackers — `Current state`, the canonical index
(§5) and `roadmap.md` — agree with each other **and with disk**. Disk arbitrates.

Write all output in the language set in `constitution.md → Settings → Language`.

## Steps

1. **Derive real status from disk.** List `stages/*/` and classify each stage by
   which files exist:
   - has `report.md` → **done**;
   - has `spec.md` (+ `todo.md`) without `report.md` → **in progress**;
   - otherwise → **pending / not started**.

   Do not trust what the indexes claim — trust what exists.

2. **Compare against the indexes** (`Current state`, §5, `roadmap.md`) and list
   the divergences: a stage marked done without `report.md`; a stage in the index
   with no folder on disk; wrong counts; slugs differing between §5 and the
   roadmap; `Current state` pointing at a stage that already closed.

3. **Fix the caches to match disk:**
   - Adjust §5 (canonical) to the real status.
   - Regenerate `roadmap.md` from §5.
   - Fix `Current state` (and trim it if it has turned into a diary).

4. **Do not invent the future.** For **pending** stages, if §5 and the roadmap
   disagree on count or slugs, **do not choose on your own** — present the
   divergence to the user and ask which list is authoritative before writing.

5. **Quick hygiene sweep** (see README): flag any `.sdd/` file that is not valid
   UTF-8, has mixed line endings, or shows accented characters replaced by `?`.

6. Record the reconciliation in §6 if it changed any status, and report the
   before/after to the user.

## Rule

- Reconciling **fixes caches**; it never rewrites history (§6), decisions (§3) or
  the content of specs and reports. If a report is factually wrong (it claims
  something disk contradicts), that is a finding to raise with the user — do not
  silently edit the report.
