---
name: sdd-audit
description: Cross-cutting SDD utility — the cold audit of a stage's spec.md and todo.md that must pass before `Status: draft` becomes `Status: locked` (step 6 of sdd-specify). Use it whenever a stage that is not `light` is about to be locked, again after every round of fixes, and when re-locking after an amendment. It hunts for gaps, ambiguities, unverified claims, missing tasks and contradictions, and returns a verdict with ranked findings. It reads and reports; it never edits the spec, locks it or writes code.
---

# Utility — cold audit before locking a spec

The author of a spec cannot see their own assumptions. This audit reads the spec cold, as an
executor who has never seen the project and will implement it literally, and finds every hole that
would make that executor guess, diverge or break an earlier stage — **before** the spec is locked.
After the lock the scope is frozen, and every hole missed becomes a letter-suffix stage or a defect.

Write the report in the language set in `constitution.md → Settings → Language`. The verdict words
(`READY TO LOCK`, `NOT READY TO LOCK`), the severities (`BLOCKER`, `MAJOR`, `MINOR`) and the finding
states (`open`, `fixed`, `dismissed`) stay in English, so `sddkit doctor` can read them.

## When it is required

It follows the stage's **weight** (the `Weight` column of §5; empty or missing means `full`):

- **`light`** — the basic review is enough: the checklist of `sdd-specify` step 6, `sddkit doctor`
  and, inside a track, `sddkit track check`. The audit may be skipped.
- **`full`** — the audit runs until the verdict is `READY TO LOCK`, its rounds are recorded in
  `audit.md` and the spec carries a `Locked-by-audit:` line (see "Record").
- **A trigger forces `full`.** The project lists the paths and kinds of change that always need the
  audit in `.sdd/audit-lenses.md` (see "Project lenses"). Lowering a stage that hit a trigger to
  `light` needs a written reason in the `Weight` cell and the owner's agreement. Raising a stage
  from `light` to `full` is always allowed, and is the right call when the basic review finds a
  BLOCKER.

## Who runs it

- **With subagents** (Claude Code installs `.claude/agents/sdd-audit.md` for this): delegate the
  audit to that agent, so the reader is not the author. Pass it the stage, the path of `audit.md`
  and, from round 2, nothing else: it reads the earlier rounds from the file.
- **Without subagents:** follow this skill yourself, as an adversary of your own spec. Say so in
  the round's header (`Mode: self-audit`): a self-audit is weaker, and the owner should know.

The auditor is **read-only**: it never edits the spec, the todo or the constitution, never locks,
and never runs a command that writes (`sddkit seq next`, `sddkit track claim|incorporate|close`,
`sddkit fix`, `sddkit session`, `sddkit update|migrate`, `git add|commit|push|checkout|reset`,
installs). It does not read `.env*` files and never prints a secret. A claim about a live system it
cannot reach (a database, a deployment, a third-party service) is **handed off** to the person or
agent that can check it, never stated as verified from files alone: files describe intent, the live
system is the truth.

## Procedure

### 1. Load the method and the stage

1. `.sdd/README.md` (principle zero, who rules when artifacts disagree) and
   `.sdd/constitution.md` through `## 1.`, plus `Settings`.
2. The stage folder (`.sdd/stages/NNN-<slug>/`, or `.sdd/tracks/<track>/stages/NNN-<slug>/`):
   `spec.md`, `todo.md`, `evals.md` / `checklist.md` when they exist, and `audit.md` if an earlier
   round exists. Also `templates/spec.template.md`.
3. Every decision the spec cites (§3 of the constitution) and §2 (inviolable principles) in full.
4. The `report.md` of every stage in `Depends on`, and the sections of `backlog.md`,
   `cross-cutting.md` (if present) and the track's `state.md` / `claims.json` that concern the stage.
5. `.sdd/audit-lenses.md`, if the project has one.

### 2. Gate checks (mechanical; any failure is a BLOCKER)

- Template conformance: header fields present (`Status`, `Created`, `Origin`, `Depends on`,
  `Enables`, `Touches`), sections 1 to 6 present and filled, no placeholder left (`TBD`, `TODO`,
  "etc.", "and so on", "where applicable").
