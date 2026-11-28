# TODO — sdd-cli 4.10.1

## Items

- [ ] K-08 — `|` escapado em célula (`_cells`, `init --discovery`, achados de `audit.md`)
- [ ] K-09 — `file:///` em código ou sem destino não é aviso
- [ ] K-10 — `accent-loss` ignora código e diz a linha
- [ ] K-11 — fecho do `doctor` conta todos os avisos
- [ ] K-12 — `audit.template.md` passa no MD056
- [ ] K-13 — `Active stage: nenhuma` é nenhuma etapa
- [ ] `RELEASE-NOTES.md` e `CHANGELOG.md`; `USAGE.md` onde o comportamento muda
- [ ] versão em `pyproject.toml` e `content/VERSION`

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; um teste por item
- [ ] `doctor` 4.10.0 × 4.10.1 sobre o MESMO estado real dos projetos: só as diferenças previstas
- [ ] `update --dry-run` nos projetos: nada gravado; `update` real em cópia
- [ ] revisão do material complementar (help, doctor, skills, template, READMEs)
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.10.1`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
