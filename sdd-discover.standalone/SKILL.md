---
name: sdd-discover
description: Conduct pre-project discovery for SDD (Specification-Driven Development) and produce the reviewed discovery.md plus a valid discovery.json (contract sdd-discovery/v1) that `sdd init --discovery` imports. Use before a repository exists, or to re-check the scope of an existing project, in any AI chat, with no project files and no CLI access.
---

# SDD discovery (standalone)

You are running outside any project repository, possibly in a plain chat with no
file access and no terminal. Your job: turn an uncertain idea into a reviewable
project brief (`discovery.md`) and a deterministic import file
(`discovery.json`) that the owner later feeds to `sdd init PATH --discovery discovery.json`.

Work in the owner's language (ask which one in the first message if unclear).
Never invent answers: record uncertainty as an open question or a provisional
backlog item.

## Rules

- You cannot run the `sdd` CLI. Validate the JSON yourself with the checklist at
  the end, and tell the owner they can double-check with
  `sdd discover --check discovery.json`.
- If you cannot write files, deliver both files as two separate fenced code
  blocks (`markdown` and `json`), each preceded by its file name, so they can be
  copied verbatim. If you can write files, write them where the owner chooses.
- Interview progressively: a few questions per turn, summarize what you
  understood, ask for corrections. Do not dump the whole questionnaire at once.
- Do not produce the final files until the owner has reviewed the draft
  `discovery.md` in the conversation and approved it.

## Step 1 — Explain the installation choices first

The owner will have to decide these when the kit is installed (`sdd init`) and may
not know they exist. Before the interview, explain each one in plain language,
give your recommendation for *this* project with the reason, and record the
owner's answer (or "undecided"). All can be turned on later by editing the
constitution's Settings, so "undecided" is safe.

| Choice | What it means | Turn it on when | Cost of turning it on |
| --- | --- | --- | --- |
| `estimation` | The kit keeps `estimates.md`: a living schedule/effort estimate, updated every time a stage closes. | The owner or client needs a forecast, a deadline or a budget conversation. | One more file to keep true; early numbers are rough. |
| `tracks` | Two or more agent sessions work different stages at the same time, each in its own track with a declared file footprint. | You really will run parallel sessions, and stages can be kept disjoint. | Footprint declarations, overlap checks and a merge step per track. Off by default. |
| `documentation` | `sdd-document` plans a documentation set (README, architecture, manuals...) with the owner, and stages refresh it on close. | The project has readers beyond the developers: clients, auditors, new hires. | Documents someone must maintain; a stale document is worse than none. |
| `edd` | Eval Driven Development: each stage has an `evals.md` of testable criteria (`E-NNN`) and closes with evidence in `checklist.md`. | Correctness matters and "done" must be provable; regulated or high-cost-of-error areas. | Writing criteria up front; more ceremony on small projects. |

Rules for recording the answers:

- Boolean answers go into `features` in `discovery.json`. A feature left
  undecided is `false` and is also listed as an open question.
- Record every answer (including "undecided") in a `## Installation choices`
  section of `discovery.md`.

Also ask and record in that same section. These are `sdd init` flags, **not**
part of the JSON, except the language:

- **Language** for artifacts and conversation → `project.language` (e.g. `pt-BR`, `en`).
- **AI tools** that will drive the project (`--provider`; list with `sdd providers`;
  one `.sdd/` serves several).
- Preferred **dashboard renderer**: `static`, `interactive`, `plain` or `web`
  (the last is a plain HTML file).

Finish by showing the owner the resulting command, for example:

```
sdd init . --provider claude --language pt-BR --discovery discovery.json
```

## Step 2 — Interview

Establish, in this order of priority:

1. The project: what it is, who it is for, the outcome, what "done" means.
2. Constraints: deadline, budget, stack, compliance, people, integrations.
3. Non-functional requirements the owner actually cares about (accessibility,
   performance, security, availability...). Ask, do not assume: record only what
   the owner states, and also say when none was stated. Later phases (for
   example verification) read these from `discovery.md`; there is no JSON field
   for them, so write them in a `## Non-functional requirements` section and
   carry any that constrain design into `decisions` or the vision.
4. Features and the structural decisions already made (and why), using the
   checklist below.
5. Unresolved questions, and whether each one blocks starting.
6. Delivery slices (stages): small, end-to-end, ordered. For each, its origin,
   a short context, concrete tasks, and the initial file/runtime footprint
   (globs of files it will touch, e.g. `src/search/**`; use `not yet known`
   rather than guessing).
7. Risks and assumptions.

### What counts as structural

A decision is structural if changing it would force rework in more than one
stage. Use these categories as a checklist (adapt to the project). They mirror
the checklist used later by the project's decision gate (the `sdd-decide`
skill). That skill is part of the CLI and only becomes available inside the
project, after `sdd init`; you do not have it now, so apply this list yourself:

- Stack, language, main frameworks/libraries
- Overall architecture (layers, monolith vs services, module boundaries)
- Design system / cross-cutting UI conventions (light/dark theme, component
  library, breakpoints, accessibility baseline), when the project has an interface
- Core data model and its main relationships
- Identity: authentication, authorization, roles/profiles
- Fundamental business rules (pricing, critical flows)
- External integrations with side effects (gateways, third-party APIs)
- Global conventions: naming, error format, logging, i18n
- MVP vs post-MVP boundary
- Non-negotiable constraints: deadline, budget, compliance, hosting

Not structural (leave for the stage spec): names inside an already-chosen data
model, internal function details, jobs and tooling, screen layout and microcopy,
report formatting. Note them and move on.

### Ambiguous points: branch before asking

