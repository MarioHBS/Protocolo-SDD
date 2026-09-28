# Notes — sdd-cli 4.1.0

> Notas públicas de versão. Os projetos reais em que o kit foi avaliado aparecem como `P1`, `P2`… (ver a branch `roadmap`, `docs/roadmap/01-EVIDENCIA.md`).

## Summary (4.1.0) — implementada em branch (aguarda aprovação para merge)

- **Tema:** sessões menores, trilhas verificáveis, documentação ativa e diagnóstico honesto — guiada por dois projetos reais (P2 em 3.3.0 e P1 em 4.0.0).
- **Adicionado:**
  - `sdd context [--budget]` e regras de leitura no shim/README (P2: ~25k → ~5k tokens estimados por sessão; P1: ~12k → ~4,7k);
  - `sdd track claim|check|verify|incorporate` e `sdd seq next`: pegadas declaradas, sobreposição bloqueada, incorporação atômica com lock, números compartilhados entregues uma vez; `doctor` acusa worktrees de agentes (Kilo cria cópias completas com `.sdd/` defasado);
  - `sdd document`: entrevista guiada e retomável, plano em `.sdd/documentation.json`, arquivos podendo viver fora de `.sdd/`;
  - EDD, `backlog.md`, gate de escopo, `Origin`, checklist transversal e auditoria de credenciais nos skills; achados novos do `doctor` (backlog, marcos, cobertura de evals, tamanho, links absolutos, deriva de features, shims não gerenciados);
  - dashboard com views reais (rich, textual e `plain` sem dependências), gate de release executado em venv limpa contra cópias dos dois projetos;
  - testes de `init`, `migrate`, `update`, `main`; job de CI que instala os extras do dashboard.
- **Mudado:** `doctor` (modo humano) lista todos os achados com o comando de correção; `--help` e `USAGE.md` completos; `sdd manual` (com `sdd docs` como alias obsoleto até a 5.0); template do §5 sem colunas Spec/Report; regras do ruff fixadas.
- **Corrigido:** `sdd context` com `Active stage` em prosa; trilhas concluídas acusadas como "não iniciadas"; scanner de trilhas morto com `NameError` desde a 3.2.0; título indevido no shim do Kilo.
- **Migração:** aditiva. De 4.0.0: `sdd update`. De v2/v3: `sdd migrate --to v4`. Depois, `sdd fix --links --features` (e `--gitignore` se houver worktrees de agentes). O `sdd fix` **não** remove as colunas Spec/Report de um §5 já existente — isso segue manual (ver adiados).
- **Verificado em cópias dos projetos reais:** `migrate --to v4` em P2 e `update` em P1 só tocam arquivos gerenciados; `--dry-run` deixa tudo byte-idêntico; `fix --links` é idempotente.

## Measured result

| Medida | P2 | P1 |
|--------|------|-----|
| Leitura inicial estimada, antes (constituição inteira) | ~25,6k tokens | ~11,9k tokens |
| Leitura inicial estimada, depois (`sdd context --budget`) | ~5,2k tokens | ~4,7k tokens |
| Constituição após `sdd fix --links` | 84.077 B → 70.817 B | — |
| `sdd migrate --to v4` / `sdd update` | só arquivos gerenciados mudam | só arquivos gerenciados mudam |
| `--dry-run` | projeto byte-idêntico | projeto byte-idêntico |
| `track_not_started` espúrio | 5 → 1 (o legítimo, "em espera") | — |

Notas de leitura:

- O ganho vem da **regra de leitura** (cabeçalho da constituição em vez dela inteira);
  o README do kit (~3,5k tokens) passou a ser o maior custo restante.
- `fix --links` reduz menos que o previsto no plano (~13 KB, não ~27 KB): as colunas
  Spec/Report continuam e cada link relativo ainda ocupa espaço. Só o template novo as
  omite; remover colunas de um §5 existente ficou registrado como adiado.
- O `doctor` de P1 acusa 6 evals sem cobertura (não as 8 do IP-004): E-003 e E-009
  da stage 002 aparecem no `report.md`, e a regra aceita `checklist.md` **ou**
  `report.md`. Vale o dono confirmar se essa é a regra desejada.


## Gate evidence

The dashboard release gate was run in a clean venv against copies of two real projects; the raw captures stay outside this repository because they show project content.
