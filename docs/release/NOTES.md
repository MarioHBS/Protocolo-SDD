# Notes — sdd-cli 4.9.1

## Verificação

- `python -m pytest -q` e `ruff check src tests`: verdes (515 testes; 13 novos em
  `test_kit_behind.py` e `test_edd_closed_without_evals.py`).
- **`doctor` 4.9.0 × 4.9.1 sobre o MESMO estado real dos 10 projetos** (2026-11-17; 4.9.0 = `sddkit`
  instalado, 4.9.1 = código da branch, antes do bump de versão): status de saída igual (0) nos 10; as
  únicas diferenças são as previstas.
  - P3 (EDD ligado em 2026-10-01, etapas 001–004 fechadas antes): saem 4 `edd_missing_evals` e
    4 `edd_missing_checklist`; entram 4 `edd_closed_without_evals` (note). Os avisos de formato das
    etapas com `evals.md` (`edd_spec_not_pointer` x3, `edd_todo_not_evals` x1) continuam iguais.
  - P3 a P9 ganham `kit_behind` (note), com o kit de cada um: 4.8.2, 4.8.2, 4.7.0, 4.3.1, 4.8.2,
    4.3.0, 4.0.0. P1, P2 e P10 (já em 4.9.0) não mudam.
  - Com o bump para 4.9.1, P1, P2 e P10 também passam a ter `kit_behind` até rodarem `update`: é o
    comportamento esperado.
- **`update --dry-run` nos 10 projetos**, com sha1 de `.sdd/`, `.claude/`, `.github/`, `.kilo/` e
  shims da raiz antes e depois: nenhum arquivo mudou, nos dois momentos (antes e depois do bump).
  Depois do bump os 10 mostram "Would bump kit_version -> v4.9.1" e a seção `v4.9.1` das notas.

## Decisões tomadas ao implementar

- `kit_behind` é sempre `note`; não vira `warn` por número de versões (o plano deixava em aberto).
- "Etapa fechada" pede dois sinais: `report.md` e linha `done`/`concluída` no §5. Etapa fora do §5
  continua com os avisos.
- Nenhum campo novo ("EDD desde a etapa N"): o estado da etapa basta para o caso real.

## Não verificado

- O hook `post-edit` (4.9.0) passa a contar as notas novas no resumo; não disparado no Claude Code
  real nesta versão (o cálculo é o mesmo do `doctor --json`).
- Tag `v4.9.1`, fast-forward de `main` e pushes esperam confirmação do dono.
