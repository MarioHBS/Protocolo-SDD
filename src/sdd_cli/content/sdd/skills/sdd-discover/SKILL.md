---
name: sdd-discover
description: Conduct pre-project discovery for SDD and produce the reviewed discovery.md plus a valid discovery.json import contract. Use before a repository exists or before sdd init --discovery.
---

# SDD discovery

Use this outside a project repository to turn an uncertain idea into a reviewable
project brief and a deterministic input for `sdd init --discovery`.

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
