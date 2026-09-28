# TODO — Implementação sdd-cli 4.2.1

> Notas públicas de versão. Os projetos reais em que o kit foi avaliado aparecem como `P1`, `P2`… (ver a branch `roadmap`, `docs/roadmap/01-EVIDENCIA.md`).

Continuação da 4.2.0. Branch `4.2.1` (mesclada em `main` e publicada em 2026-09-23).
Legenda: `[x]` feito e verificado · `[ ]` pendente.

## Estado verificado

- `py -3.12 -m pytest -q`: 180 passed; `ruff check src tests` verde.
- `sdd --version` = `sdd v4.2.1`; `main` = `origin/main` (`4ac4462`).

## Feito

- [x] `sdd discover`: explica o fluxo, imprime o caminho do skill (projeto e kit), `--check FILE`, `--against PROJETO`.
- [x] Skill `sdd-discover` explica as escolhas de instalação (estimativas, trilhas, documentação, EDD, idioma, providers, dashboard).
- [x] Shims e README do kit citam o `sdd-discover`.
- [x] Correção: `sdd update` ignora reescrita CRLF/LF ao detectar arquivo editado à mão (19 de 26 arquivos de P1 eram preservados por engano).
- [x] `sdd update` atualiza os shims dos providers gerenciados (preserva o editado).
- [x] `doctor`: `manifest_eol_drift`; `sdd fix --manifest` regrava os hashes.
- [x] Trilha `on hold` / `em espera` não gera `track_not_started`.

## Pendente (depende do dono)

- [ ] Rodar `sdd update` em P1 real (simulado com `--dry-run`: atualiza README, `sdd-discover`, `sdd-track` e o shim; preserva `todo.template.md`) e depois `sdd fix --manifest`.
- [ ] Refazer o discovery de P1 e rodar `sdd discover --check discovery.json --against .`.
- [ ] Limpar o `SDD-USAGE.md` solto na raiz de P1.
- [ ] Dashboard `interactive` em terminal real.

## Adiado

Ver a lista de itens adiados do mantenedor (contingência por `Origin`, `fix --index`, arquivar linhas frias, dashboard com servidor, etc.).
