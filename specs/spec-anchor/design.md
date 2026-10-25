# Diseño de `spec-anchor`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Dependencias de ejecución | **Ninguna**: sólo la biblioteca estándar (`ast`, `re`, `subprocess`, `tomllib`, `json`, `argparse`). | PyYAML para la cabecera (innecesario: ANCH-002 sólo admite `clave: valor`); GitPython (una dependencia más para lo que resuelve `git` por línea de comandos). |
| Ubicación | Paquete `spec_anchor` en `tools/spec_anchor/`, instalado junto a `pxls` por el mismo `pyproject.toml`, con el comando `spec-anchor`. | Un workspace de `uv` con proyecto propio (más ficheros y configuración para un único paquete interno). |
| Lectura de Python | `ast`: no importa ni ejecuta el código analizado. | Importar los módulos (ejecutaría código y obligaría a que todo importe sin errores) o expresiones regulares (frágiles con decoradores y docstrings). |
| Lectura de Markdown | Expresiones regulares línea a línea sobre la estructura fija del Artículo V. | Un parser de Markdown (dependencia sin beneficio: la estructura que se lee es mínima). |
| Herramientas de calidad | Se ejecutan como subprocesos con el mismo intérprete (`python -m ruff`, `python -m mypy`…). | Llamar a sus API internas (no son estables). |

## Módulos

| Módulo | Responsabilidad | Requisitos |
|---|---|---|
| `model.py` | Tipos inmutables: `Finding`, `Requirement`, `Spec`, `CaseRef` (un test), `ModuleRef`. | ANCH-001 a ANCH-016 |
| `tree.py` | Puerto `Tree` (listar y leer ficheros) con dos implementaciones: `DiskTree` (copia de trabajo) y `GitTree` (una revisión o el índice). | ANCH-001, ANCH-021 a ANCH-026 |
| `specs.py` | Descubre y lee specs: cabecera, requisitos, estados, texto normativo. | ANCH-001 a ANCH-005, ANCH-008, ANCH-010 |
| `pyrefs.py` | Lee marcadores `spec` de los tests y líneas `Spec:` de los módulos. | ANCH-011, ANCH-013 |
| `invariants.py` | Comprueba INV-1 a INV-6 sobre specs y referencias. | ANCH-004, ANCH-006, ANCH-007, ANCH-009, ANCH-012, ANCH-014 a ANCH-017 |
| `changes.py` | Trailers y reglas de clase comparando dos `Tree` (antes y después). | ANCH-019 a ANCH-027 |
| `git.py` | Rama actual, merge en curso, cambios sin preparar, ruta de los hooks. | ANCH-028, ANCH-029, ANCH-034 |
| `gates.py` | Puertas externas: formato, lint, tipos, tests, cobertura, arquitectura, empaquetado. | ANCH-018, ANCH-030 a ANCH-033 |
| `report.py` | Formato de los errores y código de salida. | ANCH-035, ANCH-036 |
| `hooks.py` | Instalación y comprobación de los hooks de git. | ANCH-038, ANCH-039, ANCH-041 |
| `claude.py` | Hooks de Claude Code: fin de turno y guarda de comandos y ediciones. | ANCH-043 a ANCH-047 |
| `cli.py` | Punto de entrada `spec-anchor` y orquestación de los niveles. | ANCH-030, ANCH-031, ANCH-040 |

`CLAUDE.md` y `.claude/settings.json` son ficheros del repositorio que satisfacen ANCH-042 a ANCH-046.

## Interfaz de línea de comandos

```text
spec-anchor check --quick            # verificación rápida sobre la copia de trabajo
spec-anchor check --full             # verificación completa, sin reglas de commit
spec-anchor hook pre-commit          # llamado por git
spec-anchor hook pre-merge-commit    # llamado por git
spec-anchor hook commit-msg <fich>   # llamado por git
spec-anchor install                  # instala los hooks de git
spec-anchor claude stop              # hook Stop de Claude Code (JSON por stdin)
spec-anchor claude guard             # hook PreToolUse de Claude Code (JSON por stdin)
```

