# Plan — sdd-cli 4.5.0

**Branch:** `4.5.0` (from `main` = 4.4.0) · **Language:** Portuguese

Tema: dar ao executável um nome que não colida com pacotes de outros ecossistemas, mantendo `sdd`
funcionando como alias deprecado até a v5. Motivo: P2/IP-003, em que `npx sdd` executou código de
terceiros. O texto de R3-01 (4.3.0) já ensina o agente a invocar o binário certo; renomear fecha o
risco de palpite de `npx`.

## Decisão do nome (N-00)

Decidido pelo dono em 2026-10-28: o executável passa a se chamar **`sddkit`**. Disponibilidade
conferida no mesmo dia (HTTP 404 = livre, 200 = ocupado):

| Nome | npm | PyPI | Observação |
|------|-----|------|------------|
| `sddkit` | livre | livre | candidato do plano; distintivo, fora do vocabulário do npm |
| `sdd-cli` | **ocupado** | livre | combina com o nome do pacote, mas `npx sdd-cli` executaria código alheio |
| `sdd` | **ocupado** | **ocupado** | nome atual do executável |
| `specdd` | **ocupado** | — | conferido só no npm |

Só o registro foi consultado; uma busca geral (marcas, repositórios, outros CLIs) ainda não foi
feita. Reservar o nome (N-05) segue sem decisão e não faz parte desta release.

## Estado atual do código

- `pyproject.toml`: pacote `sdd-cli`, `[project.scripts] sdd = "sdd_cli.cli:main"`, Python >= 3.12.
- `src/sdd_cli/content/__init__.py`: `CLI_NAME = "sdd"`; `cli.py` o usa em 7 pontos (R3-01).
- 27 arquivos de `tests/` mencionam o comando `sdd` (invocação ou prosa); a troca precisa separar os dois.
- `.sdd/`, manifesto, constituição, stages e hooks de caminho **não mudam**; os arquivos gerenciados
  são reescritos pelo `sdd update`.

## N-01 — Segundo entry point com o nome novo

- **Solução:** uma linha em `[project.scripts]` apontando para `sdd_cli.cli:main`; o nome vem de
  `CLI_NAME`. `sdd` continua instalado.
- **Testes:** os dois executáveis existem no wheel e respondem a `--version` com o mesmo valor.

## N-02 — `sdd` como alias deprecado

- **Solução:** quando chamado como `sdd`, imprime uma linha de aviso em `stderr` e executa
  normalmente; chamado pelo nome novo, não avisa. Remoção só na v5, junto com `sdd docs`. O aviso
  vai para `stderr` para não quebrar quem lê a saída nem `--json`.
- **Riscos e testes:** o nome com que o processo foi chamado (`argv[0]`) varia entre Windows
  (`sdd.exe`), pipx e `python -m`; cobrir os três. Saída de `--json` idêntica nos dois nomes.

## N-03 — Textos gerenciados com o nome novo

- **Solução:** shims, README e skills passam a dizer que o binário é Python no PATH e que nunca se
  usa `npx` nem `npm`, com o nome novo. Como R3-01 já usa `CLI_NAME`, é uma troca em um lugar;
  propaga por `sdd update`.
- **Riscos e testes:** os testes que checam o texto do manual (`test_help_docs.py`) e os que citam
  `sdd` em prosa; o manual deve citar `sdd` só como alias deprecado.

## Fora desta release

- **N-04** (`doctor` detecta o nome legado em `CLAUDE.md` e `.claude/settings*.json`; `fix`
  reescreve): vai na release seguinte, depois de o alias estar em uso, para o `doctor` não acusar
  todos os projetos antes de o dono poder agir. Reescrever permissões de agente é mudança de política
  de segurança do projeto.
- **N-05** (reserva do nome e distribuição por PyPI, npm ou só GitHub): decisão do dono; não migrar
  sem pedido explícito.
- Varredura dos projetos com menções (P5, P2, P4); em P4 cabe na migração para a versão vigente.

## Não faz

- Não remove o nome `sdd`.
- Não reescreve nada nos projetos além dos arquivos gerenciados que o `sdd update` já refresca.
- Não publica pacote em PyPI nem npm.
