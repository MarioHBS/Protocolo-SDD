# TODO — sdd-cli 4.9.1

## Items

- [ ] K-06 — nota `kit_behind` (manifesto < CLI), com `update --notes` e `update --dry-run`
- [ ] K-07 — `edd_closed_without_evals` no lugar de `edd_missing_evals` + `edd_missing_checklist` em etapa fechada sem `evals.md`
- [ ] `USAGE.md` cita os dois códigos

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos de K-06 e K-07
- [ ] `doctor` 4.9.0 × 4.9.1 sobre o MESMO estado real dos 10 projetos: só as diferenças previstas
- [ ] `update --dry-run` nos 10 projetos: nada gravado
- [ ] `CHANGELOG.md` e `RELEASE-NOTES.md` citam K-06 e K-07; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.9.1`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
