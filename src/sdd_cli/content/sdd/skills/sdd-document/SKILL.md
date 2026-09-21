---
name: sdd-document
description: Plans and produces the project's documentation set under the SDD methodology. Use WHENEVER the Documentation feature is on in the constitution Settings and the user asks to "document the project", "create the docs", "write the technical documentation", or when closing a stage that changed something the docs must reflect. Instead of imposing a fixed template, this skill converses with the user — using real project context — to choose the right documentation depth and the actual list of documents. Do not trigger when the Documentation feature is off.
---

# Utility — documentation

Goal: decide **with the user** what documentation this project actually needs,
then produce and maintain it. There is deliberately no fixed preset: the right
document set depends on the project, and you have the context to advise.

Write all documentation in the language set in
`constitution.md → Settings → Language`.

## Step 1 — Check the feature is on

Read `constitution.md → Settings → Documentation`. If it is `off`, do not
proceed; tell the user it can be enabled by editing that line.

## Step 2 — Read the project before proposing anything

Read the constitution (vision, principles, locked decisions), the roadmap, and
the reports of completed stages. You must understand what the project *is*
before recommending how much documentation it deserves.

## Step 3 — Recommend a depth, then agree on it

Propose one of the depths below **with a reason drawn from the actual project**,
and let the user adjust. Do not present them as rigid tiers — they are anchors.

- **Minimal** — the SDD artifacts (specs, todos, reports) plus a good README.
  Fits solo projects, short-lived tools, prototypes, or anything where the
  specs already carry the knowledge.
- **Medium** — adds a small fixed core: architecture overview, data model,
  API/contract reference, glossary, and decision records (ADRs). Fits projects
  with a real user base, a second developer arriving, or a long life ahead.
- **Comprehensive** — a numbered, versioned corpus (e.g. `DOC-001`…) covering
  architecture, governance, roles/permissions, state machines, domain events,
  security, compliance, operations. Fits regulated domains, financial cores,
  multi-team work, or anything where an auditor may ask "why".

Guidance for the recommendation:

- Weigh **who will read it**: only you? a future collaborator? an auditor?
- Weigh **cost of being wrong**: a financial ledger or a compliance-bound flow
  justifies far more documentation than an internal dashboard.
- **Bias toward less.** Documentation that is not maintained becomes a lie, and
  a lie in the docs is worse than a gap. Recommend the lightest depth that
  actually serves the reader.

## Step 4 — Agree on the concrete plan (`sdd document`)

The plan is recorded by the CLI, not renegotiated every session. `sdd document`
**interviews the user** — depth (with a recommendation drawn from the real
project), audience and cost of error, **where the files live** (a base folder,
optionally a location per document; it may be outside `.sdd/`, and outside the
project folder only after an explicit confirmation), the list of documents
(filename, purpose, owner stage), the numbering/versioning convention, the header
every document carries, which stages must refresh each document, and what to do
with documentation that already exists — and saves the result to
`.sdd/documentation.json`. It also turns the Documentation feature on in both the
constitution and the manifest and leaves a one-line pointer in §7.

- Run `sdd document` in the user's terminal, or ask the user to. An interrupted
  interview resumes with `sdd document --resume`.
- In a session with no terminal, hold the same conversation yourself, write the
  answers as JSON with the shape of `.sdd/documentation.json`, and run
  `sdd document --answers FILE.json --dry-run`, then again without `--dry-run`
  (add `--create-stubs` to create the missing files, which are never overwritten).
- Confirm the plan with the user before saving. To change it later, edit
  `.sdd/documentation.json` or run the interview again.

## Step 5 — Produce and maintain

- Write the documents in the project language, passing the Markdown lint and
  file-hygiene rules in `README.md`.
- Follow the plan in `.sdd/documentation.json`: the paths (wherever they live),
  the header it requires (version, last-updated date, "planned" marker) and the
  numbering. `sdd doctor` reports a planned file that is missing or lacks its
  header.
- **Documentation follows ground truth.** Never document intended behavior as if
  it were implemented. If a document describes something not yet built, mark it
  explicitly as planned.
- When a stage changes something documented, update the affected documents as
  part of closing that stage (`sdd-close` step 12 reads each document's `covers`
  in the plan), and note it in the stage report.

## Rules

- Documentation is a **subproduct of stages by default**. Only create dedicated
  documentation *stages* in the roadmap when the set is large enough to warrant
  its own planning (typically the comprehensive depth) — and then do it through
  `sdd-roadmap`, not ad hoc.
- Never let documentation work start while the constitution is in `DECIDING`;
  the gate applies to docs that assert architecture too.
