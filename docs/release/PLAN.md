# Plan — sdd-cli 4.8.0

**Branch:** `4.8.0` (from `main` = 4.7.0) · **Language:** Portuguese

Tema: o que o kit muda chega ao projeto de forma visível (`update` explica, `fix` ajuda, `doctor`
avisa) e a spec só trava depois de uma auditoria fria registrada, proporcional ao peso da etapa.

Origem: estágios 17 (4.7.1) e 18 (4.8.0) do plano privado, priorizados pelo dono em 2026-11-13 a
partir da avaliação dos 9 projetos monitorados. **A 4.7.1 foi absorvida: não haverá tag 4.7.1.**
A automação por hook passa a ser a 4.9.0.

## Estado atual do código (conferido em 4.7.0)

- `update` imprime só `updated <arquivo>`; o `CHANGELOG.md` não vai no pacote (`pyproject.toml`
  empacota `src/sdd_cli`), então não há de onde ler notas de versão.
- `fix` não tem backup e nenhuma função reescreve o §5; `_index_checks.py` é só leitura.
- Nenhum código referencia `~/.claude`; a skill global `sdd` do usuário continua em "(v3)".
- Nenhum provedor escreve arquivo de subagente; `_install_shim` já preserva arquivo existente.
- O passo 6 de `sdd-specify` só diz "se houver subagentes, delegue"; o `doctor` não olha `Status: locked`.
- `MANAGED_DIRS = ("skills", "templates")`: skill e template novos entram no `update` sem mudar código.

## Itens (U = update, S = portão de travamento)

- **U-02** notas de versão em `content/RELEASE-NOTES.md`; `update` imprime as da faixa
  instalada → nova (também no `--dry-run`); `update --notes` relê sem atualizar.
- **U-03** `fix --weight` (opt-in): acrescenta a coluna `Weight` vazia ao §5 canônico e à fila,
  idempotente, com `--dry-run` e backup em `.sdd/.pre-fix-backup/`.
- **U-04** texto: critério de `light` verificável (arquivos tocados, sem teste novo, sem
  contrato/dado/segurança) e reavaliação do peso da fila ao fechar etapa.
- **U-05** `doctor` nota `global_skill_stale`; `update --global-skill` regrava a skill global a
  partir de `content/shims/claude-global-skill.md`, com backup.
- **S-01** skill `sdd-audit` (contrato: somente leitura, livro de verificação, lentes genéricas,
  veredito de dois valores) e agente `.claude/agents/sdd-audit.md` (nome diferente do agente local
  do P2, `sdd-spec-lock`, para não colidir); lentes do projeto em `.sdd/audit-lenses.md`.
- **S-02** `templates/audit.template.md` + protocolo de rodadas (delta), regra de correção do autor,
  registro de premissas com prova.
- **S-03** linha `Locked-by-audit:` no cabeçalho da spec; `doctor`: `lock_without_audit` (note) e
  `lock_audit_mismatch` (warn), só em etapa não fechada; `sdd-close` copia as contagens ao `report.md`.
- **S-04** o peso decide a revisão: `light` = revisão básica; `full` ou vazio = auditoria;
  gatilhos em `audit-lenses.md`; `light_hits_audit_trigger` (warn) no `doctor`.
- **S-05** seção opcional "To measure before implementing" no §6 do modelo da spec.

## Decisões

1. Um vocabulário de peso só: `Weight` da 4.7.0 (não há `Peso: comum | pesada`).
2. Sem retroatividade: o `doctor` nunca cobra etapa fechada; etapa em curso sem a linha é só `note`.
3. O agente fino só existe para o Claude Code; os demais provedores seguem a skill em modo frio
   (o relato diz que a auditoria foi própria, mais fraca).
4. Arquivos de fora do projeto (skill global) só mudam com `--global-skill`, nunca por padrão.

## Riscos e testes

- `fix --weight` reescreve tabela do dono: só com backup, idempotente, fixture com e sem a coluna.
- O `doctor` lê `~/.claude`: somente leitura, silencioso se ausente; a suíte isola `Path.home()`.
- Colisão de agente: `update` em cópia do P2 não toca `.claude/agents/sdd-spec-lock.md` nem `CLAUDE.md`.

## Propaga por

`sdd update` (skills, templates, shims, agente) e código (`cli.py`, `_index_checks.py`, `providers.py`).
