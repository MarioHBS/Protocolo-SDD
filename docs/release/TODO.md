# TODO — sdd-cli 4.9.6

## Items

- [x] F-01 — instalador grava LF; `.gitattributes` do repositório
- [x] F-02 — nota `eol_crlf`; `fix --eol` cobre shims e ignora os backups
- [x] F-03 — testes com pacote em CRLF
- [x] TK-01 — `track close` preserva `State:` e `Last updated:`
- [x] TK-02 — `CLOSED (data) — texto` conta como fechada
- [x] TK-03 — `--archive` lista links; nota `track_link_stale`
- [x] TK-04 — `evaluate` não conta `_closed/`
- [x] H-05 — `hooks install`/`uninstall --dry-run` e aviso de arquivo versionado
- [x] D-01 — nota `weight_column_missing` (só projeto que audita)
- [x] D-02 — `doctor --all`
- [x] D-03 — raiz do projeto acima da pasta atual (`doctor`, `context`)
- [x] D-04 — conselho de worktree por pilha
- [x] D-05 — `session_branch_merged`
- [x] B-01 — `constitution_oversized` mede o que a sessão lê
- [x] B-02 — tetos por projeto nas Settings
- [x] B-03 — `long_table_cell` por seção
- [x] E-01 — `fix --slim`
- [x] E-02 — `doctor --slim`
- [x] `USAGE.md` documenta os comandos e códigos novos

## Gate

- [x] `python -m pytest -q` e `ruff check src tests` verdes; testes novos de cada item
- [x] `doctor` 4.9.1 × 4.9.6 sobre o MESMO estado real dos 10 projetos: só as diferenças previstas
- [x] `fix --slim` em cópia da constituição de P3 e P4: remove só o previsto, deixa backup
- [x] `update` real em cópia do P7 grava LF; `fix --eol --manifest` deixa o `doctor` sem `eol_crlf` nem `manifest_eol_drift`
- [x] `update --dry-run` nos 10 projetos: nada gravado
- [x] `CHANGELOG.md` e `RELEASE-NOTES.md` citam todos os itens; versão em `pyproject.toml` e `content/VERSION`
- [x] `docs/release/NOTES.md`
- [ ] tag `v4.9.6`, fast-forward `main`, push de branch, tag e `main` (só com confirmação do dono)
