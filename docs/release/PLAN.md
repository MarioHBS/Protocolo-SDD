# Plan — sdd-cli 4.4.0

**Branch:** `4.4.0` (from `main` = 4.3.2) · **Language:** Portuguese

Tema: um caminho do próprio CLI para levar os atritos registrados em `.sdd/improvement-proposals.md`
de vários projetos até o mantenedor, sem cópia manual e sem escrever nada nos projetos de origem.
Comando novo: `sdd proposals collect|list|show|send`.

## Formato real das entradas (lido em 28 entradas de três projetos)

- Cabeçalho `## IP-NNN — título`; itens `- **Data:**`, `- **Status:**`, `- **Fase afetada:**`; depois
  parágrafos com rótulo em negrito. `Status` é texto livre que começa por `aberta`,
  `contorno local`, `proposta` ou `absorvida pelo kit`.
- Os IDs recomeçam em `IP-001` em cada projeto; a identidade da proposta é (projeto, `IP-NNN`).
- Uma entrada termina no próximo `##` de qualquer tipo (`## Como registrar` e `## Resolvidas` não
  são entradas); entradas podem estar fora de ordem.

## C-01 — `sdd proposals collect [PROJETO...] [--scan RAIZ]`

- **Solução:** lê `.sdd/improvement-proposals.md` de cada projeto e grava um arquivo por proposta
  (`<codigo>-IP-NNN.md`) numa caixa de entrada na pasta de dados do usuário, resolvida só com a
  biblioteca padrão e sobrescrevível por variável de ambiente. O hash do conteúdo só detecta edição:
  entrada alterada atualiza o arquivo, entrada igual não faz nada.
- **Riscos e testes:** colisão de ID entre projetos; entrada que some da origem não é apagada.
  Fixtures com `## Resolvidas`, ordem trocada e um projeto sem o arquivo; duas execuções seguidas;
  edição de entrada.

## C-02 — `sdd proposals list` / `show <ID>`

- **Solução:** `list` mostra origem, ID, data e status e esconde `absorvida pelo kit` por padrão
  (`--all` mostra tudo); `show P1-IP-001` imprime o texto completo. Só leitura.

## C-03 — `sdd proposals send --via file|url|issue`

- **Solução:** `file` gera um pacote Markdown; `url` abre uma issue pré-preenchida; `issue` usa `gh`
  e cai para `file` se não houver `gh` autenticado. Sempre mostra o texto exato antes e pede
  confirmação; nunca apaga a cópia do projeto.
- **Riscos e testes:** `file` sem rede; `url` e `issue` com processo externo simulado.

## C-04 — Aviso de dado privado antes de enviar

- **Solução:** o código do projeto (`P1`…) fica só na caixa de entrada local; ao enviar, avisa sobre
  e-mails, caminhos absolutos e padrões de segredo e pede confirmação por ocorrência. A varredura é
  heurística e a documentação diz isso. Roda antes do envio de C-03.
- **Evidência:** 6 linhas com caminho absoluto ou e-mail nos arquivos reais de P1 e P5.

## C-05 — Aviso de projeto sem o arquivo de propostas

- **Solução:** `--scan` informa, como nota e não como erro, cada projeto com `.sdd/` e sem o
  arquivo. A grafia `improvements-proposals.md` (plural) conta como ausente; não se adivinha o nome.

## Não faz

- Não escreve, move nem apaga nada nos projetos de origem.
- Não envia nada sem confirmação explícita.
- Não adiciona dependência: o kit continua com `dependencies = []`.
