# Notas — sdd-cli 4.10.0

Feito em 2026-11-24 na branch `4.10.0` (de `main` = 4.9.6). Cinco itens (M-01 a M-05), 705 testes
(baseline 604), `ruff` limpo.

## Verificação

- **`pytest` e `ruff check src tests`:** 705 passed, ruff limpo. Testes novos: `test_adr.py` (numeração,
  índice, coluna `Record`, campo da §7), `test_adr_doctor.py` (uma fixture por verificação),
  `test_adr_discovery.py` (M-03), `test_adr_init.py` (M-04: 5 linhas `D-NNN`, pasta externa, documento
  único, resume, `--answers` inválido).
- **`doctor` 4.9.6 × 4.10.0 sobre o MESMO estado real dos 10 projetos** (2026-11-24; 4.9.6 = tag
  extraída para uma pasta temporária, 4.10.0 = código da branch; `doctor --json --all` somente leitura).
  Todos saem 0 nas duas versões. Diferenças, todas previstas:
  - `kit_behind` (nota) em P1, P3, P4, P5, P6, P7, P8, P9, P10: o CLI novo é mais novo que o kit do projeto.
  - `decisions_dir_missing` (nota) em P2, P4, P8: têm `D-NNN` e a §7 em texto livre de legado (P2: pasta
    `docs/decisoes/`; P4: ADRs dentro do DOC-007; P8: campo ainda com o texto do template).
  - Nenhuma diferença em P1 e P3 além de `kit_behind`: escrevem "não há ADRs formais" / "Não aplicável"
    na §7, e o texto agora conta como "não se aplica" (ver Decisões, 3).
  - P5, P6, P7, P9, P10 escrevem "not applicable" na §7: sem nota.
- **`adr init` em cópias de P2 e P4** (originais intocados):
  - P2, `strategy: import` de `docs/decisoes/`: 7 registros importados com a numeração original
    (ADR-001 a 007), `Record` preenchido em D-005, D-014, D-015 e D-016, coluna `Registro` acrescentada
    (a tabela é em português), §7 vira `internal`. O segundo `ADR-006` da pasta (`ADR-006-painel-admin-
    em-subdominio.md`; a pasta tem dois arquivos com esse número) **não foi importado**: o número já
    existia, e o comando avisa em vez de sobrescrever. Segunda execução: "nothing to do" e arquivos
    idênticos. Depois, o `doctor` dá 3 avisos `adr_without_decision` (ADR-002, 003 e 004 não citam
    nenhum `D-NNN`): é o aviso de que esses registros ainda não têm linha na §3.
  - P4, `strategy: link` ao DOC-007 real (99 KB, nome com espaços e travessão): §7 passa a
    `external — \`<caminho>\`` (com o texto antigo depois de `previously:`), nenhuma célula `Record`
    preenchida (o documento tem vários ADRs e o kit não os separa), `doctor` sem aviso novo.
- **`update --dry-run` nos 10 projetos:** exit 0 em todos e o sha1 de `.sdd/`, `.claude/`, `.github/`,
  `.kilo/` e dos `.md` da raiz é igual antes e depois.
- **`update` real em cópia do P7:** atualiza 6 skills, acrescenta `.sdd/templates/adr.template.md`, mostra
  as notas da 4.10.0 com a linha `Manual action:`, **não cria `.sdd/decisions/`**, e o `doctor` fica sem
  `managed_file_edited`.
- **`adr index` duas vezes seguidas:** arquivo idêntico byte a byte (testado e conferido na cópia do P2).
- **`init --discovery` com `adr: true`** (projeto novo, conferido lendo os arquivos): ADR em `proposta`
  com contexto, alternativas e a seção `Decision` preenchida com a escolha e a justificativa da linha,
  `Record` na linha `D-001`, `doctor` sem achado.

## Decisões tomadas ao implementar

1. **Ordem M-01 → M-02 → M-05 → M-03 → M-04** (M-04 depende do modo `external`). Pedido do dono: o
   número é 4.10.0 (o plano chamava o estágio de "12"); EARS e `sdd-qa` passam a 4.11.0 e 4.12.0.
