# Tareas

Plan del proyecto descompuesto en tareas individuales y medibles. Es el fichero de seguimiento: dice qué está hecho, qué está en curso y qué falta. No es normativo; lo normativo son la constitución y las specs.

## Cómo se usa

- Cada tarea tiene un ID `T-NNN` que no se reutiliza, un responsable y un criterio **Hecho cuando** comprobable.
- Las fases se ejecutan en orden y, dentro de cada fase, también las tareas.
- **Cuando se asigna una tarea a un agente de IA, el agente actualiza este fichero**: la marca 🔄 al empezar, ✅ al cumplir su criterio (o ⛔ con el motivo si se bloquea), actualiza *Dónde estamos* y añade una línea al *Registro*.
- Sólo hay una tarea 🔄 por responsable a la vez.
- Las tareas de las fases 3 a 9 son una primera descomposición. Cuando su spec queda aprobada se refinan: se dividen, se añaden o se retiran. Una tarea retirada se tacha (`~~T-NNN~~`), no se borra.
- Al cerrar cualquier fase de producto se puede publicar una versión intermedia en `main`; se añade como tarea.

**Leyenda:** ⬜ pendiente · 🔄 en curso · ✅ hecha · ⛔ bloqueada

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
- **Siguiente:** T-005 y T-006 (Bartosz).
- **Bloqueos:** —

| Fase | Hechas |
|---|---|
| 0 · Gobierno del proyecto | 4 / 6 |
| 1 · Base técnica | 0 / 5 |
| 2 · MEJ-001 · `spec-anchor` y hooks | 0 / 12 |
| 3 · MEJ-002 · Esqueleto y ejecutable | 0 / 7 |
| 4 · MEJ-003 · Modelo de color y formatos | 0 / 8 |
| 5 · MEJ-004 · Cuentagotas de pantalla | 0 / 9 |
| 6 · MEJ-005 · Selector visual | 0 / 9 |
| 7 · MEJ-006 · Portapapeles | 0 / 6 |
| 8 · MEJ-007 · Historial | 0 / 8 |
| 9 · MEJ-008 · Paletas de color | 0 / 9 |
| 10 · Primera versión | 0 / 2 |
| **Total** | **4 / 81** |

---

## Fase 0 · Gobierno del proyecto

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-001 | Redactar y ratificar la constitución | Bartosz + IA | `CONSTITUTION.md` v1.0.0 en estado RATIFICADA. | ✅ |
| T-002 | Crear el backlog inicial | IA | `mejoras.md` contiene MEJ-001 a MEJ-008. | ✅ |
| T-003 | Descomponer el proyecto en tareas | IA | Este fichero existe y cada mejora de `mejoras.md` tiene su fase. | ✅ |
| T-004 | Ratificar la enmienda 1.1.0: `tareas.md` y ficheros no anclados en `behavior`/`refactor` | Bartosz + IA | `CONSTITUTION.md` v1.1.0 en estado RATIFICADA. | ✅ |
| T-005 | Integrar los ficheros de gobierno en `dev` | Bartosz | `dev` contiene un commit `Change-Type: constitution` con `CONSTITUTION.md`, `mejoras.md` y `tareas.md`, y `git status` está limpio. | ⬜ |
| T-006 | Corregir el upstream de `dev` (hoy apunta a `origin/main`) y publicar `dev` en GitHub | Bartosz | `git status -sb` muestra `dev...origin/dev`. | ⬜ |

## Fase 1 · Base técnica

Clase `chore`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-007 | Crear el proyecto `uv` | IA | Existen `pyproject.toml` (Python 3.13, paquete `pxls` en `src/`), `uv.lock`, `.gitignore` y las carpetas `src/pxls/core`, `src/pxls/adapters`, `src/pxls/ui`, `tests/` y `tools/`; `uv sync` y `uv run python -c "import pxls"` terminan sin error. | ⬜ |
| T-008 | Configurar formato, lint y tipos | IA | `uv run ruff format --check`, `uv run ruff check` y `uv run mypy` (con `strict` en `pyproject.toml`) pasan sin avisos. | ⬜ |
| T-009 | Configurar tests y cobertura | IA | `pytest` tiene el marcador `spec` registrado y `--strict-markers` activo (`uv run pytest --markers` lo lista); Hypothesis está instalado; la cobertura por ramas tiene configurados los umbrales del Artículo X (`core` ≥ 95 %, total ≥ 85 %). | ⬜ |
| T-010 | Configurar los contratos de arquitectura | IA | `import-linter` tiene los contratos del Artículo VIII (`core` no importa `adapters`, `ui` ni PySide6; `adapters` no importa `ui`) y `uv run lint-imports` pasa. | ⬜ |
| T-011 | Integrar la base técnica | Bartosz | Criterio estándar *Integrar* (`Change-Type: chore`). | ⬜ |