- `Depends on` satisfied on disk: each stage has a `report.md`; each listed track has all its stages
  incorporated.
- Footprint: `Touches` is filled; every file the todo tells the executor to create or edit falls
  inside it; every shared sequence is declared; inside a track, `sddkit track check` passes.
- `Supersedes (partially):` is present whenever the stage changes a locked decision or something a
  closed stage delivered (`sddkit impact D-NNN` and a search find the neighbours).

### 3. Verification ledger (against disk, with `path:line`)

For every concrete claim in the spec or todo — a file, function, route, component, type, variable,
table, column, script, test file, dependency and its version, a behaviour of an external service —
test it with search and read, and quote `path:line` as proof. Classify each claim:

- **verified** — found as described;
- **refuted** — missing, renamed or different (a BLOCKER if the executor would build on it);
- **unverifiable here** — say who must verify it and how.

A report is a cache, not truth: if the spec leans on a claim from an earlier `report.md`, check it
on disk anyway.

### 4. Lenses

For each lens, write the concrete question asked and what the spec answers (or fails to). Skip a
lens only if you can say why it cannot apply to this stage.

1. **Traceability.** Goal → included scope → technical detail → acceptance criterion → todo task.
   Orphans in any column are findings.
2. **Verifiability.** Every criterion can be confirmed against the real system by a command, a
   query, a test name or an observable outcome. Flag adjectives ("fast", "robust") and limits
   nobody measured.
3. **Ambiguity and unmade decisions.** "or", "maybe", "should", "preferably", an unnamed contract,
   an unspecified default, order, limit, timeout, unit, locale, rounding, size, pagination,
   idempotency key. If the executor must choose, the spec is incomplete.
4. **Behaviour completeness.** Per flow: happy path, empty, loading, error, partial failure, retry,
   duplicate submission, cancel midway, concurrent use, expired session, stale data, what each role
   sees.
5. **Data and storage.** New or changed structures with types, nullability, defaults, constraints,
   indexes, backfill, rollback, access rules, idempotent migration, order of test → production →
   code, and who applies each step.
6. **Authorization and audit trail.** Who may do what, where the server enforces it (not only the
   UI), which actions leave a record, what happens to a blocked or downgraded user.
7. **Security and privacy.** Validation at every boundary, enumeration and timing leaks, open
   redirects, secrets, personal data in logs, upload limits and types, rate limits, webhook
   signatures, side effects of a local test run (a test can send real e-mail).
8. **Integrations.** The real contract of each external call, failure and timeout handling,
   idempotency, environment differences, cost of side effects.
9. **Interface and cross-cutting.** Every screen state, responsive behaviour, theme, accessibility,
   keyboard, copy and accents in the project language, every item of `cross-cutting.md` turned into
   a criterion or waived in writing.
10. **Tests.** The minimum the constitution demands: which tests, which files, which data, what is
    left to manual checking and when.
11. **Anti-regression and neighbours.** Contradictions with §2/§3, with what closed stages
    delivered, with sibling stages or tracks (shared files, sequences, exclusive runtime
    resources), and with documentation that will become wrong.
12. **Scope calibration.** Too broad (no finite criteria, independent capabilities mixed) or too
    atomic (delivers nothing testable alone). Every "out of scope" item has a home (a backlog row,
    a named future stage), so it is not silently lost.
13. **Todo quality.** Small tasks ordered by real dependency, each with a verifiable outcome;
    prerequisites and final check present; documentation updates included; no task that asks for a
    commit or push; irreversible steps isolated and marked.
14. **Premises that could be false.** List the 3 to 5 assumptions the design stands on and how each
    would be disproved; test the cheap ones now (see "Premises").

### 5. Severity and verdict

- **BLOCKER** — the executor would have to guess, would build on something refuted, would break an
  earlier stage or a locked decision, or the stage would breach its own footprint.
- **MAJOR** — a real gap likely to cost rework. Fix it, or waive it in writing in the spec's §6.
- **MINOR** — wording, hygiene, small clarity gains. Allowed in a `READY TO LOCK` verdict, and listed.

