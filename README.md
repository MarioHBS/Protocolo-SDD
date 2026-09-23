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

For a project that has not been initialized yet, use the reusable `sdd-discover`
skill to produce `discovery.md` for review and `discovery.json` for import, then
run `sdd init PATH --discovery discovery.json`. The CLI validates the versioned
contract and shows the planned bootstrap before it writes; use `--yes` for a
non-interactive import. With EDD enabled, `evals.md` is the authoritative
`E-NNN` criteria list. Existing stages are changed only by the explicit,
previewable `sdd migrate --edd-source-of-truth` command.

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
