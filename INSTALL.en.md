# SDD CLI installation (English)

`SDD` is a **Python** CLI (stdlib only, no dependencies) that scaffolds projects for
the *Specification-Driven Development* workflow. It runs on **Windows**, **macOS** and
**Linux**. It is **not** an npm/npx package — if `npx` gave you `could not determine
executable to run`, it is because this is a Python tool; use `pipx` or `uv` (below).

## Prerequisite

- **Python ≥ 3.12** (`python --version` / `py --version`). Older versions install "successfully" and then
  fail at the first run with a `SyntaxError`.

## Recommended install: `pipx`

`pipx` isolates the CLI in its own environment and puts `sdd` on your PATH.

### Windows (PowerShell)

```powershell
# if you don't have pipx yet:
py -m pip install --user pipx
py -m pipx ensurepath

# install the SDD CLI (from the unpacked package folder):
pipx install .\sdd-cli

# open a NEW terminal (so the PATH reloads) and verify:
sdd --version
```

> If `sdd` is not recognized in an already-open shell, open a **new** terminal window —
> `ensurepath` only takes effect in new sessions. Alternatively:
> `py -m pipx install .\sdd-cli` invokes pipx directly even when the PATH is not set.

### macOS / Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# install from the unpacked folder:
pipx install ./sdd-cli

# open a new terminal and:
sdd --version
```

## Alternative install: `uv`

If you prefer `uv` (faster, by Astral):

```bash
uv tool install ./sdd-cli          # macOS / Linux
uv tool install .\sdd-cli          # Windows (PowerShell)
```

## Verify the install

```bash
sdd --version      # should print the installed sdd version
sdd providers      # lists the supported providers
sdd manual         # prints the full manual (`sdd docs` is a deprecated alias)
sdd manual --md SDD-USAGE.md   # writes the manual to a file
```

## Optional: the dashboard

`sdd dashboard` needs `rich` and/or `textual`, which the base install does not carry.
The kit is installed from its folder, so ask for the extras there:

```bash
pipx install --force './sdd-cli[dashboard]'      # rich + textual (use .\sdd-cli on Windows)
# or only one renderer:  './sdd-cli[dashboard-rich]'  /  './sdd-cli[dashboard-textual]'
# without pipx extras:   pipx inject sdd-cli rich textual
sdd dashboard --ui rich
```

## Common error: `npm error could not determine executable to run`

This happens if you run `npx install ./sdd-cli` or `npm i ./sdd-cli`. The SDD CLI is
**not a Node package** — it is Python. Use `pipx` or `uv` (above). The error is
confusing because both ran in a terminal, but `npx` looks for a `package.json` with a
JavaScript binary that does not exist in this project.

## Next step

Inside a project folder:

```bash
sdd init --provider claude --language pt-BR -y
```

Then open your agent (Claude Code, Cursor, etc.) in the project and trigger `/sdd` (or
your provider's trigger — see `sdd providers`). The agent will read `.sdd/README.md` and
enter the INITIALIZING phase, talking to you in the configured language.

## Migrating a v1 project

```bash
# ALWAYS back up the project first and run a dry-run:
sdd migrate --to v2 --dry-run
sdd migrate --to v2
```

`migrate` detects your provider(s), language and hand-edits; it only replaces the
*managed* files (README, skills, templates, shims) and preserves `constitution.md`,
`roadmap.md` and `stages/`. It then writes `.sdd/.migration-todo.md`: the agent walks you
through the remaining constitution edits, asking you to confirm **one change at a time**.

## Refreshing a v2 project to v3

```bash
sdd migrate --to v3 --dry-run
sdd migrate --to v3
```

A v2 project whose constitution is already canonical (English headings, `## Settings`,
`**State:** <a v2 state>`) produces a minimal `.migration-todo.md` with only the
encoding-normalization and reconcile tasks -- there are no v1 Portuguese headings or
skill names to rename. The flag documents intent (`--to v2` = legacy v1->v2,
`--to v3` = refresh v2->v3); both install the current kit and bump the manifest.
