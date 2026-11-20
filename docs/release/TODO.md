# TODO — sdd-cli 4.9.6

## Items

- [x] E-01 — `fix --slim` (comentário idêntico ao do template; `--dry-run`, backup, fim de linha preservado)
- [x] E-01 — `constitution_oversized` mostra limite, maiores seções e quanto o `--slim` recupera
- [x] E-02 — `doctor --slim` (bytes por seção, linhas acima de 600 B com destino, instrução ao agente; `--json`)
- [ ] `USAGE.md` documenta `fix --slim` e `doctor --slim`

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos de E-01 e E-02
- [ ] `doctor` 4.9.1 × 4.9.6 sobre o MESMO estado real dos 10 projetos: só as diferenças previstas
- [ ] `fix --slim` em cópia da constituição de P3 e P4: remove só o previsto, deixa backup
- [ ] `update --dry-run` nos 10 projetos: nada gravado
- [ ] `CHANGELOG.md` e `RELEASE-NOTES.md` citam E-01 e E-02; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.9.6`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
