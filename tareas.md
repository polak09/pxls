# Tareas

Plan del proyecto descompuesto en tareas individuales y medibles. Es el fichero de seguimiento: dice qué está hecho, qué está en curso y qué falta. No es normativo; lo normativo son la constitución y las specs.

## Cómo se usa

- Cada tarea tiene un ID `T-NNN` que no se reutiliza, un responsable y un criterio **Hecho cuando** comprobable.
- Las fases se ejecutan en orden y, dentro de cada fase, también las tareas.
- **Cuando se asigna una tarea a un agente de IA, el agente actualiza este fichero**: la marca 🔄 al empezar, ✅ al cumplir su criterio (o ⛔ con el motivo si se bloquea), actualiza *Dónde estamos* y añade una línea al *Registro*.
- Sólo hay una tarea 🔄 por responsable a la vez.
- Las tareas de las fases 3 a 9 son una primera descomposición. Cuando su spec queda aprobada se refinan: se dividen, se añaden o se retiran. Una tarea retirada se tacha (`~~T-NNN~~`), no se borra.
- Al cerrar cualquier fase de producto se puede publicar una versión intermedia en `main`; se añade como tarea.

**Leyenda:** ⬜ pendiente · 🔄 en curso · ✅ hecha · ⛔ bloqueada · ~~tachada~~ retirada (no cuenta en los totales)

### Criterios estándar

Varias tareas se repiten en cada fase. Su criterio *Hecho cuando* es siempre el mismo:

| Tarea | Hecho cuando |
|---|---|
| **Aprobar** | La spec no contiene `[NEEDS CLARIFICATION]` y Bartosz ha pasado todos sus requisitos a `approved`. |
| **Implementar** | Los tests, marcados con sus IDs, se escribieron primero y se vieron fallar; ahora pasan, junto con el criterio propio de la tarea, y la verificación rápida pasa. |
| **Cerrar** | Todos los requisitos de la spec están `implemented`, la mejora ha salido de `mejoras.md`, la verificación completa pasa y la lista del Anexo C de la constitución está revisada. |
| **Integrar** | `dev` contiene un único commit con todo el trabajo de la fase y sus trailers, y los hooks lo han aceptado. |

Hasta que existan `spec-anchor` y los hooks (T-019 a T-021), la verificación es manual: se ejecutan a mano las puertas disponibles y se revisa la lista del Anexo C.

---

## Dónde estamos

- **En curso:** —
- **Siguiente:** T-023 (Bartosz): commit de la fase 2 en `dev`. Pendiente de Bartosz: T-006.
- **Bloqueos:** —

| Fase | Hechas |
|---|---|
| 0 · Gobierno del proyecto | 5 / 6 |
| 1 · Base técnica | 4 / 4 |
| 2 · MEJ-001 · `spec-anchor` y hooks | 11 / 12 |
| 3 · MEJ-002 · Esqueleto y ejecutable | 0 / 7 |
| 4 · MEJ-003 · Modelo de color y formatos | 0 / 8 |
| 5 · MEJ-004 · Cuentagotas de pantalla | 0 / 9 |
| 6 · MEJ-005 · Selector visual | 0 / 9 |
| 7 · MEJ-006 · Portapapeles | 0 / 6 |
| 8 · MEJ-007 · Historial | 0 / 8 |
| 9 · MEJ-008 · Paletas de color | 0 / 9 |
| 10 · Primera versión | 0 / 2 |
| **Total** | **20 / 80** |

---

