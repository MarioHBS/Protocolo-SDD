# Notes — sdd-cli 4.2.1

> Notas públicas de versão. Os projetos reais em que o kit foi avaliado aparecem como `P1`, `P2`… (ver a branch `roadmap`, `docs/roadmap/01-EVIDENCIA.md`).

## Summary (4.2.1) — 2026-09-23

- **Tema:** descoberta do discovery e atualização confiável dos projetos.
- **Adicionado:** `sdd discover` (fluxo, caminho do skill, `--check`, `--against`); skill com as escolhas de instalação; `sdd update` atualiza shims; `doctor` `manifest_eol_drift` e `sdd fix --manifest`; trilha `on hold`.
- **Corrigido:** `sdd update` tratava arquivos com fim de linha reescrito pelo Git como editados à mão e não os atualizava.
- **Migração:** aditiva; `sdd update`, depois `sdd fix --manifest`.
