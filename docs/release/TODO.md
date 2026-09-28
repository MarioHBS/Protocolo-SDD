# TODO — Implementação sdd-cli 4.1.0

> Notas públicas de versão. Os projetos reais em que o kit foi avaliado aparecem como `P1`, `P2`… (ver a branch `roadmap`, `docs/roadmap/01-EVIDENCIA.md`).

Fonte: `C:\Users\Windows\.claude\plans\avalie-os-dois-projetos-staged-pond.md`.
Branch: `4.1.0` (local; sem push; merge em `main` só com aprovação).

Reescrito em 2026-09-21 após auditoria e **atualizado ao fim da implementação**.
Legenda: `[x]` feito e verificado · `[ ]` pendente · `[~]` feito com ressalva.

## Estado final verificado

- Estado **commitado** (extraído com `git archive HEAD`, sem depender do working tree):
  154 testes passam (2 pulados: dashboard sem extras); com os extras instalados, **156 passam, 0 pulados**.
- `ruff check src tests` (o comando da CI): verde, com as regras fixadas em `pyproject.toml`.
- Lint Markdown (regras obrigatórias do kit) sem achados no conteúdo do kit, USAGE e README.
- `sdd --version` = `sdd v4.1.0`; `VERSION`, `pyproject.toml` e CHANGELOG coerentes.
- Árvore limpa: 18 commits em `main..4.1.0`, um por tópico.

## Correções da auditoria

- [x] C1 — `sdd context` com `Active stage` em prosa (P2: `Etapa 091 (…)`): resolve pela pasta, sem erro; teste.
- [x] C2 — `context --budget` conta só o cabeçalho da constituição (+ shim do provider) como startup: P2 ~25,6k → ~5,2k tokens; P1 ~11,9k → ~4,7k.
- [x] C3 — ruff verde; regras fixadas no `pyproject.toml`; `NameError` de `_STALE_TRACK_DAYS` era código morto (scanner removido).
- [x] C4 — Shim do Kilo: título restaurado.
- [x] C5 — CHANGELOG: `[4.0.0]` fechado e reposicionado; `[4.1.0]` escrito (Added/Changed/Fixed/Deferred).
- [x] C6 — Dashboard: views reais, EDD com ID da eval e agrupado por stage, painel Doctor com o comando de correção.
- [ ] C7 — **Decisão do dono:** e-mail no `pyproject.toml` (hoje `developer.mario.santos@gmail.com`, trocado numa sessão anterior; o plano mandava perguntar por ser metadado publicável) e se `sdd evaluate` / `.sdd/kit-evaluation/` (fora do plano original) fica na 4.1.0.
- [x] C8 — MELHORIAS reescrito: CI só consta como resolvida depois de o ruff ficar verde; #12 (idioma) implementado.

## Implementação

### B0 / B8 — Release

- [x] CHANGELOG `[4.1.0]` com seção Deferred; job de dashboard na CI (instala `.[dashboard]`, falha se algum teste for pulado; YAML validado).
- [x] Merge em `main` (feito depois; ver "Para decidir"); `main` já está no `origin`.

### B1 — Dieta de contexto

- [x] Shims (leitura até `## 1.`), README com política hot/cold, template do §5 sem colunas Spec/Report e sem links, templates de estimates/roadmap com limites, `sdd context`, diagnósticos de tamanho/links/duplicidade/deriva.
- [x] `sdd fix --links` agora escreve links **relativos a `.sdd/`** (a versão anterior era relativa à raiz do projeto, ou seja, quebrada a partir de `constitution.md`); idempotente; trata checkout de outra máquina (`/.sdd/`).

### B2 — Absorção das propostas

- [x] README lista EDD, backlog, cross-cutting e `documentation.json`.
- [x] Skills: `sdd-specify` (Origin, Touches, cross-cutting, `evals.md` como fonte única, estados `[-]`/`[!]`, backlog), `sdd-implement` (gate de escopo, footprint, `seq next`, eval no meio da stage), `sdd-close` (fonte única, `verify` + `incorporate`, narrativa fora do §5/§6, `documentation.json`), `sdd-roadmap` (footprints disjuntos, linha ≤ 3 frases), `sdd-reconcile` (backlog, marcos, trilhas), `sdd-init` (auditoria de credenciais na adoção).
- [x] `doctor`: `edd_milestone_without_evaluation`, `milestone_not_contiguous`, `backlog_orphan`, `queue_row_without_section` (módulo `_index_checks.py`; sem falso positivo em P1).
- [x] Templates: `cross-cutting.template.md`, `backlog.template.md` (uma seção por slug), `spec.template.md` (Touches; gate de escopo reposicionado), `track-state.template.md`.
- [x] Mensagem do dashboard com fallback e INSTALL com extras (IP-003).

### B2b — Trilhas

- [x] `_lock.py`; `sdd track incorporate` atômico (próximo `NNN` por disco + §5 + ledger; preserva CRLF); teste de **3 incorporações concorrentes** em subprocessos → números distintos.
- [x] Sobreposição por segmentos de caminho (sem falso negativo com `**/x`, sem `src/comp` × `src/components`); `verify` vê arquivos não rastreados, ignora o trabalho de trilha irmã e acusa arquivo claimado por duas; trilhas concluídas não entram no `check`.
- [x] `sequence_duplicate`, `session_branch_mismatch` (sessão grava `branch`), sequências declaradas no §7 (placeholder comentado não conta).
- [x] `sdd fix --gitignore` (opt-in), `nested_worktree_copies` com dica; linha "worktree linkado" nos 9 shims.
- [x] `sdd-track` reescrito; gates em specify/implement/close/roadmap.
- [~] `### Active tracks` **não** é atualizado pelo `incorporate` (o comando imprime o lembrete): o formato da tabela é do dono.

