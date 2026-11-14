# TODO — sdd-cli 4.8.0

## Items

- [ ] U-02 — notas de versão no `update` (`RELEASE-NOTES.md`, `--notes`)
- [ ] U-03 — `fix --weight` (coluna `Weight` vazia, backup, idempotente)
- [ ] U-04 — critério de `light` verificável e reavaliação da fila ao fechar
- [ ] U-05 — `global_skill_stale` e `update --global-skill`
- [ ] S-01 — skill `sdd-audit` e agente do Claude Code
- [ ] S-02 — `audit.template.md` e protocolo de rodadas
- [ ] S-03 — `Locked-by-audit:` e checagem do `doctor`
- [ ] S-04 — peso decide a revisão; gatilhos em `audit-lenses.md`
- [ ] S-05 — seção opcional "To measure before implementing"

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes (linha de base 365); testes novos por item
- [ ] `update --dry-run` e `update --notes` em cópia dos 9 projetos: nada gravado, `constitution.md` nunca listada
- [ ] Cópia do P2: `.claude/agents/sdd-spec-lock.md` e `CLAUDE.md` intactos
- [ ] `fix --weight` em cópia de P1/P3 (coluna aparece) e P4 (nada muda)
- [ ] `CHANGELOG.md` cita U-02..U-05 e S-01..S-05; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.8.0`, fast-forward `main`, push de branch, tag e `main`