Do this only for a structural decision with no obvious answer, or for an open
question that blocks the gate (`blocks_gate: "yes"`), never for every question.

- Name 2–3 plausible interpretations or options, each with its trade-off, and
  only then ask the owner to choose.
- For a decision that crosses concerns (a design system touches architecture,
  UX and accessibility at once), give each option from the perspective that
  matters for its category (for example architecture, UX, security) instead of
  one flat pros-and-cons list. The perspectives vary by category; do not use a
  fixed set.
- The owner decides. If they cannot yet, record the question as open.

### External references (bounded)

For a design/UI or architecture decision, before presenting the options, you may
look up how comparable products or systems solved the same problem, if you have
a web search tool.

- At most 2 queries; stop as soon as you have 2–3 concrete references. This is
  not a survey.
- Phrase the query as the generic pattern or problem (for example "light/dark
  theme patterns in a marketplace app"), never with text copied from the
  owner's project: a search provider is a third party and the idea may be
  confidential.
- Cite what you found as input to the options, not as the answer. A search
  result is not authority; the owner's decision is.
- Without a search tool, ask the owner for references they already know, or
  proceed and record the gap as an open question. Never block the interview for
  lack of the tool.
- List the references used in `discovery.md`.

## Step 3 — Draft and review `discovery.md`

Concise human review with these sections: Summary, Interview notes,
Installation choices, Non-functional requirements, Assumptions, Decisions, Open
questions, Stage order, Risks, and External references when any were used.
Present it in the chat and let the owner correct it. Only after approval, emit
the final files.

Mark every item in Decisions as **proposed**: agreed in the interview, but not
yet audited. The project's decision gate (`sdd-decide`) runs a cold
self-audit (is anything a stage depends on still undecided? are the decisions
consistent?) and only then treats them as locked. The interview does not replace
that audit, and the review must not present these decisions as final. In
`discovery.json` the `locked_on` field is simply the date the owner agreed.

## Step 4 — Emit `discovery.json`

UTF-8 JSON. It is the import source and must stay consistent with
`discovery.md`. `schema_version` is the literal string below.

```json
{
  "schema_version": "sdd-discovery/v1",
  "project": {"name": "Example", "language": "pt-BR"},
  "vision": {"what_it_is": "...", "who_it_is_for": "...", "definition_of_done": "..."},
  "features": {"estimation": false, "documentation": false, "tracks": false, "edd": true},
  "decisions": [{"decision": "...", "choice": "...", "rationale": "...", "locked_on": "2026-09-22"}],
  "open_questions": [{"question": "...", "blocks_gate": "yes", "status": "open"}],
  "backlog": [],
  "stages": [
    {
      "slug": "first-slice",
      "title": "First end-to-end slice",
      "origin": "escopo-original",
      "footprints": ["src/**"],
      "context": "...",
      "tasks": ["..."]
    }
  ]
}
```

Semantics the importer applies:

- `stages` must be non-empty. The first item becomes canonical stage
  `001-<slug>` and is the first slice to be worked on; later items form the
  provisional queue, in order.
- `decisions` become rows `D-001…` of the constitution (`locked_on` is an ISO
  date). Depending on the installed CLI version they arrive as locked or as
  proposals awaiting the gate audit; either way treat them as proposed (Step 3).
- `open_questions` become rows `Q-001…`; use `blocks_gate` `"yes"` or `"no"` and
  `status` `"open"` for anything unresolved.
- Every stage is also written to `backlog.md` with its origin, context,
  footprints and tasks. `tasks` (or `backlog`) lists the checklist items.
- `origin` is one of: `escopo-original`, `lacuna-de-levantamento`,
  `mudanca-do-cliente`, `bug-ou-regressao`, `divida-tecnica`. Default
  `escopo-original`. In a fresh discovery nearly everything is `escopo-original`
  or `lacuna-de-levantamento`.
- Slugs are lowercase kebab-case (`[a-z0-9][a-z0-9-]*`) and unique.

## Validation checklist (run it before delivering)

- [ ] Valid JSON: double quotes, no trailing commas, no comments.
- [ ] `schema_version` is exactly `sdd-discovery/v1`.
- [ ] `project.name` and `project.language` are non-empty strings.
- [ ] `vision.what_it_is`, `who_it_is_for`, `definition_of_done` are non-empty strings.
- [ ] `features` is an object of booleans only (omit or `false` for undecided).
- [ ] `stages` is a non-empty list; each has a unique kebab-case `slug`, a
      non-empty `title`, a valid `origin`, and `footprints` (if present) as a list.
- [ ] `decisions`, `open_questions` and `backlog` (if present) are lists.
- [ ] Every stage has `context` or `tasks` (the CLI warns otherwise).
- [ ] JSON and `discovery.md` agree on stages, decisions and open questions.
- [ ] Every decision is labeled proposed in `discovery.md`; every structural
      category above was either decided, recorded as an open question, or
      explicitly out of scope (for example no UI).

## Hand-off to the owner

Tell the owner, in order:

1. Save both files: `discovery.md` (for the team) and `discovery.json` (for the CLI).
2. Optionally validate: `sdd discover --check discovery.json`.
3. Create the project: `sdd init PATH --discovery discovery.json` with the
   provider/language flags decided in Step 1. The CLI shows a second summary
   and asks for confirmation (use `--yes` when there is no terminal) before
   writing anything.
4. Inside the new project, once `sdd init` has run, have the agent load
   `sdd-decide` to audit the proposed decisions before specification starts, if
   the constitution does not already point there.
5. For a project that already exists, compare the plan with what it has,
   read-only: `sdd discover --check discovery.json --against PATH`. The files
   are input for deliberation: the project can restructure its decisions and
   stages from them and does not have to adopt them as they came out.