### B3 — Robustez

- [x] Handler de exceção em `main()`; `_detect_language` case-insensitive por pontuação (`tests/test_language.py`).

### B4 — `sdd document`

- [x] Entrevista completa (profundidade recomendada por sinais reais, público, custo do erro, idioma, pasta-base fora de `.sdd/` e fora do projeto só com confirmação, lista editável, numeração/cabeçalho, `covers` por documento, adoção de docs existentes).
- [x] `--resume` (estado salvo a cada passo), `--answers FILE`, `--dry-run`, falha clara sem TTY; `documentation.json` + feature ligada na constituição **e** no manifesto + nota no §7 (idempotente, preserva CRLF); stubs sem sobrescrever.
- [x] `doctor`: `docs_missing_file`, `docs_missing_header`, `docs_path_outside_project`; `sdd init --docs` oferece a entrevista; skill `sdd-document` conduz o CLI.
- [x] Exercitado **de verdade** numa cópia de P1 (interromper, retomar, stubs, `doctor`).
- [~] Heurística de risco é vocabulário da visão/decisões (§1–§3): sugestão que o usuário confirma; registrada em ADIADOS.

### B5 — Help e docs

- [x] `--help` com descrição e exemplos em todo comando e subcomando, agrupado por propósito; `USAGE.md` reescrito (todos os comandos, códigos do `doctor`, códigos de saída); INSTALL pt-BR/es/en (Python 3.12, extras do dashboard).
- [x] `tests/test_help_docs.py`: comando sem doc, opção sem `help`, exemplo que não parseia e código de `doctor` ausente do manual **falham a suíte**.
- [x] **`sdd doctor` humano lista todos os achados** (antes dizia "clean." com problemas no `--json`).

### B6 — Dashboard (gate)

- [x] Views reais (rich, textual, plain); erro explicado sem extras; textual sem terminal recusa em vez de travar.
- [x] Gate em venv limpa: `pip install '.[dashboard]'` (e cada extra isolado), `pytest` sem pulos, rich e Textual (Pilot, 6 abas) nas cópias de P2 e de P1; evidência arquivada fora deste repositório.
- [~] Sem sessão interativa humana num terminal real (ambiente sem TTY) — descrito no README da evidência.

### B7 — Testes

- [x] `test_init.py`, `test_migrate.py` (v3.3.0 → v4 no formato de P2; `update` 4.0.0 → 4.1.0), `test_main.py`.
- [ ] Fixtures sintéticas de v1 e v2 para `migrate` (registrado em MELHORIAS/ADIADOS).

## Smokes nas cópias dos projetos reais

- [x] P2: `migrate --to v4 --dry-run` deixa tudo byte-idêntico; migrate real só troca arquivos gerenciados (README, skills, templates, manifesto, `.migration-todo.md`); `fix --links` idempotente; `doctor`: `track_not_started` 5 → 1.
- [x] P1: `update --dry-run` idem; `update` atualiza 18 arquivos, adiciona 3 templates e não toca em constituição, backlog, `improvement-proposals.md`, roadmap, estimates, CHANGELOG nem stages.
- [x] `context --budget` e `doctor` conferidos nos dois; conteúdo do kit sem mojibake.

## Documentos (fora do repo)

- [x] `HISTORICO-VERSOES-SDD-CLI.md`, `AVALIACAO-PROJETOS-REAIS-2026-09-21.md` (com resultado medido), `MELHORIAS-SDD-CLI-2026-08-31.md` (limpo, só pendências), `ADIADOS-SDD-CLI.md`, `evidencia-dashboard-4.1.0/`.

## Adiado (registrado em `ADIADOS-SDD-CLI.md`)

- `sdd-discover` (4.2.0), `sdd fix --index` (enxugar §5 existente), arquivar linhas de estimates/roadmap, README do kit em cartão + referência, guarda por hook e modo worktree, `track` "em espera", pergunta direta de risco no `sdd document`, `ws doctor`, type-check, matriz de migradores, distribuição PyPI/npm, remoção do alias `sdd docs` (5.0).

## Para decidir / fazer a seguir

- [x] `4.1.0` mergeada em `main` (commit `0b9dad3`, merge --no-ff) e `4.1.0` avançada até ele; **push ainda não feito** (`origin/main` está em `7f7eb66`, `origin/4.1.0` só tem o primeiro commit).
- [ ] C7 acima (e-mail; `sdd evaluate`) — transferido para o TODO da 4.2.0.
- [ ] Depois do merge: rodar `sdd migrate --to v4` / `sdd update` nos projetos **reais** (não nas cópias) e `sdd fix --links --features` — P2 já está em v4.2.0; P1 segue em v4.1.0 (transferido para o TODO da 4.2.0).
- [ ] Fixtures v1/v2 — transferido para o TODO da 4.2.0.

## Registro de progresso

- 2026-09-21 — TODO reescrito após auditoria.
- 2026-09-21 — C1–C8, B0–B7 implementados, smokes e gate do dashboard executados; documentos atualizados.
- Ressalva de histórico: o commit `5264c48` (dashboard) isoladamente tem 1 teste de dashboard falhando (`projeto sem .sdd`) — a guarda correspondente entrou no commit seguinte (`f5fc529`); do `f5fc529` em diante tudo passa.
