<!-- TRACK STATE — owned ONLY by the agent working this track.
     Never edit another track's state.md. Never edit constitution.md or
     roadmap.md from inside a track except at incorporation (see the
     `sdd-track` skill, "closing a stage inside a track"), and even then only
     by appending your own row(s) to §5 — never rewriting the table. This
     file is free-form scratch: the CLI never reads or writes it. -->

# Track [slug] — [one-line track goal]

- **Branched from stage:** [NNN]
- **State:** [one of: SPECIFYING / IMPLEMENTING / CLOSING]
- **Active stage in this track:** [tracks/[slug]/stages/NNN-<slug> or (none yet)]
- **Mutates shared code / build:** [yes / no — does this track leave the shared
  build red while it works? If yes, a sibling track's stability-sensitive stage
  must NOT run in parallel with it; sequence it after this track via §5
  `Depends on` (see the `sdd-track` skill).]
- **Needs build stability:** [yes / no — does any stage here require a stable,
  runnable shared build/runtime/device (manual/on-device QA, release build,
  e2e, benchmarking)? If yes, it should have been sequenced, not opened as a
  parallel sibling of a code-mutating track.]
- **Next action:** [one line]
- **Last updated:** [date]

## Notes

[free-form scratch for this track's agent — context, decisions local to the
track, anything that would otherwise crowd Current state]
