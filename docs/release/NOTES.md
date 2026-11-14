# Notes — sdd-cli 4.8.0

**Branch:** `4.8.0` (de `main` = 4.7.0) · **Idioma:** português

A 4.8.0 absorve o estágio 17 do plano (4.7.1: U-02 a U-05) e o estágio 18 (S-01 a S-05). Não haverá
tag 4.7.1. A automação por hook passa a ser a 4.9.0.

## Testes

428 passam (linha de base 365; 63 novos em `test_update_notes.py`, `test_fix_weight.py`,
`test_audit.py` e `test_stage_weight.py`). `ruff check src tests` limpo. O `conftest.py` agora isola
`Path.home()`: sem isso a suíte leria a skill global real do desenvolvedor.

## Decisões

1. **Um vocabulário de peso só.** O gate usa o `Weight` da 4.7.0 (`light` = revisão básica; `full` ou
   vazio = auditoria), não um `Peso: comum | pesada` novo, como a IP-013 do P2 sugeria.
2. **Sem retroatividade.** O `doctor` só olha etapas ainda abertas (sem `report.md`); etapa fechada
   nunca é cobrada. Etapa travada antes do `update` e ainda aberta recebe só uma `note`.
3. **Nome do agente: `sdd-audit`, não `sdd-spec-lock`.** O P2 tem um agente local `sdd-spec-lock`; o
   kit não o sobrescreve nem o duplica. Um arquivo que já exista no caminho do agente nunca é
   tocado nem entra no manifesto.
4. **Notas de versão em arquivo próprio** (`content/RELEASE-NOTES.md`), curto, e não o `CHANGELOG.md`
   (que não vai no pacote e tem parágrafos longos). O teste `test_the_release_notes_announce_the_gate`
   exige uma seção da versão atual.
5. **`fix --weight` é opt-in** (fora do `--all`) porque reescreve tabela do dono; mantém os fins de
   linha, pula tabela dentro de comentário HTML e deixa cópia exata em `.sdd/.pre-fix-backup/`, que o
   scan de mojibake e o `fix --eol` ignoram (senão a cópia deixaria de ser exata).
6. **A skill global só é escrita com `--global-skill`.** O `doctor` apenas lê, e é silencioso se o
   arquivo não existe.
7. A seção "To measure before implementing" ficou no §6 da spec, não no §5, para não mexer na regex
   do `scaffold` (que lê o §5 até o `## 6.`).

## Verificação com os 9 projetos reais (cópias de `.sdd/`, `CLAUDE.md`, `AGENTS.md`, `.claude/`)

- `update --dry-run` nos 9: nenhum arquivo muda (hash da árvore igual antes e depois); `constitution.md`
  e `roadmap.md` nunca aparecem na lista.
- `doctor --json` 4.7.0 × 4.8.0: o único código novo é `lock_without_audit` (note), em P1 (009), P3 (011,
  014), P5 (010, 021) e P6 (015-B), todas etapas travadas e ainda abertas. P4, P7, P8 e P9: nada muda.
  Nenhum erro novo; status 0 em todos.
- Cópia do P2, `update --global-skill` real: o agente local `sdd-spec-lock.md` e o `CLAUDE.md` ficam
  idênticos (hash), `sdd-audit.md` é acrescentado, a skill global (em um HOME falso) é regravada, e um
  segundo `update` diz que está em dia.
- `fix --weight`: acrescenta a coluna em P1, P3, P4, P5 e P6 (P4 já a tinha só na fila). Na cópia do P1
  o backup é criado, a segunda execução diz "clean" e o `doctor` não ganha nenhum código de peso.

## Achados fora do escopo

- **P2/`.sdd/README.md`:** o `update` o preserva como "editado à mão" e o `doctor` novo passa a avisar
  `managed_file_edited`. O arquivo é idêntico ao README do kit 4.7.0; o que difere é o hash gravado no
  manifesto. É o mesmo problema da IP-018 do P1 (hash antigo no manifesto, backup a cada `update`) e
  fica para um estágio próprio.
- A branch pública `roadmap` está parada desde a 4.4.0 e os READMEs do kit ainda mostram a tabela de
  versões de 4.2.1.
- P2/IP-003 ainda consta como `aberta` no registro do próprio projeto; o kit já o absorveu (R3-01/N-01).

## O que ficou de fora de propósito

Reservar o nome `sddkit` no npm (A-15, decisão do dono) e um comando que liste candidatas a `light`
(A-16, só se o texto de U-04 não bastar).
