# Modelo de item

```markdown
### <ID> — <título curto>

- **Status:** planejado
- **Origem:** <projeto>/<IP> — episódio real em uma ou duas frases
- **Evidência:** <arquivo:linha no kit, ou dado medido no projeto>
- **Causa raiz:** <por que acontece>
- **Solução provável:** <caminho de partida; a definitiva é decidida ao implementar>
- **Riscos e testes:** <o que pode quebrar; fixture que reproduz o episódio>
- **Dependências:** <outros itens ou decisões>
- **Propaga por:** <`sdd update` / `sdd migrate` / só código>
```

Regras: o item descreve o problema, não a implementação final; cita o episódio real, não uma
sugestão genérica; se a evidência for parcial, diz qual parte não foi confirmada.
