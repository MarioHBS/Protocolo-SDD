# Evidência — o que foi lido e o que isso prova

## Amostra (leitura de 2026-09-28)

| Código | Kit | Stages | Trilhas | Constituição | Registro de atritos |
|--------|-----|--------|---------|--------------|---------------------|
| P1 | 4.2.1 | 4 | desligadas | ~32 KB (em 2026-09-21) | IP-001 a IP-012; quase todos absorvidos na 4.1.0/4.2.0 |
| P2 | 4.2.1 | ~94 (11 com sufixo de letra) | 4 encerradas, 3 abertas | ~84 KB (em 2026-09-21) | IP-001 a IP-009; IP-003 a IP-009 abertos ou em contorno |
| P3 | 4.2.1 | 9 | desligadas | 293 linhas, linhas muito longas | não tem arquivo; `.migration-todo.md` esquecido |
| P4 | **4.0.0** | ~75 (14 com sufixo de letra) | 4 pastas encerradas | 574 linhas | não tem arquivo; roadmap de 1.655 linhas |
| P5 | 4.2.1 | 16 | 2 encerradas, 1 aberta | 203 linhas | IP-001 a IP-005, todos de 2026-09-28, da migração v3.2.0 → v4.2.1 |

Fontes: manifestos, constituições, roadmaps, changelogs, `CLAUDE.md`/`AGENTS.md`,
`.claude/settings*.json` e os registros de atritos dos projetos, mais o código do `sdd-cli`
4.2.1 (para localizar cada causa).

## Limites

- **Não foi executado `sdd doctor`** nos projetos (o shell estava indisponível na avaliação).
  Contagens de bytes de P3 e P4 e a lista real de achados do `doctor` ficam para a primeira
  execução depois do `sdd update`.
- Todas as citações de código são de 4.2.1; números de linha mudam entre versões.
- Não foi verificado se o nome candidato do executável está livre no npm.
- Os registros de atritos são autodeclarados pelos agentes e pelo dono de cada projeto. Cada
  item deste plano foi confirmado no código do kit; onde a confirmação foi parcial, o item diz.

## Mapa item → origem

| Item | Origem |
|------|--------|
| R2-01 | P5/IP-001; P4 (roadmap com 1.132 linhas de narrativa) |
| R2-02 | P5/IP-004; P2/IP-008; P4 |
| R2-03 | P2/IP-006 |
| R2-04 | P5/IP-002 |
| R2-05 | P5/IP-003 |
| R2-06 | P3 |
| R2-07 | P5/IP-005 |
| R3-01 | P2/IP-003 |
| R3-02 | P2/IP-008; P5/IP-004; P4 |
| R3-03 | P2/IP-005; P1 |
| R3-04 | P2/IP-007 |
| R3-05 | P2/IP-004 |
| R3-06 | P1/IP-003 |
| N-01 a N-05 | P2/IP-003 e a decisão de distribuição em aberto |
| A-01 a A-13 | ver `05-ADIADOS.md` |

## O que já está resolvido no kit (não reabrir)

Entradas dos projetos que o kit 4.1.0 a 4.2.1 já cobre: cobertura de evals, estados `[-]`/`[!]`,
divergência de features (`feature_mismatch`, `fix --features`), marcos contíguos, backlog de
primeira classe, `sdd docs --md` fora da raiz, nomes `static`/`interactive` do dashboard,
`--ui web`, EDD com fonte única (`migrate --edd-source-of-truth`), falso positivo de
`AGENTS.md` no `migrate --dry-run`, trilha `on hold`, hash CRLF/LF.
