# Notes — sdd-cli 4.4.0

- 307 testes passam; `ruff` limpo.
- Verificado só leitura em P1 (`KNN_WAREHOUSE`), P2 (`antologias_bilo_app`) e P5
  (`controle_fiado_app`): `sdd proposals collect` criou 28 arquivos (12 + 11 + 5, como no plano), a
  segunda execução deu 0 criados, 0 atualizados e 28 inalterados, e o hash SHA-256 de todos os
  arquivos dos três projetos (sem `.git` e `node_modules`) é idêntico antes e depois.
- `sdd proposals list` mostra 14 propostas e esconde 14 absorvidas pelo kit, como previsto em C-02.
- `sdd proposals send --via file` sobre as 14 não absorvidas achou 1 ocorrência (um caminho
  absoluto, em `controle_fiado_app`) e parou antes de gravar o pacote. As 6 linhas do plano incluem
  entradas já absorvidas, que `send` não leva por padrão.
- Achado na verificação: no Windows, `</dev/null` (NUL) responde `isatty()` verdadeiro, então o
  prompt leu EOF e terminou em traceback. Corrigido: prompt sem resposta conta como não; coberto por
  teste.
- Os códigos anônimos seguem a ordem de coleta, não a numeração de `MAPA.md`: neste teste
  `controle_fiado_app` virou `P3`. É esperado; o código existe só para o pacote não carregar o nome da
  pasta.
- `--via url` e `--via issue` foram testados só com navegador e `gh` simulados. Nenhuma issue foi
  criada e nenhum navegador foi aberto contra o repositório real.
