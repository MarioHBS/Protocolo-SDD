# Contributing

Thanks for looking. This is a small tool with one maintainer; the most useful contribution is
a **concrete report of friction** found while using it.

## Reporting a problem

Open an issue with:

1. what you ran (command, kit version from `sdd --version`, OS);
2. what you expected and what happened (paste the output);
3. the smallest project state that reproduces it, if you can (a constitution excerpt, a stage
   folder layout). Please remove anything private.

Projects that use the kit keep a running list of this in `.sdd/improvement-proposals.md`
(entries `IP-NNN`: episode, evidence, probable fix). If you have one, linking or pasting an
entry is the best possible report.

## Proposing a change

- Open an issue first for anything larger than a fix.
- Keep changes small and on one theme; commits granular, one per topic.
- Run the checks before you push:

  ```bash
  python -m pytest -q
  ruff check src tests
  ```

- Update `CHANGELOG.md` under the version you are working on.

## How branches work

Each release has its own branch and `main` shows the latest one. Release notes and plans for a
version live in `docs/release/` **on that version's branch only**. Details and the step-by-step
for opening the next version are in [docs/branching.md](docs/branching.md). Planned versions are
described on the `roadmap` branch.

## Language

Skill instructions and code are in English. Project notes may be in Portuguese.
