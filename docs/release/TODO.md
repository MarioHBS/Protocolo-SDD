# TODO — sdd-cli 4.10.0

## Items

- [ ] M-01 — `_adr.py`, template do ADR, `sddkit adr new`, numeração sem reuso
- [ ] M-02 — `sddkit adr index`, coluna "Registro" na §3, critério no `sdd-decide`
- [ ] M-05 — campo `Decision records` na §7 e verificações do `doctor`
- [ ] M-03 — discovery com `context`/`alternatives`/`adr`; ADRs `proposta`; `sdd-decide`
- [ ] M-04 — `sddkit adr init` (entrevista de legado)
- [ ] `USAGE.md`, READMEs, `RELEASE-NOTES.md` e `CHANGELOG.md` documentam tudo
- [ ] versão em `pyproject.toml` e `content/VERSION`

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes; testes novos de cada item
- [ ] `doctor` 4.9.6 × 4.10.0 sobre o MESMO estado real dos 10 projetos: só as diferenças previstas
- [ ] `adr init --dry-run` e `--answers` em cópia de P2 (ADRs externos) e P4 (ADRs em documento)
- [ ] `update --dry-run` nos 10 projetos: nada gravado; `update` real em cópia do P7 não cria `decisions/`
- [ ] `adr index` duas vezes: arquivo idêntico byte a byte
- [ ] revisão do material complementar (help, doctor, skills, template, READMEs)
- [ ] vistoria final por agente Opus, achados tratados
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.10.0`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
