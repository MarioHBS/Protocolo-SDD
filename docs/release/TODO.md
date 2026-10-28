# TODO — sdd-cli 4.4.0

## Items

- [x] C-01 — `sdd proposals collect [PROJETO...] [--scan RAIZ]` e caixa de entrada
- [x] C-02 — `sdd proposals list` e `show`
- [ ] C-04 — varredura de dado privado (antes do C-03)
- [ ] C-03 — `sdd proposals send --via file|url|issue`
- [ ] C-05 — nota de projeto sem arquivo de propostas no `--scan`

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos por item
- [ ] Verificado só leitura em P1, P2 e P5 (nenhum arquivo dos projetos muda)
- [ ] `CHANGELOG.md` cita C-01 a C-05; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.4.0`, fast-forward `main`, push de branch, tag e `main` (cada push confirmado pelo dono)
