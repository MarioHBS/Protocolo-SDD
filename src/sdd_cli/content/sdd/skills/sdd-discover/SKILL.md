---
name: sdd-discover
description: Conduct pre-project discovery for SDD and produce the reviewed discovery.md plus a valid discovery.json import contract. Use before a repository exists or before sdd init --discovery.
---

# SDD discovery

Use this outside a project repository to turn an uncertain idea into a reviewable
project brief and a deterministic input for `sdd init --discovery`.

## Explain the installation choices first

The owner will have to decide these when the kit is installed in the project
(`sdd init`), and may not know they exist. Before the interview, explain each
one in plain language, give your recommendation for *this* project with the
reason, and record the owner's answer (or "undecided") in a `## Installation
choices` section of `discovery.md`. Answers that are booleans go into
`features` in `discovery.json`; a feature left undecided is `false` and is
listed as an open question. All of them can be turned on later by editing the
constitution's Settings, so an "undecided" is safe.

| Choice | What it means | Turn it on when | Cost of turning it on |
| --- | --- | --- | --- |
| `estimation` | The kit keeps `estimates.md`: a living schedule/effort estimate, updated every time a stage closes. | The owner or client needs a forecast, a deadline or a budget conversation. | One more file to keep true; early numbers are rough. |
| `tracks` | Two or more agent sessions work different stages at the same time, each in its own track with a declared file footprint. | You really will run parallel sessions, and stages can be kept disjoint. | Footprint declarations, overlap checks and a merge step per track. Off by default. |
| `documentation` | `sdd-document` plans a documentation set (README, architecture, manuals...) with the owner, and stages refresh it on close. | The project has readers beyond the developers: clients, auditors, new hires. | Documents someone must maintain; a stale document is worse than none. |
| `edd` | Eval Driven Development: each stage has an `evals.md` of testable criteria (`E-NNN`) and closes with evidence in `checklist.md`. | Correctness matters and "done" must be provable; regulated or high-cost-of-error areas. | Writing criteria up front; more ceremony on small projects. |

Also ask, and record in the same section (they are `sdd init` flags, not part of
the JSON): the **language** for artifacts and conversation (`project.language`),
which **AI tools** will drive the project (`--provider`, list with
`sdd providers`; one `.sdd/` serves several) and, for the CLI dashboard, the
preferred renderer (`static`, `interactive`, `plain` or `web`, the last one a
plain HTML file). Show the owner the final command, for example
`sdd init . --provider claude --language pt-BR --discovery discovery.json`.

Interview progressively. Establish the project, audience, outcome, constraints,
features, structural decisions, unresolved questions, delivery slices, each
slice's origin, and initial file/runtime footprints. Do not invent answers:
record uncertainty as an open question or a provisional backlog item.

Deliver both files in the location the user chooses:

- `discovery.md`: concise human review of the interview, assumptions, decisions,
  open questions, stage order and risks.
- `discovery.json`: UTF-8 JSON consumed by the CLI. It is the import source;
  keep it consistent with the Markdown review.

Use this contract (`schema_version` is literal):

```json
{
  "schema_version": "sdd-discovery/v1",
  "project": {"name": "Example", "language": "pt-BR"},
  "vision": {"what_it_is": "...", "who_it_is_for": "...", "definition_of_done": "..."},
  "features": {"estimation": false, "documentation": false, "tracks": false, "edd": true},
  "decisions": [{"decision": "...", "choice": "...", "rationale": "...", "locked_on": "2026-09-22"}],
  "open_questions": [{"question": "...", "blocks_gate": "yes", "status": "open"}],
  "backlog": [],
  "stages": [{"slug": "first-slice", "title": "First end-to-end slice", "origin": "escopo-original", "footprints": ["src/**"], "context": "...", "tasks": ["..."]}]
}
```

`stages` must be non-empty; its first item becomes canonical stage `001` and
active for specification, while later items form the provisional queue.
Allowed `origin` values are `escopo-original`, `lacuna-de-levantamento`,
`mudanca-do-cliente`, `bug-ou-regressao`, and `divida-tecnica`. Stage slugs are
lowercase kebab-case. Ask the user to review `discovery.md` before they run the
import; the CLI will show a second summary and require confirmation (or `--yes`
without a TTY) before writing a project.