## Fase 0 · Gobierno del proyecto

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-001 | Redactar y ratificar la constitución | Bartosz + IA | `CONSTITUTION.md` v1.0.0 en estado RATIFICADA. | ✅ |
| T-002 | Crear el backlog inicial | IA | `mejoras.md` contiene MEJ-001 a MEJ-008. | ✅ |
| T-003 | Descomponer el proyecto en tareas | IA | Este fichero existe y cada mejora de `mejoras.md` tiene su fase. | ✅ |
| T-004 | Ratificar la enmienda 1.1.0: `tareas.md` y ficheros no anclados en `behavior`/`refactor` | Bartosz + IA | `CONSTITUTION.md` v1.1.0 en estado RATIFICADA. | ✅ |
| T-005 | Integrar los ficheros de gobierno en `dev` | Bartosz | `dev` contiene un commit `Change-Type: constitution` con `CONSTITUTION.md`, `mejoras.md` y `tareas.md`, y `git status` está limpio. | ✅ |
| T-006 | Corregir el upstream de `dev` (hoy apunta a `origin/main`) y publicar `dev` en GitHub | Bartosz | `git status -sb` muestra `dev...origin/dev`. | ⬜ |

## Fase 1 · Base técnica

Clase `chore`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-007 | Crear el proyecto `uv` | IA | Existen `pyproject.toml` (Python 3.13, paquete `pxls` en `src/`), `uv.lock`, `.gitignore` y las carpetas `src/pxls/core`, `src/pxls/adapters`, `src/pxls/ui`, `tests/` y `tools/`; `uv sync` y `uv run python -c "import pxls"` terminan sin error. | ✅ |
| T-008 | Configurar formato, lint y tipos | IA | `uv run ruff format --check`, `uv run ruff check` y `uv run mypy` (con `strict` en `pyproject.toml`) pasan sin avisos. | ✅ |
| T-009 | Configurar tests y cobertura | IA | `pytest` tiene el marcador `spec` registrado y `--strict-markers` activo (`uv run pytest --markers` lo lista); Hypothesis está instalado; la cobertura por ramas tiene configurados los umbrales del Artículo X (`core` ≥ 95 %, total ≥ 85 %). | ✅ |
| T-010 | Configurar los contratos de arquitectura | IA | `import-linter` tiene los contratos del Artículo VIII (`core` no importa `adapters`, `ui` ni PySide6; `adapters` no importa `ui`) y `uv run lint-imports` pasa. | ✅ |
| ~~T-011~~ | ~~Integrar la base técnica~~ | Bartosz | Retirada: la base técnica va en el commit de T-023. | — |

## Fase 2 · MEJ-001 · Checker `spec-anchor` y hooks

Spec `specs/spec-anchor/spec.md` · prefijo `ANCH`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-012 | Redactar la spec en `draft` | IA | La spec tiene todas las secciones del Artículo V, y cada invariante (INV-1 a INV-7), cada clase de cambio, los trailers, los dos niveles de verificación y las dos capas de cumplimiento tienen al menos un requisito. Las dudas quedan como `[NEEDS CLARIFICATION]`. | ✅ |
| T-013 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ✅ |
| T-014 | Escribir el diseño | IA | `specs/spec-anchor/design.md` describe los módulos, la interfaz de línea de comandos, el formato de los errores y justifica cada dependencia. | ✅ |
| T-015 | Implementar la lectura de specs e INV-1 | IA | *Implementar* + detecta IDs duplicados o mal formados y `[NEEDS CLARIFICATION]` en requisitos `approved` o `implemented`. | ✅ |
| T-016 | Implementar la lectura de tests y código e INV-2 a INV-4 | IA | *Implementar* + detecta tests sin marcador, módulos sin `Spec:` y referencias a IDs inexistentes, `retired` o `MEJ`. | ✅ |
| T-017 | Implementar INV-5 a INV-7 | IA | *Implementar* + detecta requisitos `implemented` sin test o sin módulo, requisitos `draft`/`approved` y tests que fallan. | ✅ |
| T-018 | Implementar las reglas de clase de cambio y los trailers | IA | *Implementar* + para cada una de las 5 clases hay al menos un caso válido y uno inválido probados, y se rechazan los trailers ausentes o mal formados. | ✅ |
| T-019 | Implementar la verificación rápida y la completa | IA | *Implementar* + los dos niveles se ejecutan desde la línea de comandos, devuelven 0 si todo está bien y un código distinto con un informe legible si no. La completa ejecuta todas las puertas del Artículo X disponibles; el empaquetado se añade en T-028. Cubre ANCH-030 a ANCH-037. | ✅ |
| T-020 | Implementar los hooks de git | IA | *Implementar* + un único comando instala `pre-commit`, `pre-merge-commit` y `commit-msg`; se rechaza un commit con un test sin marcador y un commit sin trailers. Cubre ANCH-028, ANCH-029 y ANCH-038 a ANCH-041. | ✅ |
| T-021 | Implementar la integración con Claude Code | IA | *Implementar* + `CLAUDE.md` remite a la constitución y a `tareas.md`; un hook de fin de turno ejecuta la verificación rápida; se bloquean `--no-verify` y los commits hechos por el agente. Cada regla está probada con un caso que pasa y uno que falla. Cubre ANCH-042 a ANCH-047. | ✅ |
| T-022 | Cerrar MEJ-001 | IA | Criterio estándar *Cerrar*. | ✅ |
| T-023 | Integrar MEJ-001 | Bartosz | Criterio estándar *Integrar* (`Change-Type: behavior`), ya con los hooks nuevos instalados. El commit incluye también la base técnica de la fase 1. | ⬜ |

