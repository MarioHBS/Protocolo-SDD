# Instalación de SDD CLI (Español)

`sdd` es una CLI **Python** (sólo stdlib, sin dependencias) que prepara proyectos para
el flujo *Specification-Driven Development*. Funciona en **Windows**, **macOS** y
**Linux**. **No** es un paquete npm/npx — si `npx` devolvió `could not determine
executable to run`, es porque esta herramienta es Python; usa `pipx` o `uv` (abajo).

## Requisito previo

- **Python ≥ 3.12** (`python --version` / `py --version`). Las versiones anteriores se instalan "con éxito" y
  fallan en la primera ejecución con un `SyntaxError`.

## Instalación recomendada: `pipx`

`pipx` aísla la CLI en su propio entorno y pone `sdd` en el PATH automáticamente.

### Windows (PowerShell)

```powershell
# si todavía no tienes pipx:
py -m pip install --user pipx
py -m pipx ensurepath

# instala la SDD CLI (desde la carpeta descomprimida del paquete):
pipx install .\sdd-cli

# abre un terminal NUEVO (para que el PATH se recargue) y verifica:
sdd --version
```

> Si `sdd` no se reconoce en un terminal ya abierto, abre una ventana **nueva** —
> `ensurepath` sólo surte efecto en sesiones nuevas. Como alternativa:
> `py -m pipx install .\sdd-cli` invoca pipx directamente aunque el PATH no esté bien.

### macOS / Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# instala desde la carpeta descomprimida:
pipx install ./sdd-cli

# abre un terminal nuevo y:
sdd --version
```

## Instalación alternativa: `uv`

Si prefieres `uv` (más rápido, de Astral):

```bash
uv tool install ./sdd-cli          # macOS / Linux
uv tool install .\sdd-cli          # Windows (PowerShell)
```

## Verificación posterior

```bash
sdd --version      # debe imprimir la versión instalada de sdd
sdd providers      # lista los providers soportados
sdd manual         # imprime el manual completo (`sdd docs` es un alias obsoleto)
sdd manual --md SDD-USAGE.md   # escribe el manual en un archivo
```

## Opcional: el dashboard

`sdd dashboard` necesita `rich` y/o `textual`, que la instalación básica no incluye.
El kit se instala desde su carpeta, así que pide los extras allí:

```bash
pipx install --force './sdd-cli[dashboard]'      # rich + textual (en Windows usa .\sdd-cli)
# o solo un renderizador:  './sdd-cli[dashboard-rich]'  /  './sdd-cli[dashboard-textual]'
# sin extras en pipx:      pipx inject sdd-cli rich textual
sdd dashboard --ui rich
```

## Error común: `npm error could not determine executable to run`

Ocurre si ejecutas `npx install ./sdd-cli` o `npm i ./sdd-cli`. La SDD CLI **no es un
paquete Node** — es Python. Usa `pipx` o `uv` (arriba). El error confunde porque ambos
corrieron en un terminal, pero `npx` busca un `package.json` con un binario JavaScript
que no existe en este proyecto.

## Siguiente paso

Dentro de la carpeta de un proyecto:

```bash
sdd init --provider claude --language pt-BR -y
```

Luego abre tu agente (Claude Code, Cursor, etc.) en el proyecto y lanza `/sdd` (o el
disparador de tu provider — ver `sdd providers`). El agente leerá `.sdd/README.md` y
entrará en la fase INITIALIZING hablando en el idioma configurado.

## Migración de un proyecto v1

```bash
# SIEMPRE haz primero un respaldo del proyecto y ejecuta dry-run:
sdd migrate --to v2 --dry-run
sdd migrate --to v2
```

`migrate` detecta tu(s) provider(s), idioma y ediciones manuales; sólo reemplaza los
archivos *managed* (README, skills, templates, shims) y preserva `constitution.md`,
`roadmap.md` y `stages/`. Luego genera `.sdd/.migration-todo.md`: el agente conduce las
ediciones restantes de la constitución, pidiéndote confirmación **un cambio a la vez**.
