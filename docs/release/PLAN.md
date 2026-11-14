# Plan — sdd-cli 4.8.2

**Branch:** `4.8.2` (de `main` = 4.8.1) · **Idioma:** português

Tema: o `backup_not_ignored` da 4.8.1 não resolve o projeto cujo backup já foi commitado: o `fix
--gitignore` grava a linha, o arquivo continua rastreado e a nota volta igual, mandando rodar o mesmo
comando.

Origem: estágio 20 do plano privado (K-05), achado em 2026-11-14 ao comparar os quatro projetos que o
dono atualizou para a 4.8.1 (P2, P3, P4 e P7). No P4, `.sdd/.pre-migrate-backup/` tinha um arquivo
commitado em 2026-08-31. Patch: só o `doctor` e o `fix --gitignore`.

## Estado atual do código (conferido em 4.8.1)

- `_unignored_backups` pergunta ao `git check-ignore` se a pasta é ignorada; para arquivo já
  rastreado a resposta é sempre "não ignorado", mesmo com a linha no `.gitignore`.
- Efeito 1: o `doctor` nota `backup_not_ignored` e indica `fix --gitignore`, que não ajuda.
- Efeito 2: com a pasta rastreada **e** listada no `.gitignore`, o `fix --gitignore` acrescenta a
  mesma linha de novo a cada execução (a checagem de "falta" usa o mesmo `check-ignore`).

## Item

- **K-05** `doctor` separa os dois casos: pasta de backup que o git só enxerga
  (`backup_not_ignored`, `fix --gitignore`) e pasta já rastreada (`backup_tracked`, nota com
  `git rm -r --cached <pasta>`). `fix --gitignore` decide o que falta com `check-ignore --no-index`
  (ignora o índice), nunca duplica uma linha, e lista a pasta rastreada como `unfixable`
  `backup_tracked`, porque o kit não mexe no índice do git do dono.

## Decisões

1. O kit não roda `git rm --cached` sozinho: o índice é do dono e a ação tem efeito em quem puxar o commit.
2. `backup_tracked` é `note`, como o `backup_not_ignored`; a gravidade não sobe por rastreado.
3. `fix --gitignore` com pasta rastreada termina com status 2 (`unresolved`), igual aos demais casos que
   o `fix` não consegue resolver sozinho.

## Riscos e testes

- Repositório com a pasta rastreada e sem linha: `doctor` acusa `backup_tracked`; `fix --gitignore`
  grava a linha uma vez e lista `unfixable`; depois do `git rm --cached` a nota some.
- Rastreada e já listada: `fix --gitignore` não grava nada (sem linha duplicada), só `unfixable`.
- Sem `.git`, ou pasta de backup inexistente: nenhum aviso (como na 4.8.1).

## Propaga por

Só código (`cli.py`, `_findings.py`) e o texto do `USAGE.md`.
