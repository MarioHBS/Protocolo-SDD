# TODO — sdd-cli 4.5.0

## Items

- [ ] N-00 — o dono decide o nome (bloqueia todos os demais; ver tabela de disponibilidade no PLAN)
- [ ] N-01 — segundo entry point com o nome novo
- [ ] N-02 — `sdd` imprime aviso de deprecação em `stderr` e executa normalmente
- [ ] N-03 — textos gerenciados (shims, README, skills) com o nome novo

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos por item
- [ ] Wheel instalado em ambiente limpo: os dois executáveis respondem, só `sdd` avisa, `--json` idêntico
- [ ] Verificado em um projeto real que `sdd update` reescreve só arquivos gerenciados
- [ ] `CHANGELOG.md` cita N-01 a N-03; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.5.0`, fast-forward `main`, push de branch, tag e `main` (cada push confirmado pelo dono)