Todos terminan con 0 si no hay errores y 1 si los hay (ANCH-036). Los hooks de Claude Code siguen el protocolo de Claude Code: código 2 para bloquear, con el motivo por la salida de error.

## Reparto de la verificación entre hooks

| Hook | En `dev` | En `main` |
|---|---|---|
| `pre-commit` | ANCH-028 (rama), ANCH-034 (disco = índice) y verificación completa sin trailers. | Si no hay un merge de `dev` en curso, rechaza (ANCH-029); si lo hay (cierre de un merge con conflictos), como `pre-merge-commit`. |
| `pre-merge-commit` | Como `pre-commit`. | Si el merge no integra exactamente `dev`, rechaza (ANCH-029); si no, verificación completa sin reglas de clase. |
| `commit-msg` | Trailers y reglas de clase (ANCH-019 a ANCH-027), comparando `HEAD` con el índice. | Nada: los merges de versión no declaran clase. |

- Las reglas de clase necesitan el mensaje, que sólo existe en `commit-msg`; por eso no están en `pre-commit`.
- Un merge en `dev` no tiene una regla propia: pasa por la verificación completa y, como su mensaje por defecto no lleva trailers, `commit-msg` lo rechaza (ANCH-019) salvo que se declare su clase.
- **Origen de un merge.** Tras un conflicto, git deja `MERGE_HEAD`. Durante `pre-merge-commit` no lo escribe, pero exporta `GIT_REFLOG_ACTION=merge <ramas>`; las ramas se resuelven a commits y se comparan con `dev`.

## Formato del informe

```text
ERROR [INV-2] tests/core/test_hex.py:12 · el test test_parse no tiene marcador spec
ERROR [ANCH-021] COLOR-004 · el cambio declara COLOR-004 pero no modifica ningún test marcado con él
2 errores
```

Una línea por error: regla, ubicación si existe y mensaje en español. Sin errores, una línea `0 errores`.

## Lectura de specs

- Cabecera: primeras líneas entre dos `---`; cada línea `clave: valor`.
- Un requisito empieza en un encabezado `###` o `####` de la sección `## Requisitos` que case con `^(#{3,4}) ([A-Z]+-\d+) · (.+)$`, y acaba en el siguiente encabezado de igual o menor nivel.
- **Texto normativo**: las líneas del bloque *Enunciado* y del bloque *Criterios de aceptación*. *Estado*, *Notas* y *Motivo* no lo son. ANCH-021 compara el texto normativo de antes y de después, normalizando espacios.
- Para no confundir IDs con otras palabras en mayúsculas, el formato «bien formado» se comprueba sobre el encabezado ya reconocido (ANCH-006), no buscando IDs en el texto libre.

## Lectura de tests y código

- Tests: ficheros `tests/**/test_*.py`. Se recorren las funciones `test*` de nivel superior y los métodos `test*` de clases `Test*`. Un decorador cuenta como marcador si es una llamada cuya función termina en `mark.spec` (`pytest.mark.spec(...)` o `mark.spec(...)`) y sus argumentos son cadenas literales.
- Módulos: ficheros `.py` bajo `src/` y `tools/`. «Define funciones o clases» significa que tiene en su nivel superior algún `def`, `async def` o `class`. La línea `Spec:` se busca en el docstring del módulo; las líneas sangradas que la siguen sin línea en blanco continúan la lista (ANCH-013), para no superar los 100 caracteres por línea.
- `CLAUDE.md` es un fichero, no código: ANCH-042 se ancla en `claude.py`, el módulo de la integración con Claude Code.

## Puertas externas

