# TODO — sdd-cli 4.3.2

## Items

- [x] U-01 — `sdd update` em dia lista arquivos editados; `doctor` ganha `managed_file_edited` e `readme_anchor_missing`

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; testes novos por caso
- [x] Verificado em projeto real (`antologias_bilo_app`), só leitura
- [x] `CHANGELOG.md` cita U-01; versão em `pyproject.toml` e `content/VERSION`
- [x] `docs/release/NOTES.md`
- [x] tag `v4.3.2`, fast-forward `main`, push de branch, tag e `main` (cada push confirmado pelo dono)
