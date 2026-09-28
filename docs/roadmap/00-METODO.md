# Método — por que releases pequenas

## Pergunta

Fazer uma atualização grande com quase todos os pontos encontrados, ou várias pequenas com
escopo definido?

## Decisão: releases pequenas e programadas

| Critério | Efeito |
|----------|--------|
| **Risco de perda de dado** | O item R2-01 (regenerar o roadmap apaga texto) bloqueia a migração de um projeto grande (P4). Precisa sair antes e sozinho, sem esperar features. |
| **Evidência desigual** | Três itens têm ≥ 2 projetos e são defeitos. Outros (`sdd finding`, lint de markdown) têm um projeto só, ou entram em conflito com convenções de outro. Misturar os dois dá release inflada e mal testada. |
| **Independência** | Detectores, textos de agente e comandos novos quase não se tocam. Juntar não traz ganho e multiplica o risco de regressão. |
| **Ciclo de feedback curto** | Os projetos usam o kit todos os dias; os atritos da migração v3.2.0 → v4.2.1 de P5 foram registrados no mesmo dia. Release pequena devolve feedback em dias. |
| **Propagação de arquivos gerenciados** | Tudo que muda README, shims ou skills chega aos projetos por `sdd update`. Agrupar essas mudanças na mesma release faz cada projeto rodar `update` uma vez só. |
| **Decisão pendente do dono** | O nome do CLI (estágio 4.4.0) não pode segurar as outras. |

## Regras de escopo de uma release

1. Um tema. Se um item não cabe no tema, vai para o estágio seguinte ou para `05-ADIADOS`.
2. Todo item traz origem (episódio real), local no código, causa raiz e solução provável.
3. Correção de defeito entra antes de capacidade nova.
4. Mudança que reescreve arquivo do usuário (constituição, roadmap, stages) só entra com
   `--dry-run`, cópia de segurança e teste de fixture.
5. Uma release nunca depende de decisão aberta do dono.

## Definição de pronto de uma release

- `pytest` e `ruff check src tests` verdes; testes novos para cada item (fixture que reproduz o episódio).
- `CHANGELOG.md` com Added/Fixed/Changed por item, citando o ID (`R2-03`).
- `sdd migrate --dry-run` e `sdd update --dry-run` em cópia de projeto real: nenhum arquivo do
  usuário muda sem estar na prévia.
- Versão no `pyproject.toml` e em `content/VERSION` conferidas.
- Documentação da versão em `docs/release/` (`PLAN.md`, `TODO.md`, `NOTES.md`) na branch dela.
- Tag `vX.Y.Z` e merge fast-forward em `main`.

## Commits

Vários commits granulares por tópico, nunca um commit genérico por release.

## Fluxo de uma versão

```text
main (última versão)
  └─ branch X.Y.Z         primeiro commit: git rm -r docs/release + docs/release/ da versão
       ├─ commits por item (R2-01, R2-02, …)
       └─ verificação → tag vX.Y.Z → merge ff em main
```
