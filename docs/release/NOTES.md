# Notes — sdd-cli 4.6.0

- 343 testes passam (linha de base na 4.5.0: 328); `ruff` limpo. Testes novos em
  `tests/test_decision_gate.py` (paridade da lista estrutural entre `sdd-decide`, `sdd-discover` e o
  standalone; perspectivas, busca limitada e ramificação) e em `tests/test_discovery_edd.py`
  (estado `DECIDING`, linhas de §3 como `proposed`, `update` que não mexe no estado, `init` sem
  descoberta que continua em `INITIALIZING`). Os testes de paridade foram conferidos falhando sem a
  mudança.
- A `sdd-discover.standalone` já tinha o texto de G-01, G-04 e G-05 desde o commit `8eb4404`
  (2026-10-02). Esta release levou esse texto para as skills embutidas no CLI e trocou a promessa
  "espelha `sdd-decide`" do standalone por um teste que compara as três cópias. O standalone não foi
  alterado.
- Wheel 4.6.0 em venv limpo: `sddkit v4.6.0`; `sdd` continua avisando em `stderr` e respondendo igual.
- `sddkit update --dry-run` em cópia (só `.sdd/`, `CLAUDE.md`, `AGENTS.md`, `.claude/`), comparando o
  hash de todos os arquivos antes e depois (nada foi escrito):
  - KNN_WAREHOUSE (4.5.0, `SPECIFYING`): atualizaria só `sdd-decide/SKILL.md` e `sdd-discover/SKILL.md`;
    `todo.template.md` editado à mão seria preservado.
  - vaquinha-familiar (P7, 4.3.2, `ROADMAP`): atualizaria o shim, o README, as skills e 3 templates, ou
    seja, só arquivos gerenciados (o salto 4.3.2 → 4.6.0 inclui as releases 4.4 e 4.5).
- **G-02 e uso real de `--discovery`:** das 7 cópias de projeto com `.sdd/` em disco, só a
  vaquinha-familiar tem a marca "Imported from discovery" no `backlog.md`. Ela já passou do portão
  (`ROADMAP`, etapa 025 fechada), então a mudança de estado final do `init --discovery` não a afeta;
  `update` não reescreve a constituição. Nenhum projeto existente é reaberto em `DECIDING`.
- Decisões tomadas no G-02 (as três questões que o `PLAN.md` deixou abertas):
  1. a marca de proposta é o texto `proposed (agreed <data>)` na coluna `Locked on`; ninguém no código
     lê essa coluna (`impact` só procura o id), então não quebrou nada. Sem data no JSON, fica
     `proposed`.
  2. depois do autoaudit, o projeto vindo de descoberta vai direto a `SPECIFYING`, sem passar por
     `ROADMAP`, porque o índice de estágios já veio da descoberta. É o mesmo destino de antes; só o
     portão voltou.
  3. `Active stage: 001-<slug>` continua preenchido em `DECIDING`; nenhum check do `doctor` ou do
     dashboard estranha a combinação. Conferido com o wheel num projeto criado por `--discovery`: `doctor`
     só acusa `abs_file_links`, aviso que já existia (ver as notas da 4.5.0).
- A mensagem final do `init` e o resumo do `--discovery` agora dizem que o projeto começa em
  `DECIDING`; `init` sem descoberta segue dizendo `INITIALIZING`.
- Não há campo novo no `discovery.json` (`sdd-discovery/v1`): `locked_on` continua sendo a data do
  acordo, que o standalone já explicava assim.
- Pendente do dono: tag `v4.6.0`, fast-forward de `main` e os pushes (branch, tag e `main`).
