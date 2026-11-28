# TODO — sdd-cli 4.10.1

## Items

- [x] K-08 — `|` escapado em célula (`_cells`, `init --discovery`, achados de `audit.md`)
- [x] K-09 — `file:///` em código ou sem destino não é aviso
- [x] K-10 — `accent-loss` ignora código e diz a linha
- [x] K-11 — fecho do `doctor` conta todos os avisos
- [x] K-12 — `audit.template.md` passa no MD056
- [x] K-13 — `Active stage: nenhuma` é nenhuma etapa
- [x] `RELEASE-NOTES.md` e `CHANGELOG.md`; `USAGE.md` onde o comportamento muda
- [x] versão em `pyproject.toml` e `content/VERSION`

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; um teste por item
- [x] `doctor` 4.10.0 × 4.10.1 sobre o MESMO estado real dos projetos: só as diferenças previstas
- [x] `update --dry-run` nos projetos: nada gravado; `update` real em cópia
- [x] revisão do material complementar (help, doctor, skills, template, READMEs)
- [x] `docs/release/NOTES.md`
- [x] tag `v4.10.1`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
