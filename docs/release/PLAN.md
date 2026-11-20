# Plan — sdd-cli 4.9.6

**Branch:** `4.9.6` (de `main` = 4.9.1) · **Idioma:** português

Tema: enxugar a constituição com ajuda do kit. O `doctor` aponta `constitution_oversized` e manda
"mover a narrativa para o CHANGELOG", mas nada ajuda a fazer isso; cada dono gasta um commit à mão.

Origem: estágio 22 do plano privado (E-01, E-02; promove o A-03). A versão pulou de 4.9.1 para 4.9.6
por decisão do dono em 2026-11-20: as versões 4.9.2 a 4.9.5 ficam sem uso e o que estava planejado
para elas será renumerado depois de 4.9.6.

## Estado atual do código (conferido em 4.9.1)

- `cli.py` (bloco da constituição no `doctor`): `constitution_oversized` quando o arquivo passa de
  `24 * 1024` bytes; o JSON traz as 3 maiores seções, o texto não mostra nem o limite nem os bytes de
  cada seção.
- `long_table_cell` aponta só a primeira linha de uma tabela com linha acima de 600 bytes.
- `fix` já tem o padrão opt-in com `--dry-run` e backup (`--weight`): `.sdd/.pre-fix-backup/<ts>/`.
- O template da constituição empacotado tem 12 comentários HTML (2.981 bytes).

## Itens

- **E-01** `sddkit fix --slim`: remove da constituição só o comentário HTML que é, byte a byte, um dos
  do template empacotado. Opt-in, `--dry-run`, backup, mantém o fim de linha do arquivo. O achado
  `constitution_oversized` passa a mostrar o limite, as 3 maiores seções com bytes e quanto o
  `--slim` recuperaria.
- **E-02** `sddkit doctor --slim` (só leitura): bytes por seção, cada linha acima de 600 bytes com o
  arquivo a que pertence (§3 e §6 → `CHANGELOG.md`, §5 → `backlog.md`, outras seções → decidir com o
  dono) e um texto de instrução para o agente. O kit **não edita** nada disso (decisão do dono de
  2026-11-17); a §3 entra no escopo.

## Decisões

1. **Só comentário idêntico ao do template.** Comentário editado, dentro de bloco de código ou que
   não existe no template fica. É o único descartável que o kit consegue provar.
2. **`doctor --slim` e `fix --slim`, mesmo nome, papéis diferentes:** o `doctor` lista, o `fix`
   aplica a parte determinística. O `doctor --slim` substitui a auditoria, não a acompanha.
3. **Severidade e texto de `constitution_oversized` não mudam** (continua `warn`; continua dizendo
   que é lido a cada sessão). Medir só a parte lida no início é decisão do estágio 27 (B-01), que
   depende do dono.
4. **Seções sem regra não recebem destino:** §1, §2, §4 e §7 saem como "decidir com o dono".
