# Notes — sdd-cli 4.9.6

## Verificação

- `python -m pytest -q` e `ruff check src tests`: verdes (604 testes, 89 a mais que os 515 da 4.9.1, nos arquivos
  `test_slim.py`, `test_eol_origin.py`, `test_track_writes.py`, `test_doctor_blind_spots.py` e
  `test_constitution_budget.py`). Rodados com CPython 3.12 (`py -3.12`): o código usa f-strings
  aninhadas (PEP 701).
- **`doctor` 4.9.1 × 4.9.6 sobre o MESMO estado real dos 10 projetos** (2026-11-20; 4.9.1 = `sddkit`
  instalado, 4.9.6 = código da branch): status de saída 0 nos 10, antes e depois. Diferenças, todas
  previstas:
  - `eol_crlf` (note) entra em P1, P3, P4, P5, P7, P8, P9 (os que têm arquivo do kit em CRLF).
  - `weight_column_missing` (note) entra em P2, P3, P4, P10 (os que têm `audit.md` e não têm a coluna).
  - P3 e P4: `constitution_oversized` (warn) sai (a parte lida no início tem 3,6 e 2,3 KB) e entra
    `cold_file_oversized` (note) para `.sdd/constitution.md`. `long_table_cell` do P3 só ganha campos.
  - P2: `track_link_stale` (note, 5 links nos índices vivos) e os 3 `cold_file_oversized` ganham o limite.
  - P5: `nested_worktree_copies_ignored` sai (o `analysis_options.yaml` já exclui `.kilo/worktrees`).
  - P10: `session_branch_mismatch` (warn) vira `session_branch_merged` (note).
  - P4, P8 e P9 (kit 4.9.1) ganham `kit_behind` pelo bump; os outros sete só mudam o texto da versão.
- **`update --dry-run` nos 10 projetos**, com sha1 de `.sdd/`, `.claude/`, `.github/`, `.kilo/` e dos
  `.md` da raiz antes e depois: nenhum arquivo mudou; os 10 mostram "Would bump kit_version -> v4.9.6".
- **`update` real em cópia do P7** (só `.sdd`, `.claude`, `.agents` e os `.md` da raiz): os arquivos que
  o `update` reescreve saem em LF (31 → 28 arquivos em CRLF); os que ele não toca seguem em CRLF até
  `fix --eol`. Em outra cópia, `fix --eol --manifest` deixou o `doctor` sem `eol_crlf` nem
  `manifest_eol_drift`.
- **`fix --slim` em cópia da constituição de P3 e P4:** P3 64.829 → 63.191 B (7 comentários); P4
  31.254 → 31.124 B (1 comentário; 130 B reais porque o arquivo está em CRLF). Backup byte a byte igual
  ao original; segunda execução não encontra nada.
- Comentários de template recuperáveis (só `--dry-run`): P1 1.345 B, P2 125, P3 1.620, P4 125, P5 e P6
  479, P7 0, P8 e P9 1.722, P10 0.

## Decisões tomadas ao implementar

- **B-01 seguiu a opção recomendada** sem esperar o dono (o pedido foi "todas as melhorias"); limite
  quente de 8 KiB escolhido aqui. Se o dono preferir a opção 2 (manter o limite no arquivo inteiro), é
  uma mudança pequena em `cli.py` (bloco da constituição no `doctor`).
- **D-01 só avisa projeto que audita.** O template novo não traz a coluna `Weight`, então avisar todo
  projeto sem ela (8 de 10) seria ruído e o `init` já nasceria com a nota.
- **`track-state.template.md` ficou como na 4.9.1.** Corrigir o comentário do cabeçalho fez o `doctor`
  acusar `managed_file_edited` (warn) no P2, cuja cópia é idêntica à do kit antigo mas tem hash antigo no
  manifesto (família do IP-018). Revertido (commit `revert(template)`); o comportamento está no
  `USAGE.md`. Fica pendente para quando o IP-018 for tratado.
- TK-03 só lista os links, não os reescreve; TK-04 corrige o contador sem mudar a saída do `evaluate`;
  `hooks uninstall` também ganhou `--dry-run` (pequeno, mesmo código).
- `fix --eol` passou a cobrir os arquivos gerenciados fora de `.sdd/` (shims), porque a nota `eol_crlf`
  os conta; a dica manda `fix --eol --manifest` para não deixar `manifest_eol_drift`.

## Não verificado

- Se o pacote publicado (CI no Linux) já sai em LF; a correção vale nos dois casos.
- `hooks install --dry-run` não foi disparado no Claude Code real; o aviso de arquivo versionado usa
  `git ls-files` e `git check-ignore`.
- Nenhum agente seguiu ainda a instrução do `doctor --slim` (nenhum texto foi movido); o `--slim` do
  `fix` recupera pouco e não tira P3 nem P4 do estado de "constituição grande" (agora uma nota).
- TK-02: a reprodução do P4/IP-002 depende de a trilha ainda constar em `Active tracks`; coberto por
  teste de fixture, não reproduzido no P4 (já corrigido à mão).
- A 4.9.6 foi construída com o `sddkit` local em CRLF; reinstalar a partir desta branch para o pacote
  local sair em LF (o instalador já normaliza de qualquer forma).
- Não publicada: sem tag, sem merge em `main`, sem push.