2. **Numeração dos ADRs** usa o mesmo livro (`.sdd/.reservations.json`) e a mesma trava (`.sdd/.lock`) do
   `seq next`, com a chave `adr`, em vez de declarar uma sequência na §7: assim um número apagado ou
   importado nunca volta, e o `sequence_duplicate` do doctor não passa a olhar a pasta.
3. **`decisions_dir_missing`** só vale quando a §7 é `internal`, vazia ou texto livre de legado; "not
   applicable", "não aplicável", "não há ADRs", "no ADRs" e `external` não recebem a nota. O gate dos 10
   projetos mostrou P1 e P3 escrevendo isso em português.
4. **O `.sdd/README.md` gerenciado voltou ao texto da 4.9.6.** O primeiro `doctor` 4.9.6 × 4.10.0 mostrou
   `managed_file_edited` novo no P2 (manifesto com hash `fc2d…` e arquivo igual ao README da 4.9.6,
   `5f79…`): o `update` o trataria como editado à mão e o aviso ficaria para sempre, a mesma armadilha do
   `track-state.template.md` na 4.9.6 (IP-018). As skills carregam as instruções.
5. **Coluna `Record`** (não `Registro`): o kit é em inglês. `Registro` e `ADR` são aceitos como apelidos,
   e `adr init` acrescenta `Registro` quando a tabela do projeto está em português.
6. **Caminho externo com espaços** vai entre crases na §7 (`external — \`caminho com espaços.md\``).
   Achado no teste com o DOC-007 do P4: sem isso o `doctor` acusava `adr_external_path_missing`.
7. **`adr init` só importa pasta com um arquivo por ADR.** Documento com vários ADRs só é vinculado.
   Status de um registro importado: `aceita` se a linha `D-NNN` tem data, `proposta` se não casa com
   nenhuma linha (e o doctor avisa `adr_without_decision`).
8. **Sem `adr set-status`**; mudar status é editar o frontmatter e rodar `adr index`.
9. **`adr new --decision`** escreve o link na célula `Record` da linha (copiando a constituição antes);
   tabela sem a coluna é deixada em paz e o comando diz como acrescentá-la.
10. **O preset `medium` do `sddkit document`** descrevia `decisions.md` como "decision records (ADRs)";
    agora diz que é uma visão e que os ADRs vivem em `.sdd/decisions/` (o espelho gerado é o L-03 do
    estágio 13, não desta release).

## Revisão do material complementar

Lido de verdade, não só pelos testes:
- **Help:** `sddkit --help` (grupo `document: document, adr, manual`), `adr --help`, `adr new|index|init
  --help` lidos na saída real; faltava o exemplo de `adr init` e a menção a `init` na descrição do grupo
  (corrigido). Exemplos parseiam (`tests/test_help_docs.py`).
- **Doctor:** mensagens e dicas dos 9 códigos lidas na saída real do `doctor` (cópia do P2 e P8); a tabela
  do `USAGE.md` bate com as severidades de `_adr_checks.py`.
- **Skills:** nenhuma ainda diz "não invente formato", "ADRs vivem na documentação" nem cita só `D-NNN`;
  `sdd-decide`, `sdd-discover` (e a standalone), `sdd-specify`, `sdd-init`, `sdd-close` e `sdd-document`
  apontam `sddkit adr`. O fluxo `DECIDING` → ADR `proposta` → autoaudit → `aceita` foi lido de ponta a
  ponta num projeto criado por `init --discovery`.
- **Achado fora das skills:** o preset do `sddkit document` (decisão 10).

## Não verificado

- A entrevista interativa com um terminal real (só com `Console` roteirizado nos testes e `--answers`
  nas cópias de P2 e P4).
- `adr init` em P1, P3, P5 a P10 (P2 e P4 são os dois casos de ADR fora do `.sdd/`; os demais declaram
  não ter ADR).
- Documentos de ADR únicos com seções parseáveis: o kit não os separa por decisão de escopo.
