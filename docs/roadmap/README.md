# Plano de atualizações do sdd-cli

**Base:** kit 4.2.1 (2026-09-23) · **Avaliação:** 2026-09-28 · **Estado:** planejado, nada implementado

Este plano organiza as melhorias encontradas ao usar o `sdd-cli` em cinco projetos reais
(citados como `P1`…`P5`) em **estágios pequenos, cada um com sua versão e sua branch**.
Cada item diz de onde veio o problema, onde ele está no código e qual a solução provável.
A solução **definitiva** só é decidida ao implementar o item, com avaliação mais criteriosa;
o que está aqui é o ponto de partida.

## Estágios

| Estágio | Versão | Tema | Itens | Bloqueia |
|---------|--------|------|-------|----------|
| [02](02-4.2.2-protecao-de-dados.md) | 4.2.2 | Não perder dado; detectores que entendem português | R2-01 a R2-07 | migração do projeto P4 |
| [03](03-4.3.0-usabilidade-do-agente.md) | 4.3.0 | Agente sabe invocar o CLI; ciclo de vida de trilhas; higiene | R3-01 a R3-06 | — |
| [04](04-4.4.0-nome-do-cli.md) | 4.4.0 | Novo nome do executável, `sdd` como alias | N-01 a N-05 | decisão do dono |
| [05](05-ADIADOS.md) | sem versão | Itens com gatilho de retomada | A-01 a A-13 | — |

Leitura de apoio: [00-METODO.md](00-METODO.md) (por que releases pequenas e como cada uma é
liberada), [01-EVIDENCIA.md](01-EVIDENCIA.md) (fontes, números e limites da avaliação) e
[ITEM-TEMPLATE.md](ITEM-TEMPLATE.md) (campos de cada item).

## Legenda de status

`planejado` · `em andamento` · `feito` · `adiado` · `descartado`.
Todos os itens estão `planejado` (ou `adiado`, em 05).

## Como este plano se conecta às branches

- Este material vive na branch `roadmap` (só documentação, nunca mesclada).
- Quando a próxima versão é aberta, o estágio correspondente é copiado para
  `docs/release/PLAN.md` da branch dela. Ver `docs/branching.md` na `main`.

## Nomenclatura

`P1`…`P5`: projetos avaliados. `P5/IP-004` = entrada `IP-004` do registro de atritos do
projeto P5. `R2-01` = item 1 do estágio 4.2.2; `R3-` para 4.3.0; `N-` para 4.4.0; `A-` para adiados.
