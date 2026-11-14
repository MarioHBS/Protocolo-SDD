# TODO — sdd-cli 4.8.2

## Items

- [x] K-05 — `backup_tracked` no `doctor`; `fix --gitignore` sem linha duplicada e com `unfixable` para pasta rastreada

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; testes novos do K-05
- [x] Repositório de teste com backup commitado: nota `backup_tracked`, `fix --gitignore`, `git rm -r --cached`, nota some
- [x] Cópia do P4 antes do commit `d2579c0`: não foi possível clonar (nome longo no Windows); caso reproduzido em repositório de teste
- [x] `update --dry-run` na cópia dos 9 projetos: nada gravado
- [x] `CHANGELOG.md` e `RELEASE-NOTES.md` citam K-05; versão em `pyproject.toml` e `content/VERSION`
- [x] `docs/release/NOTES.md`
- [x] tag `v4.8.2`, fast-forward `main`, push de branch, tag e `main`
