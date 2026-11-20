# Plan — sdd-cli 4.9.6

**Branch:** `4.9.6` (de `main` = 4.9.1) · **Idioma:** português

Tema: uma release só com tudo o que a vistoria de 2026-11-20 (dez projetos reais) planejou para as
versões 4.9.2 a 4.9.6. Por decisão do dono, os números 4.9.2 a 4.9.5 ficam sem uso e o conteúdo dos
estágios 22, 24, 25, 26 e 27 do plano privado entra aqui. Isso foge da regra de "um tema por
release" (`00-METODO.md`); o risco é de regressão maior, e por isso o gate roda o `doctor` 4.9.1 ×
4.9.6 sobre o mesmo estado real dos 10 projetos.

## Itens

### Fim de linha (estágio 24)

- **F-01** o instalador grava LF (`_install_file`) e o repositório fixa `eol=lf` (`.gitattributes`).
  Causa medida: pacote construído de checkout Windows com `core.autocrlf`, 44 de 46 arquivos de
  `content/` em CRLF; `update` copiava bytes.
- **F-02** nota `eol_crlf` no `doctor`; `fix --eol` cobre shims gerenciados e ignora os dois backups.
- **F-03** testes com um pacote em CRLF (fixture), arquivo intacto continua intacto.

### Escrita segura em trilhas e hooks (estágio 25)

- **TK-01** `track close` preserva o texto de `State:` e `Last updated:` (linha `Previous ...`),
  mantém estado já fechado em prosa, `--dry-run` mostra o diff.
- **TK-02** `CLOSED (data) — texto` conta como fechada.
- **TK-03** `--archive` lista os links que ficaram; nota `track_link_stale` nos índices vivos.
- **TK-04** `evaluate` não conta `_closed/` como trilha.
- **H-05** `hooks install`/`uninstall` com `--dry-run`; avisa arquivo versionado e sugere `--local`.

### `doctor` sem ponto cego (estágio 26)

- **D-01** nota `weight_column_missing`, só em projeto que audita (algum `audit.md`).
- **D-02** `doctor --all`: toda ocorrência de achado repetido; `mojibake_v1` com linha:coluna e trecho.
- **D-03** `doctor` e `context` sobem até o `.sdd/` mais próximo.
- **D-04** conselho de `nested_worktree_copies_ignored` por pilha; some quando a config já exclui.
- **D-05** sessão com branch já mesclada vira nota `session_branch_merged`.

### Orçamento da constituição (estágio 27)

- **B-01** `constitution_oversized` mede o que a sessão lê (Settings + Current state, 8 KiB); o resto
  é nota `cold_file_oversized` (24 KiB) com os dois tamanhos.
- **B-02** tetos por projeto nas Settings (`Constitution max size`, `Cold file max size`).
- **B-03** `long_table_cell` aconselha por seção (§3 e §6 → CHANGELOG, §5 → backlog).

### Enxugar a constituição (estágio 22)

- **E-01** `fix --slim` (só comentário idêntico ao do template; recupera 0 a 1,7 KB).
- **E-02** `doctor --slim` (só leitura): bytes por seção, linhas acima de 600 B com destino, instrução.

## Decisões

1. **B-01 sem esperar o dono:** o dono pediu "todas as melhorias" e o B-01 estava pendente; seguiu-se
   a opção recomendada no plano (medir só o que a sessão lê). Severidade do aviso quente continua
   `warn`; o tamanho total vira nota.
2. **Limite quente de 8 KiB** (escolhido aqui; o plano não fixava o número): os 10 projetos têm de 0,8
   a 3,7 KB nessa parte.
3. **D-01 só para quem audita:** o template novo não traz a coluna `Weight` (ela é opcional); avisar
   todo projeto sem a coluna seria ruído (medido: 8 de 10 não têm). A nota fica para os que têm
   `audit.md` (P2, P3, P4, P10).
4. **Template `track-state.template.md` não foi alterado** (o plano mandava corrigir o cabeçalho): mudar
   um arquivo gerenciado faz o `doctor` acusar `managed_file_edited` em projeto cuja cópia é igual à
   do kit antigo mas tem hash antigo no manifesto (P2, família do IP-018). Documentado no `USAGE.md`.
5. **TK-03 só lista**, não reescreve links (texto histórico não se reescreve); **TK-04 só corrige o
   contador**, sem mudar o formato da saída do `evaluate`.
6. **Idioma das linhas novas:** `Previous state:` / `Previous update:` (o kit é em inglês).
