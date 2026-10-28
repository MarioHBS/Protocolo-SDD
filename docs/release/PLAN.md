# Plan — sdd-cli 4.6.0

**Branch:** `4.6.0` (from `main` = 4.5.0) · **Language:** Portuguese

Tema: o portão `DECIDING` não deixa passar decisão estrutural sem auditoria. A lista do que é
"estrutural" passa a cobrir design system (P2/IP-001), a descoberta deixa de pular o autoaudit,
uma decisão estrutural contestada é apresentada por mais de uma perspectiva e, para design e
arquitetura, essas perspectivas podem se apoiar numa busca externa delimitada.

Origem: estágio 07 do plano (branch `roadmap`/repo privado), escrito em 2026-10-01, antes das
releases 4.3 a 4.5. Os itens abaixo foram reconciliados com o código desta branch.

## Estado atual do código (conferido em 4.5.0)

- `src/sdd_cli/content/sdd/skills/sdd-decide/SKILL.md`: lista "What counts as structural" com 9
  categorias, nenhuma de design system, tema ou acessibilidade; passo 2 diz só "Offer concrete
  options with pros and cons when it helps"; passo 4 é o autoaudit frio.
- `src/sdd_cli/content/sdd/skills/sdd-discover/SKILL.md`: curta, sem checklist de categorias, sem
  ramificação de interpretações, sem busca externa; manda registrar incerteza como pergunta aberta.
- `sdd-discover.standalone/SKILL.md` (fora do pacote, para uso sem Claude Code): **já recebeu** o
  texto-alvo de G-01, G-04 e G-05 e a rotulagem "proposed" das decisões, no commit `8eb4404`
  (2026-10-02). Ele diz que a lista "espelha" a de `sdd-decide`, mas hoje as duas divergem (a do
  standalone tem design system, a do `sdd-decide` não). Esse texto é a fonte para as skills do CLI.
- `cli.py → _apply_discovery` (linha ~228): troca `State: INITIALIZING` por `State: SPECIFYING`,
  grava `Active stage: 001-<slug>`, `Next action: load the sdd-specify skill` e escreve as decisões
  em §3 com a coluna `Locked on` preenchida. O autoaudit (passo 4 de `sdd-decide`) nunca roda.
- `tests/test_discovery_edd.py:41` fixa `**State:** SPECIFYING` depois de `init --discovery`; vai
  mudar com G-02.
- `tests/test_cli_name.py` falha se algum texto gerenciado ensinar `sdd <comando>`: todo texto novo
  de skill usa `sddkit`.

## G-01 — Design system / convenções de UI como categoria estrutural, em uma lista só

- **Solução:** acrescentar "Design system / convenções de UI transversais (tema claro/escuro,
  biblioteca de componentes, breakpoints, baseline de acessibilidade), quando o projeto tem
  interface" à lista de `sdd-decide`, na mesma posição da lista do standalone. A `sdd-discover` do
  CLI passa a trazer a mesma lista literalmente (copiada do standalone).
- **Testes:** a lista de categorias de `sdd-decide`, a de `sdd-discover` (CLI) e a do standalone
  têm as mesmas categorias, comparadas por texto. Hoje o standalone é o único com a categoria nova.
- **Propaga por:** `sdd update` (skills).

## G-02 — `sddkit init --discovery` deixa o projeto em `DECIDING` com as decisões como propostas

- **Solução provável:** `_apply_discovery` grava `State: DECIDING`, `Next action` apontando para o
  passo 4 de `sdd-decide` (só o autoaudit, sem repetir a entrevista) e marca as linhas de §3 como
  propostas ("importado da descoberta, não auditado"); a data da coluna `Locked on` só é
  preenchida pelo `sdd-decide` ao travar. O standalone já diz ao dono que `locked_on` é só a data
  do acordo.
- **A decidir ao implementar:**
  1. como marcar "proposta" na tabela §3 sem quebrar os leitores de `Locked on` (doctor, dashboard,
     parsers de §3); conferir antes de escolher o formato.
  2. o passo 5 de `sdd-decide` hoje abre o portão para `ROADMAP`, mas a descoberta já trouxe os
     estágios (§5, backlog, `001-<slug>/`). Escolher entre mandar para `ROADMAP` (que confirma o que
     veio) ou direto para `SPECIFYING`, e dizer isso na skill.
  3. `Active stage: 001-<slug>` já vem preenchido com o estado em `DECIDING`; verificar se algum
     check do `doctor` ou do dashboard estranha a combinação.
- **Antes de mudar o comportamento padrão:** conferir se algum projeto real foi criado por
  `--discovery`. A `01-EVIDENCIA` do plano não cita nenhum; perguntar ao dono ou varrer os repos.
- **Testes:** `init --discovery` deixa `State: DECIDING` e §3 marca as linhas como propostas
  (atualizar `test_discovery_import_bootstraps_reviewed_project`); `sddkit update --dry-run` em
  projeto já criado por descoberta não reescreve o estado (só arquivos gerenciados).
- **Propaga por:** código (`cli.py`) e skills (`sdd-decide`, `sdd-discover`).

## G-03 — `sdd-decide` nomeia perspectivas antes de levar a opção ao dono

- **Solução:** no passo 2, para decisão estrutural sem resposta óbvia, nomear 2–3 perspectivas
  pertinentes à categoria (arquitetura, UX, segurança...; a lista varia, não é fixa) e dar a opção
  de cada uma antes da pergunta final. Só texto; sem agente nem ferramenta nova. Reaproveitar o
  trecho "Ambiguous points: branch before asking" do standalone.
- **Limite:** só para decisão estrutural sem resposta óbvia, nunca para toda pergunta.
- **Testes:** o texto de `sdd-decide` contém a instrução de perspectivas e o limite de 2–3.
- **Propaga por:** `sdd update` (skill).

## G-04 — Busca externa delimitada antes de fechar design system ou arquitetura

- **Solução:** `sdd-decide` e `sdd-discover` (CLI) ganham a seção "External references (bounded)"
  do standalone: no máximo 2 consultas, parar com 2–3 referências, consulta genérica (nunca
  trecho do projeto do dono), resultado como insumo e não como resposta, e fallback sem ferramenta
  de busca (perguntar ao dono ou registrar a lacuna), sem travar a etapa.
- **Testes:** o texto traz o teto de 2 consultas, a regra de consulta genérica e o fallback.
- **Propaga por:** `sdd update` (skills).

## G-05 — `sdd-discover` ramifica interpretações antes de travar um ponto ambíguo

- **Solução:** copiar o trecho "Ambiguous points: branch before asking" do standalone para a
  `sdd-discover` do CLI; vale só para decisão estrutural sem resposta óbvia e para pergunta com
  `blocks_gate: "yes"`.
- **Testes:** o texto da skill traz a instrução e o limite.
- **Propaga por:** `sdd update` (skill).

## Ordem de trabalho

G-01 primeiro (a lista é base de G-04 e G-05), depois G-03 e G-05 (mesma técnica), G-04, e por
fim G-02, que é o único que muda código e o estado final de um fluxo. Um commit por item.

## Fora desta release

- Não há campo novo no JSON de `discovery.json` (`schema_version` continua `sdd-discovery/v1`).
- Não cria agente nem comando novo; busca externa é instrução de texto.
- Não toca peso por etapa (estágio 08, 4.7.0) nem outros estágios.
- Projetos já inicializados só recebem o texto novo por `sddkit update`; nada em `.sdd/` do dono
  é reescrito.
