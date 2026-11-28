# Plan — sdd-cli 4.10.1

**Branch:** `4.10.1` (de `main` = 4.10.0) · **Idioma:** português

Tema: correções. O item que a vistoria da 4.10.0 deixou registrado (M4, `|` escapado em célula) e os
defeitos registrados em uso real em 2026-11-26 e 2026-11-27. Escopo escolhido pelo dono em
2026-11-28: "M4 + defeitos"; as melhorias pedidas nos mesmos registros ficam para depois.

## Itens

- **K-08** (vistoria da 4.10.0, M4) um `|` dentro de uma célula quebra a tabela: `_cells` corta no
  `\|` escapado, `init --discovery` grava o valor sem escapar, e a linha de um achado de `audit.md`
  com `\|` deixa de ser lida.
- **K-09** (P11/IP-002) `abs_file_links` acusa `file:///` escrito em código (entre crases ou em bloco)
  ou sem destino, e indica um `fix --links` que não tem o que fazer.
- **K-10** (P11/IP-003) `accent-loss` acusa o `?` de uma expressão regular escrita como código, e a
  saída padrão não diz a linha.
- **K-11** (P11/IP-004) o fecho do `doctor` conta menos tipos de aviso do que a tela mostra (e pode
  dizer "clean." com um aviso de trilha na tela).
- **K-12** (P2/IP-016, item 1) `audit.template.md` tem `|` solto numa célula: o projeto que roda
  markdownlint reprova (MD056) num arquivo do kit.
- **K-13** (P2/IP-016, item 12) `Active stage` que começa por "nenhuma"/"none" e cita números na
  narrativa aponta uma etapa concluída como ativa.

## Decisões

1. **Célula continua crua.** `_cells` corta só no `|` sem barra e devolve o texto como está no arquivo
   (com o `\|`), para que reescrever a linha não mude um byte da célula.
2. **Escape único** (`_index_checks.cell_text`) para tudo que o kit escreve numa célula: não escapa duas
   vezes.
3. **Código é ignorado só pelos dois detectores** (`file:///` e `accent-loss` v1). O v2 (codificação
   dupla), que é determinístico e bloqueia o `migrate`, não muda. Bloco sem fechamento e crase sem par
   não escondem nada: na dúvida, o aviso sai.
4. **`fix --links` segue o mesmo critério do `doctor`:** link dentro de código não é reescrito.
5. **Linhas do `accent-loss` na saída padrão** quando são até 10 ocorrências; acima disso, a dica do
   `doctor --all`.
6. **Nenhum comando novo e nenhum arquivo do dono reescrito.** O único arquivo gerenciado que muda é
   `templates/audit.template.md`; o gate confere o `managed_file_edited` nos projetos (família do
   IP-018).

## Fora desta release

- P11/IP-001 (diff no `fix --dry-run`), IP-005 (nome da lente), IP-006 (`## Verifiers`), IP-007
  (`hooks install --only`), IP-008 (marca do atalho global).
- P2/IP-016, itens 2 a 5, 7, 9 e 10; P5/IP-014 (pausar uma etapa).

## Gate de saída

Suíte e `ruff` verdes com um teste por item; `doctor` 4.10.0 × 4.10.1 sobre o mesmo estado real dos
projetos, só com as diferenças previstas; `update --dry-run` sem gravar nada; `update` real em cópia.
