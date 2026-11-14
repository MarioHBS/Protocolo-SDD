# Notes — sdd-cli 4.8.1

**Branch:** `4.8.1` (de `main` = 4.8.0) · **Idioma:** português

A 4.8.1 reúne os itens K-01 a K-04 do estágio 19 do plano privado, achados quando o dono aplicou a
4.8.0 no primeiro projeto (P1, KNN Warehouse). Sem mudança de comportamento de etapa.

## Testes

458 passam (linha de base 428 na 4.8.0). Novos: `test_backup_ignore.py` (K-01, usa `git init` e
pula sem git), `test_manifest_hash.py` (K-02), `test_audit_closing.py` (K-03) e
`test_mojibake_query.py` (K-04). `ruff check src tests` limpo. Um teste de concorrência de trilhas
(`test_concurrent_incorporations_never_share_a_number`) falhou uma vez sob carga na suíte inteira e
passou em seguida, na 4.8.0 e na 4.8.1; é anterior a esta versão e não foi tocado.

## Decisões

1. **K-02 muda o que o manifesto grava, não o que ele aceita.** O hash passa a ser o do conteúdo em
   LF; `matches_recorded` segue aceitando o bruto, o LF e o CRLF, então manifesto antigo funciona.
2. **Hash bruto exato não é desvio.** A primeira versão do K-02 acusou `manifest_eol_drift` em 8 dos 9
   projetos (hash bruto CRLF gravado pela 4.8.0, disco ainda em CRLF). Agora só é desvio uma forma
   gravada que o disco não tem mais; depois de um `fix --manifest` o valor serve em LF e em CRLF.
3. **K-03 lê o que o projeto diz.** O kit não sabe quando a spec foi travada; pula a etapa que a
   constituição ou uma trilha puseram em `CLOSING` e a que tem o `todo.md` todo marcado. A divergência
   de `Locked-by-audit:` continua avisada. A alternativa `Locked-by-audit: none` ficou de fora.
4. **O marcador da skill global continua `v4.8.0`.** O texto dela não mudou e o `doctor` compara com o
   marcador do texto empacotado, não com a versão do kit.

## Verificação

- **Cópia do KNN (clone do repositório real, trabalho em andamento intocado):** com a 4.8.0, `doctor`
  acusava `mojibake_v1` (a query string do checklist da 009) e `manifest_eol_drift`; com a 4.8.1 o
  primeiro some. `update` 4.8.0→4.8.1 muda só `sdd-audit/SKILL.md` e o manifesto; `fix --manifest`
  deixa o `doctor` limpo, e converter os `.md` de `.sdd/` para CRLF não traz o desvio de volta.
  K-01: revertendo o commit de `.gitignore` do projeto, o `doctor` nota `backup_not_ignored` e
  `fix --gitignore` acrescenta a linha (sem tocar nas demais); a nota some.
- **Cópia dos 9 projetos, `doctor` 4.8.0 × 4.8.1:** nenhum código novo; saíram `lock_without_audit` (P1,
  etapa já em `CLOSING`) e `mojibake_v1` (P1 1, P2 251, P3 6, P4 20, P6 16, P7 7). Dos 301 acertos
  que o filtro de query string deixou de acusar, todos têm `/`, crase ou `http` nos 25 caracteres
  anteriores (nenhum é palavra com acento perdido). `update --dry-run` não alterou nenhum arquivo.
- **Não feito:** `update` real nos outros 8 projetos (só no KNN, em cópia).

## Pendências fora desta versão

IP-018 (arquivo idêntico tratado como "editado à mão" por hash antigo; K-02 reduz a causa e não a
cobre), branch pública `roadmap` parada desde a 4.4.0, tabela de versões dos READMEs em 4.2.1 e
A-15 (nome `sddkit` no npm).
