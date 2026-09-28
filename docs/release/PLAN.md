# Plan — sdd-cli 4.2.2

**Branch:** `4.2.2` (from `main` = 4.2.1) · **Status:** planned, nothing implemented · **Language:** Portuguese

Copied from the formal update plan on the [`roadmap`](https://github.com/MarioHBS/Protocolo-SDD/tree/roadmap)
branch (`docs/roadmap/02-4.2.2-protecao-de-dados.md`). Projects `P1`…`P5` are the real projects the
kit was evaluated on; see `docs/roadmap/01-EVIDENCIA.md` there. The solution listed in each item is
the starting point; the final one is decided when the item is implemented.

## Estágio 02 — 4.2.2: proteção de dados e detectores que entendem português

**Tema:** parar de perder ou de acusar errado. Correção de defeitos, sem capacidade nova.
**Bloqueia:** a migração do projeto P4 (kit 4.0.0, roadmap de 1.655 linhas).
**Gate de saída:** `migrate --dry-run` em cópia do roadmap de P4 lista o que sairia; suíte e
ruff verdes; um teste novo por item, a partir de fixture do episódio real.

Ordem sugerida: R2-01 primeiro (protege dado), R2-02 e R2-03 (mesma família: cabeçalhos
localizados), depois os textos (R2-04, R2-05) e as notas do `doctor` (R2-06, R2-07).

---

### R2-01 — Regenerar o `roadmap.md` a partir do §5 apaga texto que só existe ali

- **Status:** planejado
- **Origem:** P5/IP-001. Na migração v3.2.0 → v4.2.1, a Task 7 mandou regenerar o roadmap a
  partir do §5; o arquivo caiu de 200 para 57 linhas e o texto de "Entrega" de cada etapa
  deixou de existir (o §5 só tem etapa, slug, status, dependências e links). O dono só evitou
  a perda porque copiou o arquivo à mão antes. P4 é o caso maior: seu roadmap tem 1.655
  linhas, das quais 1.132 (seção "Detalhamento por etapa") são texto escrito à mão, além de
  agrupamentos por bloco e coluna "Habilita".
- **Evidência:** `src/sdd_cli/content/sdd/skills/sdd-reconcile/SKILL.md:39` ("Regenerate
  `roadmap.md` from §5"); `.../sdd-close/SKILL.md:71` ("Never hand-edit the roadmap");
  Task 7 em `cli.py` (~linha 2101, "regenerates `roadmap.md` from section 5");
  `content/sdd/roadmap.md` e `templates/roadmap.template.md` ("Do not add manual
  narrative"). O `.pre-migrate-backup/` só guarda arquivos gerenciados, não o roadmap.
- **Causa raiz:** o kit v4 assume que o detalhe de cada etapa mora na spec e no `backlog.md`,
  e que o roadmap é só um espelho. Não trata o projeto migrado cujo roadmap era a única casa
  desse texto, e a migração não avisa nem faz cópia.
- **Solução provável:** (a) `migrate` copia o `roadmap.md` para `.pre-migrate-backup/` antes
  da Task 7; (b) o `--dry-run` e o texto da Task 7 dizem quantas linhas do roadmap estão fora
  da tabela-espelho e que elas seriam descartadas; (c) decidir na implementação entre só
  avisar (mais seguro) ou fazer o `reconcile` regenerar apenas a tabela-espelho e preservar as
  seções livres (mais útil, mas exige delimitar o que é "espelho").
- **Riscos e testes:** o passo (c) mexe no contrato do roadmap e em quatro skills. Fixture:
  roadmap com blocos, coluna extra e seção "Detalhamento" longa; o teste verifica que nada
  fora da tabela é removido sem confirmação e que o backup existe.
- **Dependências:** nenhuma.
- **Propaga por:** `sdd update`/`migrate` (skills e texto da Task 7) e código.

### R2-02 — Os detectores só conhecem títulos em inglês

- **Status:** planejado
- **Origem:** P5/IP-004. O `doctor` repete, a cada execução, `track_not_started` para duas
  trilhas já incorporadas ao §5; o aviso descreve o oposto da realidade e treina o dono a
  ignorar o relatório. A constituição de P5 usa o título `### Trilhas ativas`. P2/IP-008 e P4
  mostram o mesmo efeito: 4 pastas de trilha encerrada em cada um, sem sinal de estado.
- **Evidência:** `_user_files.py:81-99` (`active_track_slugs` busca `^###\s+Active tracks`) e
  `:105-118` (`on_hold_track_slugs`, mesmo título); `_tracks.py:350-363`
  (`_stage_index_span` busca `^##\s+5\.` e `^###\s+Provisional`). Com o título traduzido, a
  função devolve `None`, a trilha nunca é considerada encerrada e o marcador `on hold` da
  4.2.1 também não funciona. Em P4 a tabela traz a linha "nenhuma trilha aberta hoje" sem
  crases, que também resulta em `None`. O regex de `closed` em `_user_files.py:135` só
  reconhece `status: closed`, não `ENCERRADA`.
- **Causa raiz:** o código casa o texto literal dos títulos do template em inglês, mas o
  kit permite (e o `sdd init` em pt-BR produz) constituições com títulos traduzidos.
- **Solução provável:** uma tabela única de aliases de títulos (`Active tracks`/`Trilhas
  ativas`, `Provisional queue`/`Fila provisória`, `Stage index`/`Índice de etapas`) usada por
  todos os detectores; reconhecer `ENCERRADA`/`encerrada`/`closed` no `state.md`; tratar a
  linha "nenhuma trilha" como tabela vazia sem cair em `None`.
- **Riscos e testes:** aceitar aliases demais pode casar título de outra seção. Fixtures:
  constituição pt-BR com trilha encerrada; tabela vazia; trilha `em espera` com título
  traduzido.
- **Dependências:** base do R3-02.
- **Propaga por:** só código.

### R2-03 — `sdd track incorporate` grava linha vazia no §5 e não valida

- **Status:** planejado
- **Origem:** P2/IP-006, duas ocorrências (2026-09-24 e 2026-09-25). O comando imprimiu
  `index row: |  |  |  |`, a linha da etapa não entrou no §5 (foi inserida à mão) e na segunda
  vez acrescentou uma segunda linha vazia. Depois, `sdd track verify` falhou com
  `track_unclaimed_touch` porque a trilha não tinha claim algum, o que obrigou a declarar um
  claim que a etapa não precisava.
- **Evidência:** `_tracks.py:380-399` (`_index_row` monta as células por prefixo do
  cabeçalho: `stage`/`etapa`, `slug`, `status`, `spec`, `report`/`relat`; qualquer outro vira
  vazio); `:402-452` (`incorporate` move a pasta e grava a linha sem checar se saiu vazia);
  `:243-246` (`verify` devolve `track has no path claims`). Confirmado que a liberação dos
  claims (`:445`) já existe em 4.2.1; a linha vazia e o `verify` continuam.
- **Causa raiz:** o cabeçalho real do §5 do projeto não casa com os nomes esperados (cabeçalho
  traduzido ou com nomes próprios) e não há validação antes de mover a pasta.
- **Solução provável:** validar a linha antes de mover (recusar se stage/slug saírem
  vazios); aceitar cabeçalhos localizados (mesma tabela de aliases do R2-02); no `verify`,
  distinguir "trilha sem claims" de "arquivo sem dono" e explicar como declarar.
- **Riscos e testes:** o `incorporate` é atômico (lock + renomear pasta); a validação deve
  vir antes de qualquer escrita. Fixture: §5 com cabeçalhos em português e com cabeçalho
  irreconhecível (deve recusar sem mover).
- **Dependências:** R2-02 (aliases).
- **Propaga por:** só código.

### R2-04 — Mensagem de backup para arquivo `manual` que não é substituído

- **Status:** planejado
- **Origem:** P5/IP-002. O `migrate` listou um arquivo de instruções do Copilot em "Hand-edited
  managed files … will be backed up before replacing"; fez a cópia, mas o arquivo continua
  intacto no projeto (no manifesto ele vale `manual`). O dono conferiu o `git status` para
  descobrir o que mudou de fato.
- **Evidência:** `cli.py:2278-2285` (`edited` inclui toda entrada editada, sem separar as
  `manual`; a mensagem fixa diz "backed up before replacing").
- **Causa raiz:** um único texto para dois casos (arquivo que será substituído e arquivo que o
  kit não gerencia).
- **Solução provável:** separar as entradas `manual` numa linha própria ("mantido, com cópia
  de segurança") e não anunciar substituição; decidir se vale fazer a cópia de arquivo que não
  será tocado.
- **Riscos e testes:** texto do `--dry-run` é contrato de testes existentes; ajustar juntos.
- **Dependências:** nenhuma.
- **Propaga por:** só código.

### R2-05 — Rótulos de versão inconsistentes nos artefatos do kit

- **Status:** planejado
- **Origem:** P5/IP-003. Após migrar para 4.2.1, o `.sdd/README.md` continua com o título
  `(v3)`; o `.migration-todo.md` abria com `Migration TODO — -> v4.2.1`, versão de origem em
  branco; as tarefas eram numeradas 4, 6 e 7 sem explicar onde estavam 1 a 3 e 5.
- **Evidência:** `content/sdd/README.md:1` (`# SDD — Spec-Driven Development (v3)`);
  `cli.py:1833` (`# Migration TODO — -> {KIT_VERSION}`, sem versão de origem).
- **Causa raiz:** rótulo escrito à mão no template; a origem da migração não é passada ao
  gerador do TODO; a omissão de tarefas desnecessárias só é explicada no cabeçalho.
- **Solução provável:** derivar o título do README da versão do kit (ou removê-lo); passar a
  versão de origem ao gerador (`v3.2.0 -> v4.2.2`); acrescentar uma linha "Tarefas 1–3 e 5
  omitidas: precondição já satisfeita".
- **Riscos e testes:** o README é arquivo gerenciado; o título muda o hash em todos os
  projetos (esperado, entra no `update`).
- **Dependências:** nenhuma.
- **Propaga por:** `sdd update` e código.

### R2-06 — `.migration-todo.md` esquecido e sem aviso

- **Status:** planejado
- **Origem:** P3. Depois de migrar para 4.2.1, o `.migration-todo.md` continua com as tarefas
  4 (enxugar `Current state`), 6 (normalizar codificação) e 7 (reconciliar índices) abertas,
  sem que nada no `doctor` indique que a migração não terminou.
- **Evidência:** `cli.py:1815-1833` gera o arquivo; nenhum finding em `_findings.py` o
  menciona (busca por `migration` só encontra o gerador e o texto de ajuda).
- **Causa raiz:** o CLI é deliberadamente "burro" e delega o restante da migração a um agente;
  não há sinal de que a tarefa ficou pendente.
- **Solução provável:** nota `migration_todo_pending` no `doctor` quando o arquivo existe,
  citando o caminho e a instrução de concluir ou apagar.
- **Riscos e testes:** ruído para quem apagou de propósito não existe (o aviso some com o
  arquivo). Teste: projeto com e sem o arquivo.
- **Dependências:** nenhuma.
- **Propaga por:** só código.

### R2-07 — Saída do `doctor` sai com `�` no console do Windows

- **Status:** planejado
- **Origem:** P5/IP-005. Ao rodar `sdd doctor` pelo Bash de um agente no Windows 11, o
  travessão e o `§` saíram como `�`, enquanto o próprio relatório afirmava "no mojibake
  detected" (a checagem olha os arquivos de `.sdd/`, não a saída do comando).
- **Evidência:** nenhuma chamada a `reconfigure`, `PYTHONUTF8` ou `PYTHONIOENCODING` em
  `src/sdd_cli/`; `main()` está em `cli.py:2994`. Causa não reproduzida nesta avaliação
  (provável: `stdout` na codificação do console).
- **Causa raiz (provável):** o CLI imprime Unicode para um `stdout` que não é UTF-8.
- **Solução provável:** no início de `main()`, `sys.stdout.reconfigure(encoding="utf-8",
  errors="replace")` (idem `stderr`), protegido para streams sem `reconfigure`.
- **Riscos e testes:** `sdd` encadeado com `head` (BrokenPipe, já tratado em `main()`);
  teste com stream cp1252 simulado.
- **Dependências:** nenhuma.
- **Propaga por:** só código.