## Fase 3 · MEJ-002 · Esqueleto de la aplicación y ejecutable

Spec `specs/app-shell/spec.md` · prefijo `APP`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-024 | Redactar la spec en `draft` | IA | La spec cubre el arranque, la ventana principal (título, tamaño, icono), la versión visible y la prueba de humo. | ⬜ |
| T-025 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-026 | Escribir el diseño | IA | `design.md` justifica PySide6 y PyInstaller, decide entre un único `.exe` o una carpeta y define cómo se ejecuta la prueba de humo. | ⬜ |
| T-027 | Implementar la ventana principal | IA | *Implementar* (con `pytest-qt`) + `uv run pxls` abre la ventana. | ⬜ |
| T-028 | Implementar el empaquetado | IA | *Implementar* + un comando genera `pxls.exe`, el ejecutable supera la prueba de humo y el empaquetado forma parte de la verificación completa. | ⬜ |
| T-029 | Cerrar MEJ-002 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-030 | Integrar MEJ-002 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 4 · MEJ-003 · Modelo de color y formatos

Spec `specs/color-model/spec.md` · prefijo `COLOR`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-031 | Redactar la spec en `draft` | IA | La spec cubre HEX `#RRGGBBAA`, RGB, HSL y HSV con alfa: validación, redondeo, formato de salida y casos límite. | ⬜ |
| T-032 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*, con las dudas de MEJ-003 resueltas (`#RRGGBB`/`#RGB`, alfa, redondeo). | ⬜ |
| T-033 | Implementar el color RGBA y HEX | IA | *Implementar* + ejemplos y propiedad de ida y vuelta HEX ↔ color (Hypothesis). | ⬜ |
| T-034 | Implementar RGB | IA | *Implementar* + leer y escribir RGB con y sin alfa según la spec. | ⬜ |
| T-035 | Implementar HSL | IA | *Implementar* + ejemplos y propiedad de ida y vuelta RGB ↔ HSL dentro de la tolerancia aprobada. | ⬜ |
| T-036 | Implementar HSV | IA | *Implementar* + ejemplos y propiedad de ida y vuelta RGB ↔ HSV dentro de la tolerancia aprobada. | ⬜ |
| T-037 | Cerrar MEJ-003 | IA | Criterio estándar *Cerrar*, con cobertura de `core` ≥ 95 %. | ⬜ |
| T-038 | Integrar MEJ-003 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 5 · MEJ-004 · Cuentagotas de pantalla

