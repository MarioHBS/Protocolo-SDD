# Instalação da SDD CLI (pt-BR)

A `sdd` é uma CLI **Python** (somente stdlib, zero dependências) que prepara projetos
para o fluxo *Specification-Driven Development*. Funciona em **Windows**, **macOS** e
**Linux**. Não é um pacote npm/npx — se apareceu `could not determine executable to run`
ao usar `npx`, é porque a ferramenta é Python; use `pipx` ou `uv` (veja abaixo).

## Pré-requisito

- **Python ≥ 3.12** (`python --version` / `py --version`). Versões antigas instalam "com sucesso" e falham
  na primeira execução com um `SyntaxError`.

## Instalação recomendada: `pipx`

O `pipx` isola a CLI num ambiente próprio e poe `sdd` no PATH automaticamente.

### Windows (PowerShell)

```powershell
# se ainda não tem o pipx:
py -m pip install --user pipx
py -m pipx ensurepath

# instalar a SDD CLI (a partir da pasta descompactada do pacote):
pipx install .\sdd-cli

# abra um NOVO terminal (para o PATH recarregar) e verifique:
sdd --version
```

> Se `sdd` não for reconhecido numa janela já aberta, abra uma **nova** janela de
> terminal — o `ensurepath` só recarrega em novas sessões. Alternativamente:
> `py -m pipx install .\sdd-cli` invoca o pipx direto mesmo se o PATH não estiver ok.

### macOS / Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# instala a partir da pasta descompactada:
pipx install ./sdd-cli

# abra um novo terminal e:
sdd --version
```

## Instalação alternativa: `uv`

Se preferir o `uv` (mais rápido, da Astral):

```bash
uv tool install ./sdd-cli          # macOS / Linux
uv tool install .\sdd-cli          # Windows (PowerShell)
```

## Verificação pós-instalação

```bash
sdd --version      # deve imprimir a versão instalada do sdd
sdd providers      # lista os providers suportados
sdd manual         # imprime o manual completo (`sdd docs` é um alias obsoleto)
sdd manual --md SDD-USAGE.md   # grava o manual num arquivo
```

## Opcional: o dashboard

`sdd dashboard` precisa de `rich` e/ou `textual`, que a instalação básica não traz.
O kit é instalado a partir da pasta dele, então peça os extras ali:

```bash
pipx install --force './sdd-cli[dashboard]'      # rich + textual (no Windows use .\sdd-cli)
# ou só um renderizador:  './sdd-cli[dashboard-rich]'  /  './sdd-cli[dashboard-textual]'
# sem extras no pipx:     pipx inject sdd-cli rich textual
sdd dashboard --ui rich
```

## Erro comum: `npm error could not determine executable to run`

Isso acontece se você tenta `npx install ./sdd-cli` ou `npm i ./sdd-cli`. A SDD CLI
**não é um pacote Node** — é Python. Use `pipx` ou `uv` (acima). O erro é confuso porque
ambos rodaram num terminal, mas o `npx` procura um `package.json` com binário JavaScript
que não existe neste projeto.

## Próximo passo

Dentro da pasta de um projeto:

```bash
sdd init --provider claude --language pt-BR -y
```

Depois abra seu agente (Claude Code, Cursor, etc.) no projeto e dispare `/sdd` (ou o
gatilho do seu provider — veja `sdd providers`). O agente vai ler `.sdd/README.md` e
entrar na fase INITIALIZING conversando em português.

## Migração de um projeto v1

```bash
# SEMPRE faça primeiro um backup do projeto e rode o dry-run:
sdd migrate --to v2 --dry-run
sdd migrate --to v2
```

O `migrate` detecta seu(s) provider(s), idioma e edições manuais; substitui só os
arquivos *managed* (README, skills, templates, shims) preservando `constitution.md`,
`roadmap.md` e `stages/`. Depois gera `.sdd/.migration-todo.md`: o agente conduz as
edições restantes na constituição, pedindo sua confirmação **uma mudança por vez**.

## Atualizar um projeto v2 para v3

```bash
sdd migrate --to v3 --dry-run
sdd migrate --to v3
```

Um projeto v2 cuja constituição já é canônica (headings em inglês, `## Settings`,
`**State:** <um estado v2>`) gera um `.migration-todo.md` mínimo com só as tarefas
de normalização de codificação e reconcile -- não há headings PT nem skill names em
português para renomear. O flag documenta a intenção (`--to v2` = legado v1→v2,
`--to v3` = refresh v2→v3); ambos instalam o kit atual e bumpa o manifest.
