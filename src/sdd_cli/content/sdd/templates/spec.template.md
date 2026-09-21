<!-- STAGE SPEC — produced by sdd-specify.
     MUST be self-contained: the executor implements from this file alone.
     Write the content in the project language (Settings > Language). -->

# Spec — Stage NNN: [slug]

- **Status:** draft   <!-- draft -> locked. Implementation only when "locked". -->
- **Created:** [date]
- **Origin:** escopo-original | lacuna-de-levantamento | mudanca-do-cliente | bug-ou-regressao | divida-tecnica
- **Depends on:** [stages] · **Enables:** [stages]
- **Touches:** <!-- declared footprint; REQUIRED when this stage lives in a parallel track. -->
  - paths: [globs relative to the project root, e.g. `src/billing/**`]
  - sequences: [shared numeric sequences this stage consumes, e.g. `migration`]
  - runtime: [exclusive resources, e.g. `dev-server`, `db-write`, `device`]
  - stability-sensitive: no   <!-- yes = accepted by running the app; cannot overlap a mutating track -->
<!-- Use the line below only if this stage alters something already delivered: -->
<!-- - **Supersedes (partially):** [stage/decision] — what changes, what remains -->

---

## 1. Embedded context

> Everything the executor needs without opening another file.

**Relevant locked decisions:**

- [D-00X: choice — why it matters here]

**What already exists (from stages this one depends on):**

- [real files/modules/contracts created earlier, by name]

**Logical links:**

- Consumes from other stages: [...]
- Delivers to future stages: [...]

---

## 2. Stage goal

[What this stage does, in 1–3 sentences.]

---

## 3. Scope

**Included:**

- [...]

**Frozen-scope gate:** once the spec is `locked`, implementation may not add work
outside this section. Anything new becomes a new stage, or a recorded amendment
with its own `Origin` — never a silent expansion.

**Explicitly out of scope (do not do in this stage):**

- [...]

---

## 4. Technical detail (already decided)

> The "how", unambiguously. Data models, contracts, components, flows, rules,
> error states. Every assertion about the stack has been verified empirically,
> not recalled from memory.

- [...]

**Contracts / interfaces:**

- [signatures, formats, routes, events — concrete]

---

## 5. Acceptance criteria

> Objective and verifiable. Each must be confirmable against the real system at
> closing time. If you cannot write finite, clear criteria, the stage is too
> broad — split it.
>
> **If Eval Driven Development is on, write the criteria once, in `evals.md`, and
> replace the list below with the single line `See evals.md.`** Repeating them
> here lets the two lists drift apart.

- [ ] [criterion 1]
- [ ] [criterion 2]

---

## 6. Risks / watch points

- [what could go wrong and how to mitigate; anything touching other stages]