Spec `specs/screen-picker/spec.md` · prefijo `PICK`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-039 | Redactar la spec en `draft` | IA | La spec cubre activar, apuntar, capturar y cancelar; la lupa; varios monitores y escalado de pantalla; y el panel del color actual. | ⬜ |
| T-040 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-041 | Escribir el diseño | IA | `design.md` decide el método de captura (Qt o API de Windows), el tratamiento de coordenadas y DPI, y define el puerto de captura. | ⬜ |
| T-042 | Implementar la lectura del color de un píxel | IA | *Implementar* + tests del puerto con un *fake* y un test de integración que pinta un color conocido en pantalla y lo lee. | ⬜ |
| T-043 | Implementar el modo cuentagotas | IA | *Implementar* + un clic captura el color del píxel bajo el cursor y Esc cancela sin cambiar el color actual. | ⬜ |
| T-044 | Implementar la lupa | IA | *Implementar* + la lupa muestra la zona ampliada alrededor del cursor con el píxel central resaltado. | ⬜ |
| T-045 | Implementar el panel del color actual | IA | *Implementar* + la ventana muestra la muestra del color y sus valores en los cuatro formatos, y se actualiza al capturar. | ⬜ |
| T-046 | Cerrar MEJ-004 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-047 | Integrar MEJ-004 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 6 · MEJ-005 · Selector visual

Spec `specs/visual-picker/spec.md` · prefijo `SEL`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-048 | Redactar la spec en `draft` | IA | La spec cubre el cuadrado de saturación y brillo, la barra de tono, el alfa, los controles por componente y la sincronía con el color actual. | ⬜ |
| T-049 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-050 | Escribir el diseño | IA | `design.md` describe los widgets propios y el modelo interno del selector. | ⬜ |
| T-051 | Implementar el cuadrado de saturación y brillo y la barra de tono | IA | *Implementar* + pulsar y arrastrar actualizan el color según los criterios de aceptación. | ⬜ |
| T-052 | Implementar el alfa y los controles por componente | IA | *Implementar* + cada control modifica sólo su componente. | ⬜ |
| T-053 | Implementar la edición manual de valores, si la spec la incluye | IA | *Implementar* + un valor válido escrito en cualquier formato cambia el color, y uno inválido se rechaza según la spec. | ⬜ |
| T-054 | Implementar la sincronía con el color actual | IA | *Implementar* + capturar con el cuentagotas actualiza el selector, y mover el selector actualiza el panel del color actual. | ⬜ |
| T-055 | Cerrar MEJ-005 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-056 | Integrar MEJ-005 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 7 · MEJ-006 · Copiar al portapapeles

Spec `specs/clipboard/spec.md` · prefijo `CLIP`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-057 | Redactar la spec en `draft` | IA | La spec cubre la elección de formato, el formato por defecto, el atajo de teclado y la confirmación visual. | ⬜ |
| T-058 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-059 | Implementar el puerto y el adaptador de portapapeles | IA | *Implementar* + tests con un *fake* y un test de integración que escribe y lee el portapapeles de Windows. | ⬜ |
| T-060 | Implementar la acción de copiar | IA | *Implementar* + el texto copiado coincide con el formato elegido para todos los ejemplos de la spec, tanto con el botón como con el atajo. | ⬜ |
| T-061 | Cerrar MEJ-006 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-062 | Integrar MEJ-006 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 8 · MEJ-007 · Historial

Spec `specs/history/spec.md` · prefijo `HIST`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-063 | Redactar la spec en `draft` | IA | La spec cubre qué entra en el historial, el límite, los duplicados, el borrado, la recuperación de un color y la persistencia entre sesiones. | ⬜ |
| T-064 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-065 | Escribir el diseño | IA | `design.md` decide dónde y en qué formato se guarda el historial y cómo se trata un fichero dañado. | ⬜ |
| T-066 | Implementar el historial en el dominio | IA | *Implementar* + límite, orden y duplicados según la spec, en `core`. | ⬜ |
| T-067 | Implementar la persistencia del historial | IA | *Implementar* + guardar y volver a cargar desde una instancia nueva produce el mismo historial, y un fichero dañado se trata según la spec. | ⬜ |
| T-068 | Implementar la vista del historial | IA | *Implementar* + elegir una entrada la convierte en el color actual. | ⬜ |
| T-069 | Cerrar MEJ-007 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-070 | Integrar MEJ-007 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 9 · MEJ-008 · Paletas de color

