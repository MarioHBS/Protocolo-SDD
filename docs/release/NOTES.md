# Notes — sdd-cli 4.7.0

- 365 testes passam (linha de base na 4.6.0: 343); `ruff` limpo. Testes novos em
  `tests/test_stage_weight.py` (leitura do peso, texto das skills, fixture com etapa `light` e etapa
  `full` lado a lado no `doctor`) e em `tests/test_index_checks.py` (peso nas duas tabelas, alias em
  português, índice sem a coluna, justificativa obrigatória).
- Decisões do W-01 (as três questões que o `PLAN.md` deixou abertas):
  1. nome canônico `Weight` com valores `light` / `full`; `Peso`, `leve` e `completo` são aceitos como
     alias na leitura. Valor desconhecido, inclusive erro de digitação, lê como `full`: só `light`
     relaxa algo, então errar cai sempre no lado rígido.
  2. a justificativa fica na própria célula (`light: corrige um typo`; `—` e `-` também separam). Assim
     o `doctor` pode exigir que exista (`weight_light_without_reason`) sem depender de `Notes`, que só a
     fila tem.
  3. com EDD desligado, `light` não relaxa nada mecânico: o `sdd-specify` aceita spec curta, mas
     critérios de aceite e a verificação de verdade do `sdd-close` não saem.
- W-02 relaxa um único check: `edd_missing_checklist` não dispara numa etapa `light` fechada quando o
  `report.md` já cobre todo `E-NNN` do `evals.md`. `edd_missing_evals` e `edd_eval_uncovered` seguem
  iguais; uma etapa `full` é checada como antes.
- **Defeito achado e corrigido durante a verificação:** a primeira versão do `edd_no_criteria` olhava só
  `E-NNN`. O LSDI numera os critérios `E1`…`E7`, e o check acusaria 8 etapas que têm critérios. Os
  checks de EDD antigos eram cegos a esse formato (nunca acusavam nada ali). O `edd_no_criteria` agora
  aceita qualquer id `E1` / `E-01` / `E-001`. Os checks de cobertura (`edd_eval_uncovered`) continuam só
  com `E-NNN`, como antes; mudar isso fica fora desta release.
- Verificação com o wheel 4.7.0 em venv limpo, sobre cópias (só `.sdd/`, `CLAUDE.md`, `AGENTS.md`,
  `.claude/`) dos 7 projetos reais com `.sdd/` em disco:
  - `doctor --json` da 4.6.0 e da 4.7.0 têm exatamente os mesmos códigos de finding nos 7 projetos
    (depois da correção acima; antes dela o LSDI diferia).
  - `update --dry-run`: nada foi escrito nas 7 cópias (hash de todos os arquivos antes e depois) e a
    `constitution.md` não aparece em nenhuma lista, então o §5 e as etapas fechadas ficam intactos. O KNN
    (4.5.0) atualizaria 5 skills, e `todo.template.md` editado à mão seria preservado.
- Nenhum projeto real tem a coluna `Weight`; o caminho `light` foi exercitado só pelas fixtures.
  Como o plano já avisava, esta capacidade nasceu de inspiração externa (BMAD), sem episódio real nos
  projetos avaliados: quem decide se compensa é a avaliação depois do uso.
- Pendente do dono: tag `v4.7.0`, fast-forward de `main` e os pushes (branch, tag e `main`).
