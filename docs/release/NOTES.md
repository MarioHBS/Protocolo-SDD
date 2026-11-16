# Notes — sdd-cli 4.9.0

## Verificação

- `python -m pytest -q` e `ruff check src tests`: verdes (502 testes).
- **Claude Code 2.1.325 real** (`claude -p`, projeto de teste com duas trilhas, `sddkit` da branch no PATH):
  - Edit em `src/app.py`, reivindicado por `left` e `right`: o hook devolveu `ask`; em modo
    não interativo o agente recebeu o motivo e a edição não foi feita.
  - `SDD_TRACK=left`, Edit em `docs/x.md` (fora do footprint): a edição passou e o agente recebeu
    `PreToolUse:Edit hook additional context: track left: docs/x.md is outside ...`.
  - Edit em `.sdd/stages/001-x/report.md`: `PostToolUse:Edit hook additional context: sddkit doctor
    after report.md: 1 error(s), 2 warning(s) (...)`.
  - O caminho do Windows (absoluto, com barra invertida) casa com o claim relativo.
- **Achado do teste real, corrigido antes de publicar:** com um `sddkit` 4.8.2 (sem `hooks`) no
  PATH, `sddkit hooks run` sai com 2 (erro do argparse) e o Claude Code **bloqueou a edição**
  (`PreToolUse:Edit hook error`). A linha registrada agora é `sddkit hooks run <evento> || true`
  com `"shell": "bash"`; repetido com o 4.8.2 a edição passa, e com o 4.9.0 o `ask` continua.

## Não verificado

- Sem Git Bash instalado o hook não roda (`shell: bash`); não há máquina assim para testar.
- `MultiEdit` está no matcher, mas o formato do `tool_input` dele não foi confirmado (usa-se só
  `file_path`).
- `update --dry-run` nos projetos reais: não feito; o `update` não toca em `.claude/settings.json`
  (teste `test_update_never_registers_a_hook`).
- Tag `v4.9.0`, fast-forward de `main` e pushes esperam confirmação do dono.
