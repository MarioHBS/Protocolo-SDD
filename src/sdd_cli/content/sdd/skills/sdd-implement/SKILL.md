---
name: sdd-implement
description: Governs the use of the stage's todo.md as a living guide DURING implementation under the SDD methodology. Use WHENEVER the constitution is in state IMPLEMENTING and the active stage has a todo.md (produced by sdd-specify). This skill governs the DISCIPLINE of the todo — keeping it current, honest about divergence — not the technical method of implementation (language, tests, architecture), which stays outside SDD's scope. Trigger when the executor starts building the active stage from its spec.
---

# Phase IMPLEMENTING — build the active stage, todo.md as your living guide

Goal: turn the locked `spec.md` into a working stage, while keeping the stage's
`todo.md` an accurate, real-time mirror of progress.

> **Scope — this skill governs the `todo.md` habit, not the build.** How you
> implement (language, frameworks, tests, architecture) is outside SDD's scope
> and is not prescribed here. This skill only governs HOW YOU USE the stage's
> `todo.md` during that work.

Write all artifacts in the language set in
`constitution.md → Settings → Language`.

## How to use `todo.md`

- **`todo.md` is your guide.** It is the plan for the stage (produced by
  `sdd-specify`). Follow it as your roadmap during implementation.

- **Granularize internally as much as you like.** Break a task into sub-steps in
  your own working list, think out loud, open micro-tasks — as long as the
  **state of the `todo.md` checkboxes reflects real progress**, not your private
  list.

- **Mark `- [x]` as each task is actually completed (verified), not all at the
  end.** Update the file continuously: a task finished → `todo.md` saved with
  that item as `- [x]`. The file is a living cache, not a once-at-the-end sweep.

- **Diverging is allowed, but honest.** If you did more, less, or different
  than planned: do **not** invent new `- [ ]` lines in `todo.md` to match ad-hoc
  work. Leave the planned item marked according to what actually happened, and
  record the divergence — it goes in `report.md → §7 Divergences from the spec`
  at close, not into blind self-marking of `todo.md`.

- **Your conversation list is not canonical.** The `todo.md` on disk is the
  stage's artifact. When you finish, the canonical proof of "done" remains
  `report.md`; `todo.md` is its mirror.

## Rules

- The executor agent is responsible for the build itself. This skill only
  governs the `todo.md` discipline during the build — keep it current and
  honest so the closing vistoria (skill `sdd-close`, step 4) finds a fully
  checked-off, truthful file rather than a retrofit.
- A stage with its spec locked may proceed straight here from `sdd-specify`. No
  production code in any other state (see the gate in `README.md`).
- **MUST NOT** implement a stage whose §5 `Depends on` column lists a track
  that is not yet fully incorporated (`sdd-specify` should have already
  refused to spec it, but this is a second check — never build against an
  unmet join dependency even if a spec somehow got written prematurely).
