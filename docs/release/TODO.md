# TODO — sdd-cli 4.8.2

## Items

- [ ] K-05 — `backup_tracked` no `doctor`; `fix --gitignore` sem linha duplicada e com `unfixable` para pasta rastreada

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos do K-05
- [ ] Repositório de teste com backup commitado: nota `backup_tracked`, `fix --gitignore`, `git rm -r --cached`, nota some
- [ ] Cópia do P4 antes do commit `d2579c0` (backup rastreado): `doctor` 4.8.1 × 4.8.2
- [ ] `update --dry-run` na cópia dos 9 projetos: nada gravado
- [ ] `CHANGELOG.md` e `RELEASE-NOTES.md` citam K-05; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.8.2`, fast-forward `main`, push de branch, tag e `main` (só com a confirmação do dono)
