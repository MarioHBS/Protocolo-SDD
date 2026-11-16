# TODO — sdd-cli 4.9.0

## Items

- [ ] H-01 — `sddkit track guard --path` (colisão de footprint) e o hook `pre-edit` com `ask`
- [ ] H-03 — aviso de caminho fora do footprint da trilha da sessão (`additionalContext`)
- [ ] H-02 — hook `post-edit` roda o `doctor` quando `report.md` muda
- [ ] H-04 — `sddkit hooks install|uninstall|status` com merge no `.claude/settings.json`
- [ ] Skill `sdd-track`, `USAGE.md` e `RELEASE-NOTES.md` citam os hooks e o fallback manual

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos de H-01..H-04
- [ ] Projeto de teste com e sem hook: `track check`, `track guard` e `doctor` à mão iguais nos dois
- [ ] Hook real do Claude Code disparado numa edição (ask na colisão, aviso fora do footprint)
- [ ] `update --dry-run` na cópia dos projetos reais: nada gravado, `settings.json` intocado
- [ ] `CHANGELOG.md` e `RELEASE-NOTES.md` citam H-01..H-04; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.9.0`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
