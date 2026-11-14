# TODO — sdd-cli 4.8.0

## Items

- [x] U-02 — notas de versão no `update` (`RELEASE-NOTES.md`, `--notes`)
- [x] U-03 — `fix --weight` (coluna `Weight` vazia, backup, idempotente)
- [x] U-04 — critério de `light` verificável e reavaliação da fila ao fechar
- [x] U-05 — `global_skill_stale` e `update --global-skill`
- [x] S-01 — skill `sdd-audit` e agente do Claude Code
- [x] S-02 — `audit.template.md` e protocolo de rodadas
- [x] S-03 — `Locked-by-audit:` e checagem do `doctor`
- [x] S-04 — peso decide a revisão; gatilhos em `audit-lenses.md`
- [x] S-05 — seção opcional "To measure before implementing"

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes (428 testes, linha de base 365); testes novos por item
- [x] `update --dry-run` e `update --notes` em cópia dos 9 projetos: nada gravado, `constitution.md` nunca listada
- [x] Cópia do P2: `.claude/agents/sdd-spec-lock.md` e `CLAUDE.md` intactos
- [x] `fix --weight` em cópia de P1/P3/P4/P5/P6 (a coluna aparece; P4 já a tinha só na fila); 2ª execução limpa
- [x] `CHANGELOG.md` cita U-02..U-05 e S-01..S-05; versão em `pyproject.toml` e `content/VERSION`
- [x] `docs/release/NOTES.md`
- [ ] tag `v4.8.0`, fast-forward `main`, push de branch, tag e `main`