Spec `specs/palettes/spec.md` · prefijo `PAL`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-071 | Redactar la spec en `draft` | IA | La spec cubre crear, renombrar y borrar paletas; añadir, quitar y reordenar colores; límites; persistencia; y exportar e importar si procede. | ⬜ |
| T-072 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-073 | Escribir el diseño | IA | `design.md` decide el formato de almacenamiento y, si procede, los formatos de exportación. | ⬜ |
| T-074 | Implementar las paletas en el dominio | IA | *Implementar* + todas las operaciones de la spec, en `core`. | ⬜ |
| T-075 | Implementar la persistencia de paletas | IA | *Implementar* + guardar y volver a cargar desde una instancia nueva produce las mismas paletas. | ⬜ |
| T-076 | Implementar la vista de paletas | IA | *Implementar* + todas las operaciones de la spec se pueden hacer desde la interfaz. | ⬜ |
| T-077 | Implementar exportar e importar, si la spec lo incluye | IA | *Implementar* + exportar e importar de nuevo produce la misma paleta en cada formato aprobado. | ⬜ |
| T-078 | Cerrar MEJ-008 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-079 | Integrar MEJ-008 | Bartosz | Criterio estándar *Integrar*. | ⬜ |

## Fase 10 · Primera versión

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-080 | Preparar la primera versión | IA | El número de versión está decidido por Bartosz y aplicado en el proyecto, las notas de la versión están escritas y el `.exe` generado desde `dev` supera la prueba de humo. | ⬜ |
| T-081 | Publicar la primera versión en `main` | Bartosz | `main` contiene `git merge --no-ff dev`, la etiqueta `vX.Y.Z` existe y el `.exe` está adjunto a la versión en GitHub. | ⬜ |

---

## Registro

Las entradas más recientes van primero.

