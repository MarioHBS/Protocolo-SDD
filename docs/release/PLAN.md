# Plan — sdd-cli 4.10.0

**Branch:** `4.10.0` (de `main` = 4.9.6) · **Idioma:** português

Tema: o ADR deixa de depender da feature Documentation e passa a viver em `.sdd/decisions/` (um
arquivo por ADR, mais um índice gerado). O plano privado chama este estágio de "estágio 12"; a pedido
do dono ele sai como **4.10.0**, e os estágios de EARS e `sdd-qa` passam a 4.11.0 e 4.12.0.

## Itens

- **M-01** lugar, formato e numerador: `.sdd/decisions/ADR-NNN-<slug>.md`, template
  `adr.template.md`, frontmatter (`id`, `status`, `date`, `stage`, `decision`, `supersedes`,
  `superseded_by`, `implemented_in`, `reconstructed`, `source`), ciclo de status
  `proposta → aceita → implementada → substituída | obsoleta`, `sddkit adr new` com número que
  nunca é reaproveitado (mesmo livro e mesma trava do `seq next`).
- **M-02** índice gerado (`sddkit adr index` → `.sdd/decisions/README.md`, idêntico byte a byte
  quando nada mudou) e coluna "Registro" na §3 da constituição; critério escrito no `sdd-decide` de
  quando a decisão ganha ADR.
- **M-05** campo `Decision records: internal | external` na §7 e verificações novas do `doctor`
  (id duplicado, status fora do ciclo, ADR sem linha `D-NNN` e vice-versa, `implementada` sem
  `implemented_in`, `substituída` sem sucessor, índice defasado, `decisions/` ausente, caminho
  externo inexistente).
- **M-03** `discovery.json` ganha `context`, `alternatives` e `adr` (opcionais, por decisão); o
  `init --discovery` escreve os ADRs em `proposta`; `sdd-decide` cria o arquivo quando a decisão
  passa o critério e o autoaudit muda `proposta` para `aceita`.
- **M-04** `sddkit adr init`: entrevista retomável (`--resume`, `--answers`, `--dry-run`) que
  reconstrói ADRs de projeto legado sem inventar (`reconstructed: true`, `source:`), vincula ou
  importa ADRs externos e preenche a coluna "Registro" e a §7.

Ordem de construção: M-01 → M-02 → M-05 → M-03 → M-04 (M-04 depende do modo `external` de M-05).
G-02 e G-03 (4.6.0) já estão feitos; M-03 só reaproveita o status `proposta`.

## Decisões

1. **Severidades do `doctor`:** só `adr_duplicate_id` é `error`; as demais são `warn`; `decisions/`
   ausente em projeto interno com `D-NNN` é `note`. Projeto sem ADR por escolha nunca falha.
2. **`adr init` importa só pasta com um ADR por arquivo.** Documento monolítico (vários ADRs em um
   arquivo) só é **vinculado**: o kit não corta documento em ADRs.
3. **Sem `adr set-status`:** o spec pede só `new`, `index` e `init`; mudar status é edição manual,
   validada pelo `doctor`.
4. **`update` e `migrate` nunca criam `decisions/`.** `adr new` e `adr init` criam.
5. **Coluna "Registro" só no template novo.** Tabela §3 sem a coluna continua lida; em projeto
   existente a coluna é preenchida por `adr init` (prévia e backup), nunca por `update`.
6. **Arquivos novos em LF**; edição da constituição preserva o fim de linha do arquivo.
7. **O `.sdd/README.md` gerenciado não muda nesta release.** O `doctor` 4.9.6 × 4.10.0 mostrou que o
   P2 (manifesto com hash antigo, arquivo igual ao README da 4.9.6) passaria a acusar
   `managed_file_edited` para sempre (família do IP-018, igual ao `track-state.template.md` da 4.9.6).
   A descrição de `decisions/` fica no `USAGE.md` e nas skills.
8. **Coluna da §3 chama-se `Record`** (o kit é em inglês); `Registro` e `ADR` são aceitos como apelidos.
9. **"Não aplicável" e "não há ADRs" (e os equivalentes em inglês) silenciam a nota** `decisions_dir_missing`:
   o `doctor` nos 10 projetos mostrou 6 deles escrevendo isso em português ou inglês na §7.
10. **Vistoria final:** o agente Opus achou B1 e I1 a I5 (ver `NOTES.md`); corrigidos nesta release. O M4 da
    vistoria (pipe escapado em célula) fica para a 4.10.1.
