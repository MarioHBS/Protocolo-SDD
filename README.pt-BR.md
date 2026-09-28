# sdd-cli

Estrutura para **Spec-Driven Development (SDD)** com agentes de código de IA.

O `sdd-cli` instala num projeto um kit metodológico pequeno e agnóstico de IDE (a pasta
`.sdd/`) e um atalho fino para o seu agente (Claude Code, Copilot, Cursor, Codex, Gemini CLI e
outros). O agente passa então por uma máquina de estados — decidir, roadmap, especificar,
implementar, fechar — em que a **constituição** e as **specs das etapas** são a fonte da
verdade e o disco é a verdade sobre o que existe. O CLI é deliberadamente "burro": copia
arquivos, grava um manifesto e audita o resultado. Todo o raciocínio fica em skills que rodam
dentro do agente.

[English](README.md)

## Início rápido

Requer **Python 3.12 ou superior**. Não é um pacote npm: instale com `pipx` ou `uv`.

```bash
pipx install git+https://github.com/MarioHBS/Protocolo-SDD.git   # versão mais recente (main)
# ou fixe uma versão:
pipx install git+https://github.com/MarioHBS/Protocolo-SDD.git@v4.2.1

cd seu-projeto
sdd init            # escolha o idioma e os agentes de IA
sdd doctor          # audite o resultado
sdd manual          # manual completo
```

Guias por sistema (Windows, macOS, Linux × pipx, uv) em [docs/install/](docs/install/):
[English](docs/install/INSTALL.en.md) ·
[Português](docs/install/INSTALL.pt-BR.md) ·
[Español](docs/install/INSTALL.es.md).

Dependências opcionais do dashboard (`rich`, `textual`):
`pipx install "sdd-cli[dashboard] @ git+https://github.com/MarioHBS/Protocolo-SDD.git"`
(ou `pipx install ".[dashboard]"` a partir de um clone).

## O que o kit gerencia e o que deixa em paz

| Gerenciado pelo kit (substituído em `update`/`migrate`) | Seu (nunca sobrescrito) |
|--------------------------------------------------------|--------------------------|
| `.sdd/README.md`, `.sdd/skills/`, `.sdd/templates/`, atalhos dos agentes | `.sdd/constitution.md`, `.sdd/roadmap.md`, `.sdd/stages/`, `CHANGELOG.md` |

Edições em arquivos gerenciados são detectadas pelo manifesto e guardadas em cópia antes da
substituição. As instruções dos skills são em inglês (confiabilidade entre agentes); os seus
artefatos usam o idioma escolhido no `init`.

## Comandos

| Finalidade | Comandos |
|------------|----------|
| Preparar | `init`, `discover`, `providers`, `update`, `migrate` |
| Diagnosticar | `doctor`, `fix`, `health`, `context`, `evaluate` |
| Trabalhar | `session`, `scaffold`, `track`, `seq`, `deps`, `impact` |
| Documentar | `document`, `manual` |
| Observar | `dashboard` |

Rode `sdd <comando> --help` para detalhes, ou `sdd manual` para tudo. Para um projeto que ainda
não existe, o skill `sdd-discover` produz um `discovery.md` revisado e um `discovery.json` que
`sdd init CAMINHO --discovery discovery.json` importa.

## Versões

Cada versão tem a sua branch, e a `main` sempre mostra a mais recente. As versões também têm tag
(`vX.Y.Z`). Veja [docs/branching.md](docs/branching.md) para a organização das branches e o
[CHANGELOG.md](CHANGELOG.md) para o que mudou.

| Versão | Branch | Tag | Situação |
|--------|--------|-----|----------|
| 4.2.1 | [`4.2.1`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.2.1) | `v4.2.1` | **Mais recente** — `main` |
| 4.2.0 | [`4.2.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.2.0) | `v4.2.0` | Discovery, dashboard `--ui web`, EDD com fonte única |
| 4.1.0 | [`4.1.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.1.0) | `v4.1.0` | Contexto por sessão, trilhas verificáveis, documentação ativa |
| 4.0.0 | [`4.0.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/4.0.0) | `v4.0.0` | Sessões, diagnósticos, inteligência do projeto |
| 3.3.0 | [`3.3.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.3.0) | `v3.3.0` | Providers e trilhas paralelas opt-in |
| 3.2.0 | [`3.2.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.2.0) | `v3.2.0` | Trilhas paralelas sem git worktree |
| 3.1.0 | [`3.1.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.1.0) | `v3.1.0` | `sdd update` |
| 3.0.0 | [`3.0.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/3.0.0) | `v3.0.0` | Snapshot pré-Git |
| 2.2.0 | [`2.2.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/2.2.0) | `v2.2.0` | Snapshot pré-Git |
| 2.1.0 | [`2.1.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/2.1.0) | `v2.1.0` | Snapshot pré-Git |
| 2.0 | [`2.0`](https://github.com/MarioHBS/Protocolo-SDD/tree/2.0) | `v2.0` | Snapshot pré-Git |

As versões 2.0 a 3.0.0 são anteriores ao histórico Git deste repositório: cada branch é um
único commit, extraído do zip da release arquivada, sem histórico commit a commit.

As próximas versões planejadas estão descritas na branch
[`roadmap`](https://github.com/MarioHBS/Protocolo-SDD/tree/roadmap).

## Estrutura do repositório

```text
src/sdd_cli/         código do CLI; content/ guarda o kit copiado para os projetos
tests/               suíte pytest
docs/                guias de instalação, modelo de branches e (nas branches de versão) notas da release
CHANGELOG.md         o que mudou em cada versão
CONTRIBUTING.md      como reportar problemas e propor mudanças
```

## Contribuindo

Atritos encontrados ao usar o kit são a contribuição mais valiosa. Veja
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

[MIT](LICENSE) © 2026 Mário Henrique
