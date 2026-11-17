# Plan — sdd-cli 4.9.1

**Branch:** `4.9.1` (de `main` = 4.9.0) · **Idioma:** português

Tema: dois pontos cegos do `doctor` achados numa vistoria de dez projetos reais em 2026-11-17. Ele
não diz quando o kit do projeto está atrás do CLI instalado, e cobra `evals.md` e `checklist.md` de
etapas fechadas antes de o projeto ligar o EDD.

Origem: estágio 21 do plano privado (K-06, K-07).

## Estado atual do código (conferido em 4.9.0)

- `cli.py:1137-1142` compara a versão do manifesto com `KIT_VERSION` só num sentido:
  `cli_older_than_project` (`warn`) quando o CLI é mais velho. Projeto mais velho que o CLI não gera
  nada; `global_skill_stale` cobre só a skill global.
- `cli.py:1151-1172`: com `features.edd`, toda pasta de `stages/` com `spec.md` e sem `evals.md` dá
  `edd_missing_evals`; com `report.md` e sem `checklist.md` dá `edd_missing_checklist`. Nenhum dos
  dois olha o estado da etapa no §5. O peso `light` não ajuda: não cala `edd_missing_evals`, e só
  isenta o checklist quando o `report.md` cobre todos os `E-NNN`, que não existem sem `evals.md`.
- `sddkit update --notes` já imprime as notas de versão desde o kit instalado, sem gravar (U-02).

## Itens

- **K-06** nota `kit_behind` quando a versão do manifesto é menor que a do CLI; diz as duas versões
  e manda ler `sddkit update --notes` e rodar `sddkit update --dry-run`.
- **K-07** etapa com `report.md`, sem `evals.md` e marcada `done` no §5: os dois avisos viram uma
  nota única, `edd_closed_without_evals`. Etapa aberta, ou fechada sem `report.md`, ou ausente do §5,
  continua com os avisos de hoje.

## Decisões

1. **`kit_behind` é sempre `note`.** Não bloqueia nem muda o status de saída. Não vira `warn` por
   número de versões: a régua seria arbitrária e o `update` é decisão do dono.
2. **"Fechada" exige dois sinais:** `report.md` na pasta (o mesmo sinal que o `doctor` já usa para
   "closed stage") **e** `Status` `done`/`concluída` na linha do §5. Um só não basta: relatório
   escrito antes da hora ou linha marcada à mão não escondem o aviso.
3. **Nota, não silêncio.** A evidência continua não sendo dispensada; a nota diz que a etapa não tem
   evals e o que fazer se ela não for anterior ao EDD.
4. **Sem campo novo.** Nada de "EDD desde a etapa N" na constituição ou no manifesto: o estado da
   etapa já basta para o caso real.

## Fora

- `edd_spec_not_pointer` e `edd_todo_not_evals` em etapas que têm `evals.md`: defeito de formato
  real, sem mudança.
