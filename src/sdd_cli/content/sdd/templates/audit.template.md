<!-- STAGE AUDIT — written by the spec's author from what the sdd-audit auditor returned.
     One `## Round N` section per round, newest last. Required for a `full` stage; a `light`
     stage may skip it. Keep the severity words (BLOCKER/MAJOR/MINOR), the verdict words and the
     states (open/fixed/dismissed) in English: `sddkit doctor` reads them. Write everything else
     in the project language (Settings > Language). -->

# Audit — Stage NNN: [slug]

## Round 1 — [date]

- **Mode:** full <!-- full | delta | self-audit -->
- **Verdict:** NOT READY TO LOCK <!-- READY TO LOCK | NOT READY TO LOCK -->
- **Counts:** BLOCKER 0 · MAJOR 0 · MINOR 0

| Id | Severity | Lens | Where | State | Pointer |
|----|----------|------|-------|-------|---------|
| F-01 | BLOCKER | 3 | spec.md §4 | open | [what is wrong, in one line, and where the fix landed] |

> `State` is `open`, `fixed` or `dismissed`. A dismissed finding needs the owner's reason in
> `Pointer`. A finding keeps its id across rounds; its last row decides its state.

## Premises

| Premise | State | Evidence or owner |
|---------|-------|-------------------|
| [what the design stands on] | untested <!-- verified (evidence) / refuted / untested (who, when) --> | [`path:line`, or who will test it and when] |

<!-- After the last round, when the verdict is READY TO LOCK and the spec is locked, add this line
     to the spec's header (counts of the findings whose last state is fixed/dismissed):
     - **Locked-by-audit:** round N · YYYY-MM-DD · fixed B/M · dismissed D -->
