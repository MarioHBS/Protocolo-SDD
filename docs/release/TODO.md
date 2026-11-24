# TODO — sdd-cli 4.10.0

## Items

- [x] M-01 — `_adr.py`, template do ADR, `sddkit adr new`, numeração sem reuso
- [x] M-02 — `sddkit adr index`, coluna "Registro" na §3, critério no `sdd-decide`
- [x] M-05 — campo `Decision records` na §7 e verificações do `doctor`
- [x] M-03 — discovery com `context`/`alternatives`/`adr`; ADRs `proposta`; `sdd-decide`
- [x] M-04 — `sddkit adr init` (entrevista de legado)
- [x] `USAGE.md`, READMEs, `RELEASE-NOTES.md` e `CHANGELOG.md` documentam tudo
- [x] versão em `pyproject.toml` e `content/VERSION`

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; testes novos de cada item
- [x] `doctor` 4.9.6 × 4.10.0 sobre o MESMO estado real dos 10 projetos: só as diferenças previstas
- [x] `adr init --dry-run` e `--answers` em cópia de P2 (ADRs externos) e P4 (ADRs em documento)
- [x] `update --dry-run` nos 10 projetos: nada gravado; `update` real em cópia do P7 não cria `decisions/`
- [x] `adr index` duas vezes: arquivo idêntico byte a byte
- [x] revisão do material complementar (help, doctor, skills, template, READMEs)
- [x] vistoria final por agente Opus, achados tratados
- [x] `docs/release/NOTES.md`
- [ ] tag `v4.10.0`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
