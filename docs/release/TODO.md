# TODO — sdd-cli 4.8.1

## Items

- [x] K-01 — `backup_not_ignored` e `fix --gitignore` cobrindo os backups do kit
- [x] K-02 — manifesto grava o hash do conteúdo em LF
- [x] K-03 — `lock_without_audit` pula etapa em `CLOSING` ou com o `todo.md` todo marcado
- [x] K-04 — `mojibake_v1` ignora query string de URL

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; testes novos por item
- [x] Cópia do P1 e do P2: `doctor --json` sem `manifest_eol_drift`, `lock_without_audit` na etapa em `CLOSING` e `mojibake_v1` da query string
- [x] `update --dry-run` na cópia dos 9 projetos: nada gravado, `constitution.md` nunca listada
- [x] `fix --manifest` em cópia do P1: 2ª execução limpa, e a cópia continua limpa depois de trocar o fim de linha
- [x] `CHANGELOG.md` e `RELEASE-NOTES.md` citam K-01..K-04; versão em `pyproject.toml` e `content/VERSION`
- [x] `docs/release/NOTES.md`
- [x] tag `v4.8.1`, fast-forward `main`, push de branch, tag e `main`
