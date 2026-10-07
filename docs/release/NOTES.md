# Notes — sdd-cli 4.3.2

- 223 testes passam; `ruff` limpo.
- `antologias_bilo_app` (v4.3.1): `sdd update --dry-run` lista `.sdd/README.md` e
  `templates/track-state.template.md`; `sdd doctor` emite `managed_file_edited`. O README dele já
  contém a seção "Who rules when artifacts disagree" (corrigido depois da 4.3.1), por isso
  `readme_anchor_missing` não dispara ali; coberto por fixture.
- Os outros quatro projetos não têm arquivo gerenciado divergente.
