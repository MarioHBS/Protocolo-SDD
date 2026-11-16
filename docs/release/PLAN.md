# Plan — sdd-cli 4.9.0

**Branch:** `4.9.0` (de `main` = 4.8.2) · **Idioma:** português

Tema: três verificações que hoje dependem de alguém lembrar de rodar um comando passam a disparar
sozinhas, por hook do provedor, onde o provedor tiver hook. Onde não tiver, o comando manual de hoje
continua igual: o hook é reforço, nunca pré-requisito.

Origem: estágio 09 do plano privado (H-01..H-03), promovido do `A-07` por decisão do dono em
2026-10-01. Os três itens são ideia, sem episódio real nos projetos avaliados.

## Estado atual do código (conferido em 4.8.2)

- `sddkit track check` (colisão entre trilhas) e `track verify` (mudanças do Git fora do footprint)
  só rodam quando chamados à mão. Não existe `track guard`.
- Nenhum código do kit escreve `.claude/settings.json` nem registra hook. Só o provedor `claude`
  tem hook de ferramenta (`PreToolUse`/`PostToolUse`); os outros dez provedores não.
- Uma trilha não sabe qual é "a sessão atual": por padrão as trilhas dividem a árvore **e a branch**.
  Só `claims.json` com `branch` (via `track claim --branch`) liga uma sessão a uma trilha.
- O `doctor` já devolve tudo em `_doctor_payload` (JSON), então o H-02 não precisa de checagem nova.

## Itens

- **H-01** `sddkit track guard --path <arquivo>`: diz quais trilhas ativas reivindicam o caminho.
  Caminho reivindicado por duas ou mais trilhas = colisão. No hook, vira `permissionDecision: ask`
  (o dono confirma); nunca `deny`.
- **H-02** hook `PostToolUse` em `Write|Edit|MultiEdit` cujo caminho case `.sdd/**/report.md` roda o
  mesmo cálculo de `doctor --json` e devolve o resultado como `additionalContext`, na mesma sessão.
  Outro `.md` não dispara.
- **H-03** o mesmo `guard`, com a trilha da sessão resolvida, avisa quando o caminho tocado está fora
  do footprint dela. Só aviso (`additionalContext`), nunca `ask`, nunca `deny`.
- **H-04** `sddkit hooks install|uninstall|status`: registra e remove os hooks de H-01..H-03 em
  `.claude/settings.json` (ou `--local` em `settings.local.json`). Item novo, necessário: sem ele o
  dono teria de escrever o JSON à mão.

## Decisões

1. **Só o provedor `claude`.** É o único com hook de ferramenta entre os onze do registro. Os outros
   seguem com `track check`/`verify`/`doctor` manuais; `hooks status` diz isso.
2. **Opt-in explícito.** `init` e `update` não instalam hook: ele roda um comando na máquina do dono
   a cada edição. Só `sddkit hooks install` registra.
3. **Merge, não sobrescrita.** O kit lê o `settings.json`, acrescenta só as suas entradas (reconhecidas
   pelo comando `sddkit hooks run ...`) e preserva o resto byte a byte na leitura. `uninstall` remove
   só as dele. JSON inválido = erro, nada gravado.
4. **O hook nunca derruba a edição.** Em modo hook, qualquer exceção interna vira saída vazia com
   exit 0. `sddkit` fora do PATH dá erro não bloqueante do próprio Claude Code (exit 127), a edição
   segue.
5. **Trilha da sessão** = `--track`, depois `SDD_TRACK`, depois a branch atual casada com o `branch`
   de um `claims.json`. Sem trilha resolvida, o H-03 fica calado (não dá para saber o que é "fora");
   o H-01 continua, porque colisão entre duas trilhas não depende da sessão.
6. **Escopo do hook:** `PreToolUse` com `Edit|Write|MultiEdit` (H-01/H-03) e `PostToolUse` com o
   mesmo matcher (H-02). Caminhos dentro de `.sdd/` nunca geram aviso de trilha (mesma regra do
   `track verify`).
7. **Sem `track guard` ligado a dado novo.** Usa os `claims.json` que já existem; nenhum arquivo
   novo no projeto além do `settings.json` que o dono pediu para tocar.

## Riscos e testes

- Windows: o `file_path` chega com barra invertida e absoluto; normalizar para relativo à raiz do
  projeto antes de casar com o glob. O comando do hook é `sddkit`, sem caminho absoluto (o `.exe` do
  pipx fica no PATH). Teste com caminho `C:\...` simulado.
- Ruído do H-02: só `report.md` dentro de `.sdd/`. Teste: `README.md` e `notes.md` não disparam.
- Sem hook configurado, `track check`, `track guard --path` e `doctor` à mão funcionam como antes.
- `hooks install` duas vezes não duplica entrada; `uninstall` preserva hooks do dono; `settings.json`
  com JSON inválido ou com `hooks` de tipo errado aborta sem gravar.
- Entrada JSON do hook malformada (stdin vazio, sem `file_path`) = saída vazia, exit 0.

## Propaga por

Código (`_hooks.py` novo, `cli.py`), `.claude/settings.json` do projeto (só por `hooks install`),
texto da skill `sdd-track`, `USAGE.md` e `RELEASE-NOTES.md`.

## Fora do escopo

Hook para os outros provedores; hook de `sdd-close` que roda `fix`; qualquer bloqueio (`deny`).
