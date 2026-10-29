# TODO — sdd-cli 4.7.0

## Items

- [x] W-01 — coluna opcional `Weight` (`light`/`full`, alias `Peso`/`leve`/`completo`) no §5 e na fila; helper de leitura; `sdd-roadmap` e `sdd-specify`; fechar as 3 questões do PLAN
- [x] W-02 — `doctor` de EDD e `sdd-close` leem o peso; definir `edd_no_criteria` (evals.md sem nenhum `E-NNN` numa etapa fechada)

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes (linha de base: 343 testes); testes novos por item
- [ ] Fixture com etapa `light` e etapa `full` lado a lado; §5 sem a coluna lê tudo como `full`
- [ ] `sddkit update --dry-run` em cópia de projeto real: nenhuma etapa fechada nem o §5 mudam
- [ ] `CHANGELOG.md` cita W-01 e W-02; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.7.0`, fast-forward `main`, push de branch, tag e `main` (cada push confirmado pelo dono)
