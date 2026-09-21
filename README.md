# sdd-cli

Spec-Driven Development scaffolding for AI coding agents.
Personal tool — stdlib only, no dependencies.

```bash
pipx install .            # from this folder
sdd init                  # inside any project
sdd docs                  # full manual
```

**Per-OS install guides** (`INSTALL.<lang>.md` in this folder, three languages):

- [Português (Brasil)](INSTALL.pt-BR.md) — Windows / macOS / Linux × pipx / uv
- [English](INSTALL.en.md) — Windows / macOS / Linux × pipx / uv
- [Español](INSTALL.es.md) — Windows / macOS / Linux × pipx / uv

Commands: `init`, `providers`, `manual` (`docs` alias), `context`, `doctor`,
`fix`, `update`, `session`, `scaffold`, `deps`, `impact`, `health`, `dashboard`,
`evaluate`, `document`, `track`, `seq`, and `migrate --to v4`.

The CLI is deliberately dumb: it copies the `.sdd/` kit, places a thin shim for
your agent(s), and records a manifest. All reasoning lives in `.sdd/skills/` and
runs inside the agent.

Run `sdd doctor` to audit mojibake issues and stage hygiene (closed stages with
open `todo.md` checkboxes, missing `todo.md` for spec'd stages, and whether
`.sdd/CHANGELOG.md` exists).

- Skill instructions: **English** (reliability across agents).
- Your artifacts: the language chosen at `init` (`Settings > Language`).
- Managed files (replaced on migrate): `.sdd/README.md`, `skills/`, `templates/`, shims.
- Your files (never touched): `constitution.md`, `roadmap.md`, `stages/`.

Run `sdd manual` for everything else.
