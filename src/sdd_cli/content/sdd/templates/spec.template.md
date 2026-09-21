<!-- STAGE SPEC — produced by sdd-specify.
     MUST be self-contained: the executor implements from this file alone.
     Write the content in the project language (Settings > Language). -->

# Spec — Stage NNN: [slug]

- **Status:** draft   <!-- draft -> locked. Implementation only when "locked". -->
- **Created:** [date]
- **Origin:** escopo-original | lacuna-de-levantamento | mudanca-do-cliente | bug-ou-regressao | divida-tecnica
- **Depends on:** [stages] · **Enables:** [stages]
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

**Frozen-scope gate:** implementation may not add work outside this section;
record an amendment with its Origin instead.

- [...]

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

- [ ] [criterion 1]
- [ ] [criterion 2]

---

## 6. Risks / watch points

- [what could go wrong and how to mitigate; anything touching other stages]
