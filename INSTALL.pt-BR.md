# Instalação da SDD CLI (pt-BR)

A `sdd` é uma CLI **Python** (somente stdlib, zero dependências) que prepara projetos
para o fluxo *Specification-Driven Development*. Funciona em **Windows**, **macOS** e
**Linux**. Não é um pacote npm/npx — se apareceu `could not determine executable to run`
ao usar `npx`, é porque a ferramenta é Python; use `pipx` ou `uv` (veja abaixo).

## Pré-requisito

- **Python ≥ 3.10** (`python --version` / `py --version`). Já vem em maioria dos sistemas.

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
sdd --version      # deve imprimir: sdd v2.1.0
sdd providers      # lista os 10 providers suportados
sdd docs           # imprime o manual completo
sdd docs --md SDD-USAGE.md   # grava o manual num arquivo
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
