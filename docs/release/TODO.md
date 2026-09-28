# TODO — Implementação sdd-cli 4.2.0

> Notas públicas de versão. Os projetos reais em que o kit foi avaliado aparecem como `P1`, `P2`… (ver a branch `roadmap`, `docs/roadmap/01-EVIDENCIA.md`).

Fontes: a lista de itens adiados do mantenedor, a lista de melhorias do mantenedor,
o TODO da 4.1.0 (pendências herdadas) e as propostas dos projetos reais
(P1 `improvement-proposals.md`, P2 `improvement-proposals.md`).

Branches: `4.2.0` e `4.2.1` (a 4.2.1 continua a 4.2.0; ver o TODO da 4.2.1). Ambas mescladas em `main` e publicadas em 2026-09-23.
Legenda: `[x]` feito e verificado · `[ ]` pendente · `[~]` feito com ressalva.

## Estado verificado (2026-09-23)

- `py -3.12 -m pytest -q`: 171 passed; `ruff check src tests` verde (ruff instalado hoje).
- `VERSION`, `pyproject.toml` e CHANGELOG em 4.2.0 (`[4.2.0] — Unreleased`).
- `main` está igual a `origin/main` (o push da 4.1.0 e dos fixes de P1 já foi feito).
  A branch `4.2.0` não existe no remoto.

## Feito

- [x] `sdd-discover` + `sdd init PATH --discovery FILE.json` (schema `sdd-discovery/v1`, prévia e confirmação).
- [x] `sdd migrate --edd-source-of-truth` (prévia, idempotente; stages ambíguas só reportadas).
- [x] Templates EDD com `evals.md` como fonte única dos `E-NNN` (P1 IP-005).
- [x] `sdd dashboard --ui web [--out FILE]`: HTML estático, sem servidor (P1 IP-010).
- [x] `sdd migrate --dry-run` só anuncia remoção de shim byte-idêntico (P2 IP-002); testes.
- [x] `.markdownlint.json` na raiz do repo e na pasta de trabalho do mantenedor (mesmas regras de P2).
- [x] Notas atualizadas; IPs de P1 e de P2 marcados como absorvidos.

## Pendências herdadas da 4.1.0 (auditadas: nunca foram feitas)

- [x] **Decisão do dono (C7), 2026-09-23:** e-mail `developer.mario.santos@gmail.com` mantido no `pyproject.toml`; `sdd evaluate` / `.sdd/kit-evaluation/` fica na versão (já existe em código, teste e manual).
- [x] Fixtures sintéticas de v1 (sem manifesto, `?`) e v2 (dupla codificação, aborta sem escrever e repara com `--fix-mojibake`) em `tests/test_migrate.py`.
- [ ] Rodar `sdd update` no **P1 real** (manifesto ainda em v4.1.0) e depois `sdd fix --links --features`
  (P2 já está com manifesto v4.2.0; conferir se o `fix` foi rodado lá).
- [ ] Limpar o `SDD-USAGE.md` solto na raiz de P1 (remover, mover para `.sdd/` ou ignorar).
- [~] Sessão interativa humana do dashboard `interactive` em terminal real (só validado com Pilot, sem TTY).
- [~] `### Active tracks` não é atualizado por `sdd track incorporate` (formato da tabela é do dono; o comando só lembra).
- [x] `sdd document` pergunta diretamente "há dinheiro, saúde ou regulação?"; a resposta vence a heurística (que segue como fallback em `--answers`).

## Ainda a fazer nesta versão

- [x] `ruff check src tests` (comando da CI): verde.
- [x] Instalação local (`pip install --user -e ".[dashboard]"`) refeita: `sdd --version` e metadados do pip em 4.2.0, com `--ui web`.
- [x] Merge em `main` (`--no-ff`, 4.2.0 e 4.2.1) e push de `main`, `4.2.0` e `4.2.1` para o `origin`, autorizados em 2026-09-23.
- [x] Branches `4.2.0` e `4.2.1` publicadas no `origin`.
- [ ] Após o merge: `sdd migrate --edd-source-of-truth` nos projetos reais com EDD (P1) e conferir a prévia.

## Adiado (registrado em `ADIADOS-SDD-CLI.md`, com gatilho)

- Contingência de orçamento por `Origin`; `sdd fix --index`; arquivar linhas de `estimates.md`/`roadmap.md`.
- Dashboard com servidor local ou GUI nativa (`tkinter`).
- README do kit em cartão + referência; guarda por hook e modo worktree; trilha "em espera".
- `ws doctor`, type-check, matriz de migradores, distribuição PyPI/npm, remoção do alias `sdd docs` (5.0).

## Registro de progresso

- 2026-09-23 — 4.2.0 implementada em branch: discovery, EDD como fonte única, dashboard web, fix do dry-run do migrate.
- 2026-09-23 — pergunta direta de risco no `sdd document`, fixtures v1/v2, C7 decidido, ruff verde, instalação local atualizada.
- 2026-09-23 — 4.2.1: `sdd discover` (explica o fluxo, caminho do skill, `--check`, `--against`), skill com as escolhas de instalação, shims/README citando `sdd-discover`, correção do `sdd update` (hash ignora CRLF/LF).