## Fase 2 · MEJ-001 · Checker `spec-anchor` y hooks

Spec `specs/spec-anchor/spec.md` · prefijo `ANCH`.

| ID | Tarea | Quién | Hecho cuando | Estado |
|---|---|---|---|---|
| T-012 | Redactar la spec en `draft` | IA | La spec tiene todas las secciones del Artículo V, y cada invariante (INV-1 a INV-7), cada clase de cambio, los trailers, los dos niveles de verificación y las dos capas de cumplimiento tienen al menos un requisito. Las dudas quedan como `[NEEDS CLARIFICATION]`. | ⬜ |
| T-013 | Aprobar la spec | Bartosz | Criterio estándar *Aprobar*. | ⬜ |
| T-014 | Escribir el diseño | IA | `specs/spec-anchor/design.md` describe los módulos, la interfaz de línea de comandos, el formato de los errores y justifica cada dependencia. | ⬜ |
| T-015 | Implementar la lectura de specs e INV-1 | IA | *Implementar* + detecta IDs duplicados o mal formados y `[NEEDS CLARIFICATION]` en requisitos `approved` o `implemented`. | ⬜ |
| T-016 | Implementar la lectura de tests y código e INV-2 a INV-4 | IA | *Implementar* + detecta tests sin marcador, módulos sin `Spec:` y referencias a IDs inexistentes, `retired` o `MEJ`. | ⬜ |
| T-017 | Implementar INV-5 a INV-7 | IA | *Implementar* + detecta requisitos `implemented` sin test o sin módulo, requisitos `draft`/`approved` y tests que fallan. | ⬜ |
| T-018 | Implementar las reglas de clase de cambio y los trailers | IA | *Implementar* + para cada una de las 5 clases hay al menos un caso válido y uno inválido probados, y se rechazan los trailers ausentes o mal formados. | ⬜ |
| T-019 | Implementar la verificación rápida y la completa | IA | *Implementar* + los dos niveles se ejecutan desde la línea de comandos, devuelven 0 si todo está bien y un código distinto con un informe legible si no. La completa ejecuta todas las puertas del Artículo X disponibles; el empaquetado se añade en T-028. | ⬜ |
| T-020 | Implementar los hooks de git | IA | *Implementar* + un único comando instala `pre-commit`, `pre-merge-commit` y `commit-msg`; se rechaza un commit con un test sin marcador y un commit sin trailers. | ⬜ |
| T-021 | Implementar la integración con Claude Code | IA | *Implementar* + `CLAUDE.md` remite a la constitución y a `tareas.md`; un hook de fin de turno ejecuta la verificación rápida; se bloquean `--no-verify` y los commits hechos por el agente. Cada regla está probada con un caso que pasa y uno que falla. | ⬜ |
| T-022 | Cerrar MEJ-001 | IA | Criterio estándar *Cerrar*. | ⬜ |
| T-023 | Integrar MEJ-001 | Bartosz | Criterio estándar *Integrar* (`Change-Type: behavior`), ya con los hooks nuevos instalados. | ⬜ |

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

- 2026-10-24 · Enmienda 2.0.0 de la constitución: sin ramas de trabajo, todo en `dev`; tareas adaptadas.
- 2026-10-24 · T-004 · Completada: enmienda 1.1.0 ratificada por Bartosz y aplicada por la IA en `CONSTITUTION.md`.
- 2026-10-24 · T-003 · Asignada a la IA y completada: plan de 81 tareas en 11 fases.
- 2026-10-24 · T-002 · Completada: `mejoras.md` con MEJ-001 a MEJ-008.
- 2026-10-24 · T-001 · Completada: constitución v1.0.0 ratificada.