| Puerta | Comando | Nivel |
|---|---|---|
| Hooks instalados | ficheros de la carpeta de hooks con la marca (ANCH-041) | Rápida |
| Formato | `python -m ruff format --check --output-format concise` | Rápida |
| Lint | `python -m ruff check --output-format concise` | Rápida |
| Tipos | `python -m mypy` | Completa |
| Tests y cobertura | `python -m pytest --cov --cov-report= --cov-fail-under=0` (el umbral lo aplica spec-anchor, no pytest-cov) | Completa |
| Cobertura total ≥ 85 % | `python -m coverage json` | Completa |
| Cobertura de `core` ≥ 95 % | `python -m coverage json --include=src/pxls/core/*` | Completa |
| Arquitectura | `lint-imports` | Completa |
| Empaquetado | Comandos definidos en `[tool.spec-anchor]` de `pyproject.toml` (claves `package` y `smoke`). Si no existen, la puerta no se ejecuta (ANCH-033). | Completa |

Casos límite: `pytest` sin tests (código 5) cuenta como verde; un `core` sin sentencias medibles no aplica su umbral.

## Hooks de git

- Se escriben en la ruta que devuelve `git rev-parse --git-path hooks`, para respetar `core.hooksPath`.
- Cada hook es un script `sh` (git para Windows los ejecuta con su propio `sh`) que contiene la marca `# managed-by: spec-anchor` y ejecuta `uv run --frozen spec-anchor hook <nombre> "$@"`.
- Un hook sin la marca es ajeno: no se toca (ANCH-039). La comprobación de ANCH-041 busca los tres ficheros con la marca.
- El comando que ejecuta el hook es configurable (`install(root, runner)`); los tests lo instalan con el intérprete de la suite, porque `uv run` no encontraría el proyecto temporal.
- **Variables `GIT_*`.** Git exporta a los hooks `GIT_INDEX_FILE`, `GIT_DIR` y otras. Todas las puertas eliminan las variables `GIT_*` del entorno de sus subprocesos: si no, los tests que crean repositorios temporales escribirían en el índice del repositorio real cuando la suite se ejecuta desde un hook.

## Claude Code

- `.claude/settings.json` declara:
  - `Stop` → `"$CLAUDE_PROJECT_DIR/.venv/Scripts/python.exe" -m spec_anchor claude stop`.
  - `PreToolUse` con `matcher` `Bash|PowerShell|Edit|Write|MultiEdit|NotebookEdit` → el mismo intérprete con `claude guard` (ANCH-044 a ANCH-046).
  - Se llama al intérprete del entorno virtual y no a `uv run`: en el entorno de Claude Code `uv` puede no estar en el `PATH`, y un hook que no arranca no bloquea nada.
- Claude Code aplica los cambios de `.claude/settings.json` en la sesión en curso: se comprobó al crear el fichero, cuando la guarda empezó a bloquear comandos de esa misma sesión.
- **Contador de bloqueos (ANCH-047).** El número de bloqueos seguidos se guarda en `.git/spec-anchor/stop-blocks`. Se pone a 0 cuando la verificación pasa. Con 2 bloqueos previos, el tercer intento termina con código 0 y un `systemMessage` que muestra el informe a la persona.
- **Detección de comandos.** Expresiones regulares sobre el texto del comando: `git` (con opciones `-C`/`-c` opcionales) seguido de `commit`, `merge`, `cherry-pick`, `revert`, `rebase` o `am`; `--no-verify`; `-n` en `git commit`; `core.hooksPath`; rutas `.git/hooks` y `.claude/settings`.
- **Limitaciones.**
  - Un alias de git o un script que haga el commit por dentro no se detecta; lo frena la verificación de los hooks de git en el siguiente commit de la persona.
  - La guarda mira el texto del comando, no su efecto: también bloquea un comando que sólo *lee* esas rutas o que contiene `git commit` como dato. Para leerlas, el agente usa la herramienta Read, que no se vigila.

## Cambios en la configuración del proyecto

- `pyproject.toml`: añadir `tools/spec_anchor` a los paquetes, el comando `spec-anchor`, `tools` a la cobertura y a mypy, y la sección `[tool.spec-anchor]`.
- Sin dependencias nuevas.
