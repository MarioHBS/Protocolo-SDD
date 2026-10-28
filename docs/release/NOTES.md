# Notes — sdd-cli 4.5.0

- 328 testes passam; `ruff` limpo. Testes novos: aviso do alias e entry points (`test_main.py`) e o
  guarda de nome (`test_cli_name.py`).
- Nome decidido pelo dono em 2026-10-28: `sddkit`. Livre no npm e no PyPI na mesma data; `sdd-cli`
  está ocupado no npm (`npx sdd-cli` executaria código alheio). A distribuição continua `sdd-cli` e
  nada foi publicado nem reservado (N-05 segue aberto).
- Wheel 4.5.0 em ambiente limpo (venv novo): `sddkit.exe` e `sdd.exe` são instalados e respondem
  `sddkit v4.5.0`. Só `sdd` escreve o aviso em `stderr`; `sddkit` e `python -m sdd_cli` não escrevem
  nada. A saída de `doctor --json` é idêntica nos dois nomes (descontado `cli_path`).
- `sddkit update` de um projeto criado pela 4.4.0 mudou só arquivos gerenciados: manifesto, README,
  8 skills, 3 templates e o shim `AGENTS.md`. `constitution.md`, `roadmap.md` e
  `improvement-proposals.md` ficaram intactos; o `--dry-run` não escreveu nada.
- Dry-run no KNN_WAREHOUSE (P1, v4.4.0): lista o shim de `.claude/commands`, o README, 8 skills e 3
  templates, e preserva `todo.template.md` por estar editado à mão. `CLAUDE.md` e
  `.claude/settings.local.json` do KNN têm 0 menções a `sdd <comando>` e a `Bash(sdd`, então nada
  do dono precisa mudar. O KNN estava em uso durante a verificação (backups de dados, build do
  frontend, `checklist.md` da 008), por isso o hash do projeto inteiro não serve de prova; o dry-run
  só lê, e isso foi comprovado no projeto de teste.
- O plano dizia que o N-03 era "uma troca em um lugar". Não é: os textos gerenciados são Markdown
  estático, com 158 ocorrências em 23 arquivos, mais cerca de 130 em `cli.py` e módulos. A troca foi
  mecânica e é protegida por `test_cli_name.py`, que lê os subcomandos reais do parser e falha se
  algum texto gerenciado ou de ajuda voltar a ensinar `sdd <comando>`. O guarda achou 22 exemplos de
  ajuda que a primeira passada tinha deixado (`\n` literal antes de `sdd`).
- Achado de ferramenta: o `sed -i` do Git Bash remove os CRs dos arquivos. A árvore de trabalho
  desta máquina é CRLF (`core.autocrlf=true`) e `test_switching_provider_removes_only_an_untouched_old_shim`
  compara o hash do shim com o do kit, então falha se o arquivo do kit virar LF. Os CRLF foram
  restaurados; o índice do Git é LF e os commits não mudam.
- Fora desta release: N-04 (`doctor` detecta o nome legado, `fix` reescreve) fica para a seguinte, para
  não acusar todos os projetos antes de o alias estar em uso; mesmo assim, `doctor` já sugere
  `sddkit fix --links` nas mensagens novas.
- Já existia e não foi tocado: `abs_file_links` acusa a frase "`file:///` links here" do próprio
  template da constitution, então todo projeto novo nasce com esse aviso.
