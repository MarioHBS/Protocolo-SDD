# TODO — sdd-cli 4.5.0

## Items

- [x] N-00 — o dono decide o nome (bloqueia todos os demais; ver tabela de disponibilidade no PLAN)
- [x] N-01 — segundo entry point com o nome novo
- [x] N-02 — `sdd` imprime aviso de deprecação em `stderr` e executa normalmente
- [x] N-03 — textos gerenciados (shims, README, skills) com o nome novo

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; testes novos por item
- [x] Wheel instalado em ambiente limpo: os dois executáveis respondem, só `sdd` avisa, `--json` idêntico
- [x] Verificado em um projeto real que `sdd update` reescreve só arquivos gerenciados
- [x] `CHANGELOG.md` cita N-01 a N-03; versão em `pyproject.toml` e `content/VERSION`
- [x] `docs/release/NOTES.md`
- [ ] tag `v4.5.0`, fast-forward `main`, push de branch, tag e `main` (cada push confirmado pelo dono)
