# Plan — sdd-cli 4.3.2

**Branch:** `4.3.2` (from `main` = 4.3.1) · **Language:** Portuguese

## U-01 — Arquivo gerenciado editado à mão some da vista depois do primeiro `sdd update`

- **Origem:** `antologias_bilo_app`. O README do `.sdd/` tinha edição manual; o primeiro update o
  preservou e avisou, o manifest foi para a versão nova e as rodadas seguintes dizem "Already up
  to date" e o `doctor` "clean". As skills novas já citavam uma seção que esse README não tinha.
- **Evidência:** `cmd_update` encerra em `if installed >= bundled` antes de calcular os arquivos
  preservados; nenhum check do `doctor` compara o disco com o manifest além de fim de linha.
- **Solução:** `_managed_files_edited` (difere do manifest e do kit) alimenta a listagem do update
  em dia e o finding `managed_file_edited`; `_missing_readme_anchors` gera `readme_anchor_missing`.
- **Riscos e testes:** só leitura. Fixtures: README editado com manifest atual; projeto limpo sem
  findings; arquivo igual ao kit com hash antigo não é reportado.
- **Não corrige:** o conteúdo do arquivo do projeto; isso é decisão do dono.