- 2026-10-25 · T-022 · Completada: Bartosz aprueba el nuevo texto de ANCH-013 y pasa a `implemented`; los 47 requisitos de `specs/spec-anchor/spec.md` están `implemented` y la verificación rápida da 0 errores. La completa se ejecutará en el hook del commit de T-023.
- 2026-10-25 · T-022 · 46 requisitos pasan a `implemented` y MEJ-001 sale de `mejoras.md`. La verificación completa de la fase (suite entera, cobertura 94 %) sólo da INV-6 por ANCH-013. El checker destapó que las listas `Spec:` partidas en dos líneas perdían IDs (ANCH-017 y ANCH-027): se propone ampliar ANCH-013 con líneas de continuación (en `draft`). ANCH-042 se ancla en `claude.py`. Anexo C revisado: 98 criterios de aceptación con test.
- 2026-10-25 · T-022 · Asignada a la IA.
- 2026-10-25 · Bartosz instala los hooks de git en el clon; la verificación rápida da 0 errores.
- 2026-10-25 · T-021 · Completada: `CLAUDE.md`, configuración de Claude Code y `spec_anchor.claude` (ANCH-042 a ANCH-047); 32 tests vistos en rojo y luego en verde. Los hooks se activaron en la misma sesión y bloquearon dos comandos reales del agente (ANCH-046 y ANCH-045).
- 2026-10-25 · Bartosz aprueba el nuevo texto de ANCH-022 (exención de los módulos sin definiciones); vuelve a `approved`.
- 2026-10-25 · T-020 · Completada: `hooks` (instalación, hooks ajenos, aviso de hooks no instalados) y `spec-anchor hook` para `pre-commit`, `pre-merge-commit` y `commit-msg` (ANCH-028, ANCH-029, ANCH-038 a ANCH-041); probados con commits y merges reales en repositorios temporales; 151 tests. Hallazgos: ANCH-022 contradecía la exención de la constitución III.3 (propuesto nuevo texto, en `draft`); `pre-merge-commit` no dispone de `MERGE_HEAD`; las puertas eliminan las variables `GIT_*` para no tocar el repositorio real.
- 2026-10-25 · Acordado con Bartosz: la suite completa se ejecuta una vez por fase; durante las tareas, sólo los tests nuevos.
- 2026-10-25 · T-019 · Completada: comando `spec-anchor check --quick/--full` (ANCH-030 a ANCH-037); 133 tests, cobertura 98 %. Sobre el propio repositorio la rápida da 0 errores en 0,75 s y la completa sólo los 47 INV-6 esperados (requisitos aún `approved`).
- 2026-10-25 · T-018 · Completada: `changes` con trailers y reglas de las 5 clases (ANCH-019 a ANCH-027); 106 tests vistos en rojo y luego en verde, cobertura 99,85 %. Requisitos ANCH con tests: 27 de 47; los restantes quedan repartidos explícitamente entre T-019, T-020 y T-021.
- 2026-10-25 · T-017 · Completada: INV-5 a INV-7 (ANCH-016 a ANCH-018) en `invariants` y `gates.run_tests`; 64 tests vistos en rojo y luego en verde, cobertura 99,8 %.
- 2026-10-25 · T-011 · Retirada por decisión de Bartosz: la base técnica se integra en el commit `behavior` de T-023.
- 2026-10-24 · T-016 · Completada: `pyrefs` y comprobaciones INV-2 a INV-4 (ANCH-011 a ANCH-015); 53 tests vistos en rojo y luego en verde, cobertura 99,7 %. El propio repositorio pasa INV-1 a INV-4 sin errores.
- 2026-10-24 · T-015 · Completada: `model`, `tree`, `specs` e `invariants` (ANCH-001 a ANCH-010); 31 tests vistos en rojo y luego en verde, cobertura 99,6 %, todas las puertas pasan. Lee la spec real sin errores.
- 2026-10-24 · T-014 · Completada: `specs/spec-anchor/design.md` (sin dependencias de ejecución, 12 módulos, CLI y reparto entre hooks).
- 2026-10-24 · T-013 · Completada: Bartosz aprueba `specs/spec-anchor/spec.md`; sus 47 requisitos pasan a `approved`.
- 2026-10-24 · T-013 · Bartosz acepta las propuestas de la IA para las 9 dudas; la IA las aplica a `specs/spec-anchor/spec.md` (0 dudas abiertas). La duda de ANCH-043 se separa en un requisito nuevo, ANCH-047: 47 requisitos, todos en `draft`.
- 2026-10-24 · T-012 · Completada: `specs/spec-anchor/spec.md` con 46 requisitos en `draft`, trazabilidad completa con la constitución y 9 dudas abiertas.
- 2026-10-24 · T-008 a T-010 · Completadas: ruff, mypy strict, pytest con marcador `spec`, cobertura (total 85 %; el 95 % de `core` lo aplicará T-019) e import-linter pasan.
- 2026-10-24 · T-007 · Completada: proyecto `uv` con Python 3.13.15, `uv sync` e `import pxls` sin errores.
- 2026-10-24 · T-005 · Completada: commit `3c668e8` en `dev`.
- 2026-10-24 · Enmienda 2.0.0 de la constitución: sin ramas de trabajo, todo en `dev`; tareas adaptadas.
- 2026-10-24 · T-004 · Completada: enmienda 1.1.0 ratificada por Bartosz y aplicada por la IA en `CONSTITUTION.md`.
- 2026-10-24 · T-003 · Asignada a la IA y completada: plan de 81 tareas en 11 fases.
- 2026-10-24 · T-002 · Completada: `mejoras.md` con MEJ-001 a MEJ-008.
- 2026-10-24 · T-001 · Completada: constitución v1.0.0 ratificada.
