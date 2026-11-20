# Notes — sdd-cli 4.9.6

## Verificação

- `python -m pytest -q` e `ruff check src tests`: verdes (532 testes; 17 novos em `test_slim.py`).
  Rodados com CPython 3.12 (`py -3.12`): o código usa f-strings aninhadas (PEP 701).
- **`doctor` 4.9.1 × 4.9.6 sobre o MESMO estado real dos 10 projetos** (2026-11-20; 4.9.1 = `sddkit`
  instalado, 4.9.6 = código da branch, já com o bump): status de saída igual (0) nos 10; nenhum achado
  sai ou entra além do previsto.
  - P3 e P4: `constitution_oversized` ganha `limit`, `top` e `slim_bytes` (mesma severidade, mesmo
    limiar); P3 segue com `long_table_cell` x29.
  - P4, P8 e P9 (kit 4.9.1) ganham `kit_behind` (note) por causa do bump para 4.9.6; os outros sete já
    tinham a nota e só mudam o texto da versão. É o comportamento esperado do K-06.
- **`update --dry-run` nos 10 projetos**, com sha1 de `.sdd/`, `.claude/`, `.github/`, `.kilo/` e dos
  `.md` da raiz antes e depois: nenhum arquivo mudou; os 10 mostram "Would bump kit_version -> v4.9.6".
- **`fix --slim` em cópia da constituição de P3 e P4** (só o `constitution.md`, em pasta temporária):
  - P3: 64.829 → 63.191 bytes (7 comentários, 1.638 B); P4: 31.254 → 31.124 bytes (1 comentário,
    128 B previstos; 130 B reais porque o arquivo está em CRLF e cada linha removida custa 2 bytes).
  - Mesmo número de seções H2; backup byte a byte igual ao original em `.sdd/.pre-fix-backup/`;
    segunda execução não encontra nada.
- Medido (só `--dry-run`, nos projetos reais): o que o `--slim` recupera de comentários de template é
  1.345 B no P1, 125 B no P2, 1.620 B no P3, 125 B no P4, 479 B no P5 e no P6, 0 B no P7 e no P10,
  1.722 B no P8 e no P9.

## Decisões tomadas ao implementar

- Nome do modo de leitura: `doctor --slim` (o plano deixava em aberto). Ele substitui a auditoria
  em vez de acompanhá-la, para a saída ficar só com o plano.
- Destino por seção só onde o dono decidiu (§3 e §6 → `CHANGELOG.md`, §5 → `backlog.md`); §1, §2, §4
  e §7 saem como "decidir com o dono". O plano de 2026-11-17 não cobria §4 e §7.
- A lista inclui linhas de texto (não só linhas de tabela) acima de 600 B; o `long_table_cell` do
  `doctor` continua olhando só linhas com `|`.
- Severidade e limiar de `constitution_oversized` não mudaram (decisão B-01 do estágio 27 depende do
  dono).

## Não verificado

- O `--slim` só reconhece comentários iguais aos do template **desta** versão do kit. Comentário de
  template de uma versão anterior (projeto antigo) conta como editado e fica.
- O ganho é pequeno: não tira P3 (≈ 40 KB acima do limite) nem P4 (≈ 6,5 KB acima) do aviso. O que
  tira é mover texto do dono, que o `doctor --slim` lista e o kit não faz.
- Não houve uso real do `doctor --slim` por um agente seguindo a instrução (nenhum texto movido).
- Não publicada: sem tag, sem merge em `main`, sem push.
