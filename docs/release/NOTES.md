# Notes — sdd-cli 4.2.0

> Notas públicas de versão. Os projetos reais em que o kit foi avaliado aparecem como `P1`, `P2`… (ver a branch `roadmap`, `docs/roadmap/01-EVIDENCIA.md`).

## Summary (4.2.0) — implementada em branch (aguarda aprovação para merge)

- **Tema:** entrada do projeto (discovery), critérios de aceitação com fonte única e dashboard sem terminal — guiada por P1 (IP-005, IP-010) e P2 (IP-001, IP-002).
- **Adicionado:**
  - `sdd-discover` (skill fora de projeto) gera `discovery.md` e `discovery.json` (`sdd-discovery/v1`); `sdd init PATH --discovery FILE.json` valida, mostra prévia e pede confirmação;
  - `sdd migrate --edd-source-of-truth`: conversão EDD explícita, com prévia e idempotente; stages ambíguas só são reportadas;
  - `sdd dashboard --ui web [--out FILE]`: HTML autocontido e somente leitura (padrão `.sdd/dashboard.html`), sem servidor nem dependências; recria o arquivo a cada execução.
- **Mudado:** templates EDD tratam `evals.md` como lista autoritativa de `E-NNN`; o relatório usa os mesmos IDs; `.markdownlint.json` na raiz do repositório.
- **Corrigido:** `sdd migrate --dry-run` anunciava a remoção de qualquer `AGENTS.md`, inclusive um escrito à mão (P2 IP-002); prévia e execução agora compartilham `_stale_shims`.
- **Migração:** aditiva; projetos EDD já em andamento convertem com `sdd migrate --edd-source-of-truth`.
