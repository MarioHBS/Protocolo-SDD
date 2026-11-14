# Plan — sdd-cli 4.8.1

**Branch:** `4.8.1` (de `main` = 4.8.0) · **Idioma:** português

Tema: arestas que a 4.8.0 deixou ao ser aplicada de verdade no primeiro projeto (P1, KNN Warehouse):
um backup que o git enxerga, um aviso de fim de linha que volta, uma cobrança de auditoria sobre
etapa já travada e um falso positivo antigo de acento.

Origem: estágio 19 do plano privado (K-01 a K-04), da avaliação do P1 em 2026-11-14, pedida pelo
dono depois de atualizar o projeto. Patch: nenhum comportamento de etapa muda; só o `doctor`, o
`fix` e o hash do manifesto.

## Estado atual do código (conferido em 4.8.0)

- `fix --weight` grava `.sdd/.pre-fix-backup/`; `fix --gitignore` só conhece pastas de worktree de
  agente e o `doctor` não avisa de backup visível ao git.
- `manifest.hash_file` hasheia os bytes como estão; o `update` grava CRLF no Windows e o git
  normaliza para LF depois, então `manifest_eol_drift` volta mesmo após `fix --manifest`.
- `audit_findings` pula só etapa com `report.md`; etapa em `CLOSING` travada antes da 4.8.0 recebe
  `lock_without_audit`.
- O detector v1 de `_mojibake.py` trata o `?` de `?range=` como acento perdido.

## Itens (K = ajuste do uso real)

- **K-01** `doctor` nota `backup_not_ignored`; `fix --gitignore` acrescenta `/.sdd/.pre-fix-backup/` e
  `/.sdd/.pre-migrate-backup/` quando existem e o git os vê.
- **K-02** o manifesto grava o hash do conteúdo em LF (`hash_file`); `matches_recorded` continua
  aceitando bruto, LF e CRLF, então manifestos antigos seguem válidos.
- **K-03** `lock_without_audit` não cobra etapa em `CLOSING` (constituição ou trilha) nem etapa com o
  `todo.md` todo marcado; divergência de `Locked-by-audit:` continua avisada.
- **K-04** o detector `mojibake_v1` ignora `?` seguido de `nome=` (query string).

## Decisões

1. K-02 muda o que o manifesto grava, não o tamanho do hash (a regra de `06-ADIADOS.md` sobre não
   truncar continua valendo); a leitura de hashes antigos não muda.
2. K-03 usa o que o projeto diz (estado e `todo.md`), porque o kit não sabe quando a spec foi
   travada. A alternativa de uma linha `Locked-by-audit: none` fica fora.
3. O marcador da skill global continua `v4.8.0`: o texto dela não mudou, e o `doctor` compara com o
   marcador do texto empacotado, não com a versão do kit.

## Riscos e testes

- K-02: arquivo intacto não pode parecer editado; fixtures com manifesto antigo (bruto CRLF) contra
  disco em LF e CRLF, e `update` seguinte sem backup novo.
- K-03: esconder etapa que precisaria de auditoria; a nota é só `note` e o `IMPLEMENTING` continua cobrado.
- K-04: não esconder perda real de acento (`m?s` continua acusando).

## Propaga por

Código (`cli.py`, `_index_checks.py`, `_mojibake.py`, `manifest.py`) e `sdd update` (texto da skill
`sdd-audit` e `USAGE.md`).
