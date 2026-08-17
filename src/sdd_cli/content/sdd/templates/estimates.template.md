<!-- ESTIMATES TEMPLATE — produced by sdd-roadmap (step 5) when the Estimation
     feature is on, and kept alive by sdd-close (step 10) / sdd-reconcile.
     Write the content in the project language (Settings > Language); keep this
     English skeleton (comments, headings, table headers) as the structure.
     NOT a structural decision or an ADR — a living schedule projection that
     adjusts to real data as the project advances. -->

# Estimates — [PROJECT NAME]

**Document:** Living schedule estimate
**Version:** 1.0
**Date:** [date]

**Status:** Living — updated by `sdd-close` (step 10) when each stage closes.

> **Aviso sobre precisão.** [If the Estimation feature was turned ON after some
> stages had already closed, say so here. Past stages' real durations are
> reconstructed from the dates in their `report.md`, not from continuous
> session start/end tracking. Treat historical durations as approximations,
> not exact measurements. From stage [NNN] onward, tracking is continuous.]

---

## Why this document exists

Projects when the product will be ready, based on the SDD roadmap
(`constitution.md` §5 — canonical index). Not a traditional calendar forecast
(human team, sprints) — for agent-driven work in intense sessions. The real
bottleneck tends to be per-stage complexity and reviewer availability, not
"lines of code per day of capacity."

Every time a stage closes (`sdd-close`), this document is revisited: compare
real vs. estimate, adjust remaining stages if the observed pace diverges, and
update the progress tables.

---

## Methodology

Stages are classified into effort categories (multiplier in **active working
days**, not calendar days):

- **Validation** (test/adapt existing schema): ~1–2 days
- **New implementation** (backend + API from scratch): ~2–4 days
- **Implementation with frontend** (backend + API + UI): ~3–5 days
- **Configuration/ops** (CSP, deploy, CI/CD): ~1–2 days

Bands: **Optimistic / Realistic / Pessimistic**. The **Real** column shows the
observed duration (or the close date when the metric is approximate — see the
precision warning above).

---

## Per-stage projection

> Ordered by the canonical index (constitution §5). Add one row per stage as
> `sdd-roadmap` defines it; fill `Real` when `sdd-close` closes each stage.

### [Block name, e.g. MVP] (NNN–NNN)

| Stage | Nature | Optimistic | Realistic | Pessimistic | Real |
| --- | --- | --- | --- | --- | --- |
| NNN [slug] | [nature] | 1 | 2 | 3 | [closed date / pending / in progress] |

**Subtotal [block]:** N optimistic · N realistic · N pessimistic · N stages.

<!-- Repeat one "### [Block]" sub-table per roadmap block. Subtotals feed the
     per-block and final-conclusion tables below. -->

### Accumulated closed

- **N stages closed** between [first close date] and [last close date] (~N
  calendar days).
- **Estimated sum (realistic):** N working days projected for N stages.

---

## Pending stages

> Estimates not yet finalized. `Real` is filled by `sdd-close`. Stage in
> **progress** is noted; the rest are pending.

| Stage | Nature | Optimistic | Realistic | Pessimistic | Real |
| --- | --- | --- | --- | --- | --- |
| NNN [slug] | [nature] | 1 | 2 | 3 | pending |

**Subtotal pending:** N optimistic · N realistic · N pessimistic · N stages.

---

## Calendar projection ([reference date])

- **Current milestone:** N stages closed; next to **implement** is NNN ([slug]
  [in progress | not started]).
- **Observed cadence:** [N] calendar days for N stages ≈ [N.NN] calendar days
  per stage (running average from stage 001).
- **Projection for the [N] pending stages:** ~N calendar days at the observed
  cadence.

### Final conclusion forecast

> Single explicit point of the expected end-of-roadmap date. **Recalculated at
> every reconcile and every close** (`sdd-close` step 10) from the real observed
> cadence — never fixed. Three bands summing the estimated effort of remaining
> stages over the observed cadence, from today.

**Reference date:** [date] (today) · **Closed:** N · **Remaining:** N ·
**Observed cadence:** ~[N.NN] calendar days per stage.

| Band | Estimated sum (remaining) | ÷ observed cadence | Final conclusion forecast |
| --- | --- | --- | --- |
| **Optimistic** | N working days | ~N calendar days | **[date]** |
| **Realistic** | N working days | ~N calendar days | **[date]** |
| **Pessimistic** | N working days | ~N calendar days | **[date]** |

> **Recommended band:** realistic — **[date]**.

### Per-block forecast

> Same formula as the final conclusion (estimated working days of the block ÷
> observed cadence → calendar days), applied to each block from the reference
> date. Answers "when does mobile / dark theme / the corrections lot finish?"
> without mental summation. Blocks are **chained in roadmap order**; each block
> starts at the (realistic) conclusion date of the previous block, respecting
> dependencies in §5.

| Block | Stages | Optimistic | Realistic (recommended) | Pessimistic |
| --- | --- | --- | --- | --- |
| [block-1] | NNN–NNN | [date] | [date] | [date] |
| [block-2] | NNN–NNN | [date] | [date] | [date] |

> **Method notes.** (1) The **Realistic** column is chained: each block starts
> at the previous block's realistic end. So the last block's realistic date
> matches the final conclusion's realistic date — same date, seen per block.
> (2) Optimistic/Pessimistic are likewise chained within their own band.
> Differences of ±1 day against the final-conclusion table are rounding from
> dividing by the per-stage cadence; the final-conclusion table stays the
> canonical source for "when does everything finish."

### Intermediate milestones

| Milestone | Forecast date | Real date |
| --- | --- | --- |
| [milestone — stages NNN–NNN] | — | [closed date] |
| [milestone — stages NNN–NNN] | [forecast] | projected |
| **Final roadmap conclusion (NNN–NNN)** | **[otim. / real. / pessim.]** | projected |

> Past milestones show — in **Forecast date** and the close date in **Real
> date**. Future milestones show the projected date in **Forecast date** and
> "projected" in **Real date**; as each closes, the date migrates from
> forecast to real.

---

## Where the greatest uncertainty was

- [Stage NNN: why it was the riskiest, and the outcome — whether it diverged
  from the bands or not.]

---

## Update log

| Date | Event | Adjustment |
| --- | --- | --- |
| [date] | Creation of the estimates document, populated with the real history of the closed stages and the estimates for the pending ones. | v1.0 |
