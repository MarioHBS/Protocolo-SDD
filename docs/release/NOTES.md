# Notas — sdd-cli 4.10.1

Feito em 2026-11-28 na branch `4.10.1` (de `main` = 4.10.0). Seis correções (K-08 a K-13), 833 testes
(baseline 735), `ruff` limpo.

## Verificação

- **`pytest` e `ruff check src tests`:** 833 passed, ruff limpo, com Python 3.12.10. Testes novos:
  `test_table_pipes.py`, `test_links_in_code.py`, `test_mojibake_code.py`, `test_doctor_summary.py`,
  `test_template_tables.py` (confere as tabelas de todos os `.md` do kit) e
  `test_active_stage_none.py`.
- **`doctor` e `context` 4.10.0 × 4.10.1 sobre o MESMO estado real de 11 projetos** (P1 a P11,
  somente leitura; 4.10.0 = tag extraída numa pasta temporária). Todos saem 0 nas duas versões.
  Diferenças, todas conferidas nos arquivos:
  - `kit_behind` (nota) em P4 e P11, os que já estavam na 4.10.0.
  - P3: 3 `mojibake_v1` a menos, todos query string sem `=` escrita como código (`?lat&lon&radius`).
  - P11: 1 `mojibake_v1` (regex entre crases) e 1 `abs_file_links` (`file:///` entre crases) a menos;
    o fecho passa de "1 kind(s)" a "clean.".
  - `context`: P2 apontava a etapa 015 e P7 a 025, ambas já fechadas, com `Active stage`
    "nenhuma"/"none". Agora nenhuma etapa.
- **`update --dry-run` nos 11 projetos:** exit 0 e o sha1 de `.sdd/`, `.claude/`, `.github/`, `.kilo/`,
  `.gitignore` e dos `.md` da raiz é igual antes e depois. `templates/audit.template.md` aparece como
  atualizável em todos, nunca como editado à mão. Os dois `hand-edited` do P2 (`README.md` e
  `track-state.template.md`) são os antigos, do IP-018.
- **`update` real em cópias de P2 (de 4.9.0) e P11 (de 4.10.0):** o template muda, o `doctor` sai
  "clean.", sem `managed_file_edited`, e um segundo `update --dry-run` não tem o que fazer.

## Decisões tomadas ao implementar

1. **`_cells` devolve a célula crua** (com o `\|`), para que reescrever a linha preserve os bytes.
2. **`_markdown.mask_code` só esconde código certo** (bloco fechado, crases em par dentro do mesmo
   bloco). Bloco aberto ou crase solta não escondem nada.
3. **`mojibake_v1` em código deixa de ser visto.** É o preço de não acusar regex e URL: um acento
   perdido escrito entre crases ou em bloco de código não aparece mais. O v2 continua valendo em
   qualquer lugar.
4. **`file:///` é procurado sem diferenciar maiúsculas** no `doctor` (como antes) e agora também no
   `fix --links`.
5. **Dica do `abs_file_links`:** passou a dizer que o `fix --links` só reescreve alvo dentro do
   projeto; os outros são editados à mão.
6. **Contagem do fecho:** conta os tipos (`code`) com severidade `warn` do relatório inteiro; pode
   subir em relação à 4.10.0 no mesmo projeto.
7. **"Nenhuma etapa":** valor que começa por `none`, `nenhum`, `nenhuma` ou `n/a`, ou é só um traço.
   Um slug como `none-handling` continua sendo uma etapa.

## Não verificado

- Sem vistoria final por agente separado (a 4.10.0 teve uma; esta é só de correções e foi revista pelo
  próprio autor).
- `markdownlint` não foi rodado: o MD056 é conferido pelo teste do kit, que conta as células.
- A saída colorida num terminal real.

## Fica para depois

P11/IP-001 e IP-005 a IP-008; P2/IP-016, itens 2 a 5, 7, 9 e 10; P5/IP-014 (pausar uma etapa).
