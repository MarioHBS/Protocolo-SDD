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

## Step 4 — Agree on the concrete list

Turn the chosen depth into an explicit list of documents: filename, purpose, and
owner stage (which stage produces or updates it). Confirm the list with the user
before writing anything. Record the agreed list in the constitution (a short
"Documentation set" note under §7) so later sessions do not renegotiate it.

If the project uses numbered documents, agree on the numbering and versioning
convention now and record it in §7 — that convention is project-specific and
belongs in the constitution, not in this skill.

## Step 5 — Produce and maintain

- Write the documents in the project language, passing the Markdown lint and
  file-hygiene rules in `README.md`.
- Every document states its version and last-updated date.
- **Documentation follows ground truth.** Never document intended behavior as if
  it were implemented. If a document describes something not yet built, mark it
  explicitly as planned.
- When a stage changes something documented, update the affected documents as
  part of closing that stage, and note it in the stage report.

## Rules

- Documentation is a **subproduct of stages by default**. Only create dedicated
  documentation *stages* in the roadmap when the set is large enough to warrant
  its own planning (typically the comprehensive depth) — and then do it through
  `sdd-roadmap`, not ad hoc.
- Never let documentation work start while the constitution is in `DECIDING`;
  the gate applies to docs that assert architecture too.
