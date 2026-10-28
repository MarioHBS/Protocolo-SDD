# TODO — sdd-cli 4.6.0

## Items

- [x] G-01 — design system na lista estrutural de `sdd-decide`; `sdd-discover` (CLI) com a mesma lista; teste de paridade com o standalone
- [x] G-03 — `sdd-decide` nomeia 2–3 perspectivas em decisão estrutural sem resposta óbvia
- [ ] G-05 — `sdd-discover` (CLI) ramifica interpretações em ponto que bloqueia o portão
- [ ] G-04 — busca externa delimitada em `sdd-decide` e `sdd-discover` (teto de 2 consultas, consulta genérica, fallback)
- [ ] G-02 — `init --discovery` deixa `State: DECIDING` com decisões propostas; resolver as 3 questões do PLAN

## Gate

- [ ] `python -m pytest -q` e `ruff check src tests` verdes (linha de base: 328 testes); testes novos por item
- [ ] Teste de `init --discovery` (estado final e §3 como proposto) e do fallback sem busca
- [ ] `sddkit update --dry-run` em cópia de projeto real: só arquivos gerenciados mudam
- [ ] Conferido se algum projeto real usou `--discovery` antes de mudar o estado final (G-02)
- [ ] `CHANGELOG.md` cita G-01 a G-05; versão em `pyproject.toml` e `content/VERSION`
- [ ] `docs/release/NOTES.md`
- [ ] tag `v4.6.0`, fast-forward `main`, push de branch, tag e `main` (cada push confirmado pelo dono)
