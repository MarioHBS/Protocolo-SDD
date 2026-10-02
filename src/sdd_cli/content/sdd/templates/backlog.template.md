# Backlog

> User-owned deferred work: the detail of stages still in the Provisional queue
> (constitution §5). A queue row is an **index entry** — 2-3 sentences (what,
> why, dependency) plus a pointer here — while context, findings and tasks live
> in one section per stage, titled with its slug.
>
> - `sdd-roadmap` creates a section together with the queue row.
> - `sdd-specify` reads the section, embeds what still applies in the spec and
>   **removes the section**, so the work cannot be implemented twice.
> - The backlog never holds status or order — that is the queue's job (single
>   index). `sdd doctor` reports a section nobody points at and a queue row that
>   cites a section that does not exist.
> - **Format the doctor actually reads:** the queue row must be a markdown
>   table row with a literal `Slug` column, for example
>   `| my-slug | pending | — | See backlog.md#my-slug |`, and this section's
>   heading must repeat that same slug (`## my-slug`). A bullet list or a bare
>   link in §5 is not parsed, even though it reads fine to a person.

## [slug]

**Context.** [what is known, where it came from, why it matters]

**Tasks.**

- [ ] [task]