The verdict has **two values only**: `READY TO LOCK` when there is no BLOCKER, every claim the
design depends on is verified or explicitly handed off to a named verifier, and each MAJOR is fixed
or waived in writing; otherwise `NOT READY TO LOCK`. "Ready with reservations" does not exist. In
doubt, do not approve: a false "ready" costs far more than one more round.

## Rounds

- **Round 1 is complete:** gate checks, ledger and all lenses.
- **Later rounds are delta rounds.** Read `audit.md`, confirm each earlier finding by its `id`
  (`resolved`, `partial` or `open`), reread only what the corrections touched, and search the
  whole stage folder, the neighbouring specs and the constitution for every fact that was changed.
  Run a full pass again only if round 1 had BLOCKERs in more than one lens or the spec changed scope.
- **The author's correction rule.** A fact corrected in one place is searched for in the spec, the
  todo, `state.md`, the neighbouring specs and the constitution **before** the next round is
  requested: corrections that leave other mentions behind are the main source of new findings.

## Premises

Every premise that a decision or an accepted risk rests on gets a state: `verified (evidence)`,
`refuted`, or `untested (who, when)`. An accepted risk may not rest on an untested premise. A claim
of absence ("X never reaches the browser") lists the channels searched (public variable, prop of a
client component, serialized HTML, log), not only the usual convention. Measurements that must be
done before implementation, with owner and moment, go in the spec's §6 under "To measure before
implementing".

## Record

The author (not the auditor) writes what the audit returned into `.sdd/stages/NNN-<slug>/audit.md`
(from `templates/audit.template.md`): one `## Round N` section per round, with the date, the mode
(`full`, `delta` or `self-audit`), the verdict, the counts and one table row per finding
(`id`, severity, lens, location, state, pointer). When the verdict is `READY TO LOCK` and the spec is
locked, add to the spec's header:

```text
- **Locked-by-audit:** round 3 · 2026-11-13 · fixed 4/9 · dismissed 0
```

`fixed B/M` counts the BLOCKER and MAJOR findings whose last state is `fixed`; `dismissed` counts the
findings the owner dispensed with, each with its reason in the table. `sddkit doctor` reports a
locked, still-open `full` stage with no such line (`lock_without_audit`, a note; not one already in
`CLOSING` or with every `todo.md` item done) and a line that
disagrees with `audit.md` (`lock_audit_mismatch`, a warning). `sdd-close` copies the numbers into the
stage `report.md`.

## Report format

1. **Verdict** on the first line, with the stage id and slug and the counts of BLOCKER / MAJOR / MINOR.
2. **Findings**, most severe first: id (`F-01`…), severity, lens, location with line numbers, what is
   missing or wrong, the concrete failure scenario, and the smallest fix.
3. **Verification ledger:** claim, evidence (`path:line`) or the name of the verifier, status.
4. **Traceability gaps** (lens 1) and **premises** (lens 14) with how to test each.
5. **Hand-offs:** exactly what the caller must delegate before locking.
6. **From round 2:** which earlier findings are resolved, which are not, and which new ones the
   corrections introduced.

Never soften a finding to be polite and never invent one to look thorough: a finding without a
concrete failure scenario and a location does not belong in the report. If the spec is sound, say so
plainly and show what was checked.

## Project lenses and triggers: `.sdd/audit-lenses.md`

A file the project owns (the kit never creates or edits it). Two optional sections:

```markdown
## Extra lenses
- Payments: the real contract of the payment provider, retries and webhook replay.

## Triggers
- `src/server/auth/**`
- `supabase/migrations/**`
```

"Extra lenses" are added to the list above for this project. Every backticked glob under
"Triggers" marks a path whose change forces the `full` weight: `sddkit doctor` reports a stage
marked `light` whose `Touches` paths match one (`light_hits_audit_trigger`). Describe kinds of
change that are not paths (a decision other stages will inherit, a premise about an external system
not yet measured, a data migration) as plain bullets in the same section: the auditor reads them,
the doctor ignores them.

## After the audit

The author fixes the spec and todo, records the round in `audit.md`, and asks for another round
until the verdict is `READY TO LOCK`. Only then does the author set `Status: locked`, add the
`Locked-by-audit:` line, move the constitution to `IMPLEMENTING` and run `sddkit session sync`. The
auditor does none of those.
