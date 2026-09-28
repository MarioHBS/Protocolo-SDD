# Adiados — com origem, motivo e gatilho de retomada

Nada some sem registro. Cada item diz por que não entrou nos estágios 02 a 04 e o que faria
o item voltar. Quando um gatilho for atingido, o item vira um item de estágio (com o modelo
de `ITEM-TEMPLATE.md`).

| ID | Item | Origem | Motivo de adiar | Gatilho |
|----|------|--------|-----------------|---------|
| A-01 | `sdd finding`: área nativa para achados de teste manual com evidências (`F-NNN`, capturas ligadas ao achado, vínculo achado → etapa verificado pelo `doctor`, importação do arquivo manual existente) | P2/IP-009 | Capacidade nova e grande; só um projeto pede; o formato exige desenho com o dono | Segundo projeto com fluxo próprio de observações de teste manual |
| A-02 | Contingência de orçamento por `Origin` no `estimates.md` (razão etapas tardias ÷ planejadas por origem), com proxy: contagem de stages com sufixo de letra | P2/IP-001 (solução 5); P2 tem 11 stages com sufixo e P4 tem 14 | O campo `Origin` existe desde a 4.1.0, mas nenhum projeto acumulou dado suficiente | ~20 stages fechadas com `Origin` preenchido em algum projeto, ou decisão de expor a contagem de sufixos como nota do `doctor` |
| A-03 | `sdd fix --index`: enxugar um §5 existente (remover colunas Spec/Report quando o link é o convencional; mover narrativa do §6 para o CHANGELOG) | Medição em P2 (84 KB → 71 KB após `fix --links`); P4 tem 574 linhas | Remover colunas de tabela do dono é mudança estrutural, não reparo determinístico | 3 projetos com `constitution_oversized`: P2 confirmado, P4 e possivelmente P3 prováveis; confirmar com `doctor` após `update` |
| A-04 | Lint de markdown no `doctor` e `sdd fix --markdown` (reparo determinístico de MD022/031/032/040), com configuração distribuída | P2/IP-004 | Só um projeto pede; P4 tem convenção oposta (~80 colunas); o kit não deve impor estilo. R3-05 ataca a causa por texto | Segundo projeto sem convenção conflitante; ou pedido explícito do dono |
| A-05 | Comando para arquivar linhas antigas de `estimates.md` e `roadmap.md` | P4 (roadmap de 1.655 linhas), P2 (roadmap de 120 KB) | O `doctor` já acusa `cold_file_oversized`; nada arquiva | Arquivos frios acima de ~200 KB ou skills passando a lê-los por padrão. P4 provavelmente já cumpre; confirmar |
| A-06 | Separar o README do kit em "cartão de sessão" + referência | Medição na 4.1.0 (README ≈ 3,5k dos ~5k tokens de início) | Exige reorganização editorial compatível com todos os skills que o citam | Medição em mais projetos mostrando o README como maior custo de início |
| A-07 | Guarda de trilha por hook (`PreToolUse` chamando `sdd track guard`), modo worktree opt-in e trailer `SDD-Track:` nos commits | Avaliação de trilhas (arquivos editados por duas trilhas, números de stage colidindo) | Só cobre providers com hooks; modo worktree exige validar junctions no Windows | Um segundo incidente de colisão que `check`/`verify` não teria pego |
| A-08 | Dashboard gráfico com servidor local ou janela nativa (`tkinter`) | P1/IP-010 (entregue como HTML estático em `--ui web`) | Servidor e GUI nativa não foram pedidos além do HTML | Pedido concreto de janela nativa ou atualização ao vivo |
| A-09 | `sdd ws doctor/fix` (agregação entre workspaces) | Ideia de acompanhamento | Exige definir descoberta, permissões e agregação | Dono com vários projetos querendo relatório único |
| A-10 | Type-check (`mypy` ou `pyright`) | Pendência da CI | Decisão de política e configuração | Decisão do dono |
| A-11 | Matriz versionada de migradores entre majors | Pendência de migração | O `migrate` cobre o major vigente | Fluxos de migração divergindo entre majors |
| A-12 | Política de commits como configuração do projeto | P2, P3 e P5 escrevem regras de commit no `CLAUDE.md` (formato, granularidade, nunca citar o processo) | Cada projeto tem a sua; o `CLAUDE.md` é o lugar certo. Só observação | Pedido repetido de que o kit gere ou verifique essas regras |
| A-13 | Evals herdados por tipo de mudança (stage que move arquivos herda o eval de varredura de imports) | P1/IP-007 (parte não absorvida) | Continua como convenção manual do projeto | Segundo projeto com o mesmo defeito recorrente |

## Removido do escopo por decisão

- **Truncar o hash dos arquivos gerenciados:** alteraria o tamanho do hash e invalidaria os
  manifestos gravados (arquivos intactos passariam a parecer editados à mão); 64 bits bastam
  para esse uso local.
