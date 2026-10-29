# Plan — sdd-cli 4.7.0

**Branch:** `4.7.0` (from `main` = 4.6.0) · **Language:** Portuguese

Tema: o peso de cerimônia é um atributo da etapa (`leve` ou `completo`), não só um interruptor do
projeto. Uma etapa que corrige um typo não paga o mesmo `sdd-close` (EDD) que uma etapa que desenha
uma tabela nova.

Origem: estágio 08 do plano (repo privado), escrito em 2026-10-01. Pedido do dono, inspirado no
"Adaptive Planning" do BMAD Method. **Nenhum item tem episódio real registrado nos projetos
avaliados**: é inspiração externa, não atrito observado. O dono pediu a capacidade mesmo assim; a
avaliação depois de implementada decide se compensa. Os itens abaixo foram reconciliados com o
código desta branch.

## Estado atual do código (conferido em 4.6.0)

- **§5 já tem colunas opcionais.** O plano antigo dizia que o §5 "só tem colunas de etapa, status e
  link". A tabela canônica é `Stage | Slug | Status | Depends on`; a fila provisória é
  `Slug | Status | Depends on | Notes`. Com EDD ligado, o `sdd-roadmap` já acrescenta uma coluna
  opcional `Milestone` (comentário no template e `milestone_findings`). Peso segue o mesmo molde.
- `_index_checks._tables` devolve cada linha como `dict` com os cabeçalhos em minúsculas; uma coluna
  ausente vira `row.get("weight")` vazio. Projeto antigo, sem a coluna, lê tudo como `completo` sem
  tocar em nada.
- **O `doctor` de EDD não olha a "etapa ativa".** O bloco (`cli.py`, em torno da linha 1100) percorre
  todas as pastas de `.sdd/stages/` com `spec.md`. O peso precisa ser buscado por etapa, casando o
  nome da pasta (`NNN-slug`) com a linha do §5 (`_stage_name` já faz esse casamento).
- Os checks atuais, e o que cada um exige hoje:
  - `edd_missing_evals`: etapa com `spec.md` e sem `evals.md`.
  - `edd_spec_not_pointer` / `edd_todo_not_evals`: spec e todo apontam para `evals.md`.
  - `edd_missing_checklist`: etapa **fechada** (`report.md`) sem `checklist.md`, **mesmo que o
    `report.md` já cubra todos os `E-NNN`**.
  - `edd_eval_uncovered`: cada `E-NNN` precisa aparecer em `checklist.md` **ou** `report.md`.
- `sdd-close` (passo 1) já aceita a evidência em `checklist.md` ou no relatório; `sdd-specify`
  (passo 5) cria `evals.md` e `checklist.md` sempre que EDD está ligado.
- Não existe hoje nenhum finding quando `evals.md` de uma etapa fechada não tem nenhum `E-NNN`
  (conjunto vazio de critérios): é uma lacuna anterior a esta release, vale para qualquer peso.

## W-01 — Coluna opcional de peso no §5 (canônica e fila provisória)

- **Solução:** coluna opcional `Weight` nas duas tabelas, valores `light` / `full`; ausência de
  valor, de coluna ou valor desconhecido é `full`. Um helper em `_index_checks` devolve o peso de
  uma etapa pelo nome da pasta ou pelo slug da fila. `sdd-roadmap` pergunta o peso ao enfileirar uma
  etapa nova e pede uma frase de justificativa quando for `light`; `sdd-specify` ajusta o que exige
  (ver W-02) e lembra de levar a coluna junto na promoção da fila para o §5.
- **A decidir ao implementar:**
  1. **nome e idioma**: o plano usa `Peso`/`leve`/`completo`; o kit é em inglês e os cabeçalhos já
     aceitam aliases (`Stage`/`Etapa`). Proposta: canônico `Weight`/`light`/`full`, com `Peso`,
     `leve` e `completo` aceitos como alias na leitura.
  2. **onde fica a justificativa**: a fila tem `Notes`; a tabela canônica não. Opções: a frase
     no próprio valor da célula (`light: corrige typo`, o helper lê só o primeiro token) ou no
     `spec.md` da etapa. Preferência: na célula, para o `doctor` poder exigir que exista.
  3. **o que `light` relaxa com EDD desligado**: nada mecânico (não há check de EDD). Proposta:
     `sdd-specify` aceita spec curta, mas critérios de aceite e a verificação de verdade
     (`sdd-close` passo 2) nunca saem.
- **Riscos e testes:** marcar `light` para fugir de rigor; mitigar com a justificativa obrigatória
  e `full` como padrão. Testes: fixture com §5 sem a coluna lê tudo como `full`; fixture com as
  duas colunas lê `light` e `full` lado a lado, na tabela canônica e na fila; alias `Peso`/`leve`.
- **Propaga por:** `sddkit update` (skills `sdd-roadmap`, `sdd-specify`), comentário do template do
  §5 e código (`_index_checks`). Constituições existentes não são reescritas: a coluna entra quando
  o agente enfileira ou revisa uma etapa.

## W-02 — `doctor` e `sdd-close` de EDD interpretam o peso

- **Solução:** o `doctor` busca o peso de cada etapa e relaxa só o volume de cerimônia numa etapa
  `light`:
  - `edd_missing_checklist` não dispara se todo `E-NNN` de `evals.md` já aparece em `report.md`;
  - `edd_missing_evals` continua exigindo `evals.md` (a régua mínima não cai);
  - `edd_eval_uncovered` continua valendo por critério: toda evidência definida precisa existir.
  `sdd-close` e `sdd-specify` dizem o mesmo em texto: numa etapa `light`, `evals.md` com 1–2
  critérios e a evidência no relatório bastam, sem `checklist.md` separado.
- **A decidir ao implementar:** o buraco do `evals.md` sem nenhum `E-NNN` numa etapa fechada
  (pré-existente). Fechá-lo só para `light` seria estranho (a regra mais dura no peso mais leve).
  Proposta: tratar como defeito e emitir `edd_no_criteria` para qualquer peso, listado em Fixed no
  CHANGELOG, já que correção de defeito entra antes de capacidade nova.
- **Riscos e testes:** relaxar demais; por isso a evidência mínima é fixa. Testes: etapa `light`
  fechada, com `report.md` cobrindo os critérios e sem `checklist.md`, não acusa; etapa `light`
  fechada com critério sem evidência acusa `edd_eval_uncovered`; etapa `full` com o mesmo
  arranjo continua acusando `edd_missing_checklist` (comportamento atual preservado).
- **Dependências:** W-01.
- **Propaga por:** código (`cli.py`, `_findings.py` para o texto do finding) e skill `sdd-close`.

## Ordem de trabalho

W-01 primeiro (helper de leitura, template, skills), depois W-02 (doctor e `sdd-close`). Um commit
por item; a pergunta de nome/idioma do W-01 fecha antes de qualquer teste, porque os testes fixam o
formato.

## Gate de saída

Suíte e `ruff` verdes; fixture com etapa `light` e etapa `full` lado a lado; `sddkit update
--dry-run` em cópia de projeto real não muda nenhuma etapa já fechada nem o §5 (peso ausente vira
`full`, nunca `light`).

## Fora desta release

- Não muda o manifesto (`features.edd` e os demais continuam por projeto).
- Não cria comando novo para marcar peso; é edição do §5 pelo agente, como `Milestone`.
- Não toca nos estágios 09 a 16 do plano.
