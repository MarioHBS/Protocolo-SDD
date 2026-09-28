# sdd-cli

Scaffolding for **Spec-Driven Development (SDD)** with AI coding agents.

`sdd-cli` installs a small, IDE-agnostic methodology kit into a project (a `.sdd/` folder) and
a thin shim for your agent (Claude Code, Copilot, Cursor, Codex, Gemini CLI and more). The
agent then works through a state machine — decide, roadmap, specify, implement, close — where
the **constitution** and the **stage specs** are the source of truth and the disk is the
ground truth. The CLI itself is deliberately dumb: it copies files, records a manifest and
audits the result. All the reasoning lives in skills that run inside your agent.

[Português (Brasil)](README.pt-BR.md)

## Quick start

Requires **Python 3.12 or newer**. Not an npm package: install it with `pipx` or `uv`.

```bash
pipx install git+https://github.com/MarioHBS/Protocolo-SDD.git   # latest version (main)
# or pin a release:
pipx install git+https://github.com/MarioHBS/Protocolo-SDD.git@v4.2.1

cd your-project
sdd init            # choose language and AI providers
sdd doctor          # audit the result
sdd manual          # full manual
```

Per-OS guides (Windows, macOS, Linux × pipx, uv) are in [docs/install/](docs/install/):
[English](docs/install/INSTALL.en.md) ·
[Português](docs/install/INSTALL.pt-BR.md) ·
[Español](docs/install/INSTALL.es.md).

Optional dashboard dependencies (`rich`, `textual`):
`pipx install "sdd-cli[dashboard] @ git+https://github.com/MarioHBS/Protocolo-SDD.git"`
(or `pipx install ".[dashboard]"` from a clone).

## What it manages, and what it leaves alone

| Managed by the kit (replaced on `update`/`migrate`) | Yours (never overwritten) |
|-----------------------------------------------------|----------------------------|
| `.sdd/README.md`, `.sdd/skills/`, `.sdd/templates/`, provider shims | `.sdd/constitution.md`, `.sdd/roadmap.md`, `.sdd/stages/`, `CHANGELOG.md` |

Edits to managed files are detected through the manifest and backed up before replacement.
Skill instructions are in English (reliability across agents); your artifacts use the
language chosen at `init`.

## Commands

| Purpose | Commands |
|---------|----------|
| Set up | `init`, `discover`, `providers`, `update`, `migrate` |
| Diagnose | `doctor`, `fix`, `health`, `context`, `evaluate` |
| Work | `session`, `scaffold`, `track`, `seq`, `deps`, `impact` |
| Document | `document`, `manual` |
| Observe | `dashboard` |

Run `sdd <command> --help` for details, or `sdd manual` for everything. For a project that
does not exist yet, the `sdd-discover` skill produces a reviewed `discovery.md` plus a
`discovery.json` that `sdd init PATH --discovery discovery.json` imports.

## Versions

Each release has its own branch, and `main` always shows the latest one. Releases are also
tagged (`vX.Y.Z`). See [docs/branching.md](docs/branching.md) for how branches are organized
and [CHANGELOG.md](CHANGELOG.md) for what changed.

| Version | Branch | Tag | Status |
|---------|--------|-----|--------|
| 4.2.1 | [`4.2.1`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.2.1) | `v4.2.1` | **Latest** — `main` |
| 4.2.0 | [`4.2.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.2.0) | `v4.2.0` | Discovery, dashboard `--ui web`, EDD source of truth |
| 4.1.0 | [`4.1.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.1.0) | `v4.1.0` | Session context, verifiable tracks, active documentation |
| 4.0.0 | [`4.0.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.0.0) | `v4.0.0` | Sessions, diagnostics, project intelligence |
| 3.3.0 | [`3.3.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.3.0) | `v3.3.0` | Providers and opt-in parallel tracks |
| 3.2.0 | [`3.2.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.2.0) | `v3.2.0` | Parallel tracks without git worktrees |
| 3.1.0 | [`3.1.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.1.0) | `v3.1.0` | `sdd update` |

The planned next releases are described on the [`roadmap`](https://github.com/MarioHBS/Protocolo-SDD/tree/roadmap)
branch.

## Repository layout

```text
src/sdd_cli/         CLI code; content/ holds the kit that is copied into projects
tests/               pytest suite
docs/                install guides, branching model, and (on version branches) release notes
CHANGELOG.md         what changed in each version
CONTRIBUTING.md      how to report problems and propose changes
```

## Contributing

Friction found while using the kit is the most valuable input. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 Mário Henrique
