# Plan — sdd-cli 4.3.1

**Branch:** `4.3.1` (from `main` = 4.3.0) · **Status:** implemented, release step pending · **Language:** Portuguese

Adiantada do estágio 12 (4.11.0) do plano de atualizações (branch `roadmap`): é texto puro e não
depende de `.sdd/decisions/` nem de comando novo. O resto do estágio 12 e o estágio 13 seguem
planejados para as versões 4.11.0 e 4.12.0.

## M-06 — O kit não diz quem manda quando documentação, decisão e código divergem

- **Origem:** projeto K-entre-nos. Duas regras coexistem sem dizer qual vale: "a documentação segue
  o código" (`sdd-document`, "Documentation follows ground truth") e "o ADR manda" (a §3 é
  imutável). O caso que as concilia é o ADR-032 do K: duas premissas de um documento foram
  refutadas ao implementar, e a decisão foi emendada em vez de o código divergir em silêncio.
- **Evidência:** `sdd-document/SKILL.md` (regra "Documentation follows ground truth"); `sdd-specify`
  (anti-regressão); `sdd-close` passo 12 lê o `covers` do plano de documentação mas não classifica
  divergência; princípio zero do README só trata índice × disco.
- **Causa raiz:** as duas regras valem para classes diferentes de artefato e o kit não diz quais.
- **Solução:** seção "Who rules when artifacts disagree" no README do kit, com três classes
  (intenção, realidade observável, premissa refutada) e a regra "decisões descem, evidência sobe".
  `sdd-close` (passo 12), o template de relatório (§7) e `sdd-document` citam a seção pelo título;
  a tabela existe uma só vez.
- **Desvio do plano original:** não há seção "Deriva" nova no relatório; a classificação entra na
  §7 "Divergences from the spec", que já existe. Obrigatoriedade por nível fica para o estágio 13.
- **Riscos e testes:** texto gerenciado, chega por `sdd update`; nada em projeto existente muda além
  dos arquivos gerenciados. Teste: tabela no README, citação por título nas três outras peças,
  nenhuma duplicando a tabela.
- **Propaga por:** `sdd update`.

## Fora desta versão

O ajuste dos leitores de Settings do L-01 (`doctor` e `_set_feature` aceitarem os níveis de
documentação) é o primeiro commit do estágio 13, para esta release ter um tema só.
