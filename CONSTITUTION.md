# Constitución de `pxls`

| | |
|---|---|
| **Versión** | 2.0.0 |
| **Estado** | RATIFICADA · en vigor |
| **Ratificada** | 2026-10-24, por la persona propietaria del producto |
| **Última enmienda** | 2026-10-24 |

Este documento es la norma suprema del proyecto. Prevalece sobre cualquier spec, plan, convención, costumbre o instrucción dada a un agente de IA. Ninguna de sus reglas puede ignorarse sin enmendarlo antes (Artículo XII).

---

## Preámbulo

`pxls` es una aplicación de escritorio para Windows, escrita en Python, que permite capturar el color de cualquier píxel de la pantalla y elegir colores con un selector visual, convertirlos entre formatos y organizarlos en un historial y en paletas.

El proyecto sigue **Spec-Driven Development en modalidad *spec-anchored***. La especificación no es un documento previo que se abandona al empezar a programar (*spec-first*), ni un artefacto del que se genera el código y que nadie edita a mano (*spec-as-source*). Es un documento vivo, escrito y mantenido por personas, **anclado** al código mediante vínculos que una máquina puede verificar en cada cambio.

La regla de oro, de la que se deriva todo lo demás:

> **Spec, tests y código cambian juntos o no cambian.**
> Si cambia el comportamiento del código, cambia la spec. Si cambia la spec, cambian los tests y el código. En `dev` y en `main` nunca hay deriva entre ellos.

## Glosario

- **Persona propietaria del producto**: Bartosz Kucmierz. Es la única con autoridad para aprobar requisitos, ratificar enmiendas e integrar cambios en las ramas integradas.
- **Capacidad**: área funcional cohesionada del sistema (p. ej. `color-model`, `screen-picker`).
- **Spec**: fichero `specs/<capacidad>/spec.md`. Describe *qué* hace el sistema y *por qué*; nunca *cómo*.
- **Requisito**: unidad normativa mínima de una spec, identificada por un ID estable (p. ej. `CONV-001`).
- **Texto normativo**: el enunciado y los criterios de aceptación de un requisito. El resto de la spec (contexto, notas, ejemplos ilustrativos) es informativo.
- **Mejora**: entrada del fichero `mejoras.md`. Describe algo que **todavía no existe** en el sistema. No es normativa.
- **Tarea**: entrada del fichero `tareas.md`, el plan del proyecto y su seguimiento. No es normativa.
- **Fichero no anclado**: todo fichero que no es spec, código anclado ni test anclado (configuración, dependencias, lockfile, hooks, `CLAUDE.md`, `mejoras.md`, `tareas.md`, documentación…).
- **Código anclado**: todo el código Python bajo `src/` y `tools/`.
- **Test anclado**: toda función de test bajo `tests/`.
- **Anclaje**: vínculo verificable por máquina entre un requisito, los tests que lo prueban y el código que lo implementa.
- **Deriva** (*drift*): cualquier discrepancia entre spec, tests y código. Es un defecto de severidad máxima.
- **Rama integrada**: `dev` o `main`. No existen ramas de trabajo: todo el desarrollo se hace en `dev`.
- **Copia de trabajo**: los cambios aún sin commitear en `dev`. Es el único lugar donde puede haber estados intermedios.
- **Integración**: cada commit en `dev`. Es la unidad de anclaje (Artículo II.4).
- **Checker**: la herramienta `spec-anchor`, que verifica automáticamente los invariantes y las reglas de cambio de esta constitución.

---

## Artículo I · Supremacía de la spec

1. La spec es la única fuente de verdad sobre el comportamiento del sistema.
2. Si código y spec discrepan, se presume que el código es incorrecto. Si se concluye que la spec está mal, se corrigen spec, tests y código **en el mismo cambio**.
3. **Código sin requisito es un defecto**: es funcionalidad no autorizada. Se especifica o se elimina.
4. **Requisito implementado sin test es un defecto**: es una promesa no verificada.
5. La spec describe el **estado actual** del sistema, no su historia ni sus planes. Las specs se organizan por capacidad, nunca por cambio, sprint o ticket. La historia vive en git; lo pendiente, en `mejoras.md`; el avance, en `tareas.md`.

## Artículo II · Sincronía bidireccional

Toda integración declara exactamente una **clase**. La clase determina qué ficheros puede tocar y qué obligaciones contrae:

| Clase | Puede tocar | Obligaciones |
|---|---|---|
| `behavior` | specs, tests, código anclado y los ficheros no anclados que el cambio necesite | Declara los IDs afectados. Por cada ID declarado cambian su texto normativo **y** al menos un test marcado con él. Todo módulo de código anclado modificado incluye en su `Spec:` algún ID declarado. Si implementa una mejora, la elimina de `mejoras.md`. |
| `refactor` | código anclado, los ficheros no anclados que el cambio necesite y, sólo para adaptarlos a cambios estructurales, tests anclados | No toca specs. No cambia lo que afirma ningún test. La suite pasa. Ningún requisito pierde tests. |
| `editorial` | specs y documentación | No altera el significado de ningún texto normativo. No toca código ni tests. Requiere aprobación explícita de la persona propietaria del producto. |
| `chore` | sólo ficheros no anclados | No toca specs, tests ni código anclado. |
| `constitution` | este documento y las adaptaciones que la enmienda exija | Ver Artículo XII. |

Además, cualquier clase de cambio puede modificar `tareas.md`. Una dependencia de ejecución añadida en un `behavior` o un `refactor` se justifica en `design.md` (Artículo IX.2).

De esta tabla se derivan las dos direcciones del anclaje:

- **II.1 · Código → spec.** Todo cambio de comportamiento observable es `behavior` y modifica la spec. Modificar código anclado sin tocar la spec sólo es legítimo como `refactor`, y la prueba de que el comportamiento no cambió es que la suite pasa **sin cambiar lo que afirman los tests**. Un refactor que no toca ningún test es la forma preferida: es la prueba más fuerte.
- **II.2 · Spec → código.** Modificar el texto normativo de un requisito `implemented` obliga a modificar, en la misma integración, sus tests y el código necesario para que pasen. La única excepción es `editorial`.
- **II.3 · Tests ↔ spec.** Los tests son la forma ejecutable de la spec. Cambiar lo que un test afirma es cambiar el comportamiento: es `behavior`.
- **II.4 · Atomicidad.** La unidad de anclaje es la **integración**: cada commit en `dev`. Los estados intermedios (p. ej. tests en rojo durante el paso *Rojo* del Artículo VI) sólo existen en la copia de trabajo y nunca se commitean. Todo commit en `dev` y en `main` cumple todas las reglas de este artículo y todos los invariantes del Artículo III.
- **II.5 · Declaración.** La clase y los IDs se declaran con *trailers* en el mensaje del commit de integración (Anexo B). Una declaración falsa (p. ej. un `refactor` que cambia comportamiento) es una deriva y se trata como tal.

### II.6 · Ramas

| Rama | Papel | Recibe |
|---|---|---|
| `main` | Producción: sólo versiones finales. | Versiones desde `dev` (`git merge --no-ff`). Cada versión se etiqueta `vX.Y.Z` y publica su ejecutable. |
| `dev` | Desarrollo: todo el trabajo, incluidas las correcciones. | Commits de integración. |

1. No se crean otras ramas. Las correcciones de producción también se hacen en `dev` y llegan a `main` con una versión nueva.
2. Los commits se hacen **en local**, donde los hooks ejecutan la verificación completa (Artículo XI). Nunca se hacen commits ni merges desde la web de GitHub, porque allí no se ejecuta ninguna verificación.
3. Las versiones (`dev` → `main`) no declaran clase: cada integración que contienen ya la declaró. Se verifican los invariantes sobre el resultado.
4. Sólo la persona propietaria del producto integra en `dev` y en `main`.

## Artículo III · Trazabilidad

### III.1 · Identificadores

- Formato `<PREFIJO>-<NNN>`: prefijo de 3 a 5 mayúsculas, único por capacidad y declarado en la cabecera de su spec, seguido de un número de tres dígitos.
- Los IDs son **inmutables**: nunca se renumeran ni se reutilizan. Un requisito que deja de existir pasa a `retired` y su ID queda reservado para siempre.
- El prefijo `MEJ` está reservado para las entradas de `mejoras.md`. Las tareas de `tareas.md` usan IDs `T-NNN`, que no son requisitos.

### III.2 · Marcado en tests

Cada test lleva al menos un marcador `@pytest.mark.spec("CONV-001")`.

### III.3 · Marcado en código

Cada módulo del código anclado que define funciones o clases declara, en su docstring de módulo, los requisitos que implementa:

```python
"""Color conversions between HEX, RGB, HSL and HSV.

Spec: CONV-001, CONV-002, CONV-003
"""
```

Los módulos sin definiciones (p. ej. un `__init__.py` que sólo reexporta) están exentos.

**Riesgo asumido.** El marcado por módulo no permite al checker detectar, dentro de un módulo ya anclado, una función nueva que hace algo no especificado. Se compensa con:

1. Módulos pequeños y cohesionados, cuyo `Spec:` describa con fidelidad todo lo que hacen.
2. Los umbrales de cobertura del Artículo X, que obligan a probar todo el código con tests marcados.
3. El punto correspondiente de la lista de revisión (Anexo C).

### III.4 · Invariantes

Los invariantes marcados *Siempre* se exigen también sobre la copia de trabajo, al final de cada turno de un agente de IA. Los marcados *Al integrar* se exigen en todo commit.

| ID | Invariante | Se exige |
|---|---|---|
| INV-1 | Los IDs son únicos y bien formados, y ningún requisito `approved` o `implemented` contiene `[NEEDS CLARIFICATION]`. | Siempre |
| INV-2 | Todo test tiene al menos un marcador `spec`. | Siempre |
| INV-3 | Todo módulo del código anclado que define funciones o clases declara `Spec:` en su docstring. | Siempre |
| INV-4 | Toda referencia (marcador o `Spec:`) apunta a un requisito existente que no está `retired`; nunca a una mejora `MEJ` ni a una tarea `T`. | Siempre |
| INV-5 | Todo requisito `implemented` está referenciado por al menos un test y por al menos un módulo del código anclado. | Al integrar |
| INV-6 | No existen requisitos `draft` ni `approved`: todos están `implemented` o `retired`. | Al integrar |
| INV-7 | Todos los tests pasan. | Al integrar |

Juntos, INV-4 e INV-6 garantizan que en las ramas integradas todo el código y todos los tests apuntan a requisitos `implemented`.

## Artículo IV · Ciclo de vida

```text
 mejoras.md ──► draft ──► approved ──► implemented ──► retired
 (backlog)     └─ copia de trabajo ──┘ └── commit en dev ───┘
```

| Estado | Dónde vive | Significado | Anclaje |
|---|---|---|---|
| Mejora `MEJ-NNN` | `mejoras.md` | Idea o funcionalidad pendiente. No es normativa. | Prohibido referenciarla. |
| `draft` | spec, copia de trabajo | En redacción. Puede contener `[NEEDS CLARIFICATION]`. | Puede referenciarse sólo en la copia de trabajo. |
| `approved` | spec, copia de trabajo | Sin ambigüedades y aceptado por la persona propietaria del producto. | Puede referenciarse sólo en la copia de trabajo. |
| `implemented` | spec | Anclado: tiene tests y código. | Obligatorio (INV-5). |
| `retired` | spec | Retirado. Se conservan el ID y una línea con el motivo. | Prohibido referenciarlo. |

1. **Backlog.** Todo lo que todavía no está implementado vive en `mejoras.md`, nunca en una spec commiteada (INV-6). Cada mejora tiene un ID `MEJ-NNN` que no se reutiliza. Cualquiera, persona o agente de IA, puede añadir mejoras.
2. **De mejora a requisito.** Para implementar una mejora se redactan, en la copia de trabajo de `dev`, sus requisitos en `draft`, se clarifican, se aprueban, se implementan y, **en la misma integración**, se elimina la mejora de `mejoras.md`.
3. **Aprobación.** Sólo la persona propietaria del producto pasa un requisito a `approved`, de forma explícita (en una revisión o en una instrucción directa a un agente). Un agente de IA puede redactar requisitos, pero nunca los marca como `approved` por iniciativa propia.
4. El paso `approved → implemented` ocurre en la misma integración que añade sus tests y su código.
5. El paso `implemented → retired` ocurre en la misma integración que elimina sus tests y el código que sólo él justificaba.

## Artículo V · Formato de las specs

1. Estructura de directorios:

   ```text
   mejoras.md           # backlog, no normativo
   tareas.md            # plan de tareas y seguimiento, no normativo
   specs/
   └── <capacidad>/
       ├── spec.md      # normativo y anclado
       └── design.md    # opcional: decisiones técnicas, informativo
   ```

2. Cada `spec.md` es Markdown. Empieza con una cabecera YAML (`capability`, `prefix`, `owner`) y contiene, en este orden: **Propósito**, **Alcance** y **Fuera de alcance**, **Glosario** (si aplica), **Requisitos** y **Notas**.
3. Cada requisito sigue la plantilla del Anexo A: enunciado en sintaxis **EARS** y criterios de aceptación en forma **Dado / Cuando / Entonces** con valores concretos.
4. La spec dice *qué* y *por qué*. No nombra clases, módulos, librerías ni frameworks. Eso va en `design.md`.
5. **Prohibido adivinar.** Ante cualquier ambigüedad se escribe `[NEEDS CLARIFICATION: <pregunta>]` y se pregunta. Esta regla obliga especialmente a los agentes de IA.
6. Un requisito, una idea. Si un enunciado une con "y" dos comportamientos independientes, son dos requisitos.
7. `design.md` no es normativo, pero no puede contradecir ni a la spec ni a esta constitución. Se mantiene al día y se comprueba en revisión, no con el checker.
8. Las specs, `design.md`, `mejoras.md`, `tareas.md` y la documentación se escriben en **español**.
9. **`tareas.md`.** Contiene el plan del proyecto: tareas con un ID `T-NNN` que no se reutiliza, un responsable, un estado y un criterio *Hecho cuando* comprobable, más un registro con fecha. Cuando se asigna una tarea a un agente de IA, el agente actualiza el fichero al empezar y al terminar la tarea.

## Artículo VI · Flujo de trabajo

Todo cambio de comportamiento sigue este orden, sin saltarse pasos:

1. **Elegir**: tomar una mejora de `mejoras.md` (o detectar un defecto) y trabajar en `dev` sin commitear hasta el paso 9.
2. **Especificar**: redactar o modificar requisitos en `draft`.
3. **Clarificar**: resolver todos los `[NEEDS CLARIFICATION]` y obtener la aprobación (`approved`).
4. **Diseñar**: si el cambio afecta a la arquitectura o añade dependencias, actualizar `design.md`.
5. **Rojo**: escribir los tests a partir de los criterios de aceptación, marcados con sus IDs, y verlos fallar.
6. **Verde**: escribir el código mínimo que los hace pasar, en módulos cuyo `Spec:` incluya esos IDs.
7. **Refactorizar**: con los tests en verde y sin cambiar lo que afirman.
8. **Verificar**: los requisitos pasan a `implemented`, la mejora sale de `mejoras.md` y se ejecuta la verificación completa (Artículo XI).
9. **Integrar**: la persona propietaria del producto hace en `dev` un único commit `behavior` que reúne spec, tests y código.

Durante todo el flujo, `tareas.md` refleja la tarea en curso y las completadas (Artículo V.9).

## Artículo VII · Tests primero

1. Ningún código de producción se escribe antes que el test que lo exige.
2. Cada criterio de aceptación se corresponde con al menos un test.
3. Las propiedades universales del dominio (p. ej. ida y vuelta entre espacios de color, rangos válidos) se prueban con tests basados en propiedades (Hypothesis), además de con ejemplos concretos.
4. El núcleo de dominio se prueba sin dobles. Los adaptadores se prueban contra sus puertos con implementaciones falsas (*fakes*). La UI tiene, como mínimo, tests de humo con `pytest-qt`.

## Artículo VIII · Arquitectura

1. Capas:
   - `pxls.core`: dominio puro. Modelos de color, conversiones, análisis y formateo. Sin E/S, sin GUI, sin dependencias del sistema operativo. Determinista.
   - `pxls.adapters`: el mundo exterior. Captura de pantalla, portapapeles, persistencia, atajos globales. Implementan puertos (`typing.Protocol`) definidos en `core`.
   - `pxls.ui`: presentación con **PySide6** (Qt 6).
2. Regla de dependencias: `core` no importa nada de `adapters` ni de `ui`, ni PySide6; `adapters` no importa nada de `ui`. Se verifica automáticamente (`import-linter`).
3. Plataforma objetivo: **Windows 10 y 11 de 64 bits**. Todo lo que depende de la plataforma vive en `adapters`, detrás de un puerto, de modo que añadir otra plataforma sea una enmienda MINOR y no una reescritura.

## Artículo IX · Simplicidad

1. **YAGNI**: no se implementa nada que no exija un requisito `approved`.
2. Se prefiere la biblioteca estándar. Cada dependencia de ejecución se justifica en un `design.md`, junto con las alternativas descartadas.
3. Las dependencias se fijan con lockfile; ninguna queda sin acotar.
4. Ninguna abstracción sin al menos dos usos reales o un puerto exigido por el Artículo VIII.

## Artículo X · Calidad y distribución

| Puerta | Herramienta | Umbral |
|---|---|---|
| Entorno y dependencias | `uv` | Python 3.13 |
| Formato y lint | `ruff format`, `ruff check` | Cero avisos |
| Tipos | `mypy --strict` | Cero errores; `Any` prohibido en `core` |
| Tests | `pytest`, `pytest-qt`, Hypothesis | Todos pasan |
| Cobertura | `pytest-cov` (por ramas) | `core` ≥ 95 %, total ≥ 85 % |
| Arquitectura | `import-linter` | Contratos del Artículo VIII |
| Anclaje | `spec-anchor` | Artículos II y III |
| Empaquetado | PyInstaller | Se genera `pxls.exe` y supera una prueba de humo |

1. **Distribución.** `pxls` se distribuye como ejecutable de Windows desde la primera versión. Ninguna integración puede romper el empaquetado. Cada versión de `main` se etiqueta `vX.Y.Z` (versionado semántico) y va acompañada de su `.exe`.
2. **Idioma del código.** Identificadores, comentarios, docstrings y mensajes de commit se escriben en **inglés**.

## Artículo XI · Cumplimiento

1. **Checker `spec-anchor`.** Es la primera capacidad del proyecto y se construye con el mismo método que el resto (`specs/spec-anchor/spec.md`, prefijo `ANCH`). Comprueba los invariantes del Artículo III y las reglas del Artículo II sobre cada integración y sus trailers.
2. **Niveles de verificación.**

   | Nivel | Qué incluye | Cuándo |
   |---|---|---|
   | Rápida | `ruff format --check`, `ruff check` e invariantes *Siempre* | El final de cada turno de un agente de IA, sobre la copia de trabajo |
   | Completa | Rápida + el resto de puertas del Artículo X + invariantes *Al integrar* + reglas del Artículo II + trailers | Cada commit |

3. **Capas de cumplimiento.** No hay integración continua remota: las barreras son dos y ambas son obligatorias.
   - *En el PC (hooks de git).* Los hooks `pre-commit`, `pre-merge-commit` y `commit-msg` ejecutan la verificación completa en cada commit. Instalarlos es obligatorio en todo clon del repositorio, antes del primer commit.
   - *En Claude Code.* `CLAUDE.md` remite a esta constitución. Un hook ejecuta la verificación rápida al final de cada turno y no permite dar la tarea por terminada si falla. La configuración del repositorio impide al agente usar `--no-verify` y hacer commits.
4. Ninguna capacidad de producto se implementa antes de que `spec-anchor` y los hooks estén operativos. Hasta entonces, las reglas se aplican en revisión manual con la lista del Anexo C.
5. Como los hooks locales se pueden saltar técnicamente, la disciplina es parte de la norma: nadie, persona o agente, desactiva, omite (`--no-verify`) ni debilita una verificación sin una enmienda previa de esta constitución.
6. Añadir integración continua remota en el futuro es una enmienda MINOR.

## Artículo XII · Gobernanza

1. Esta constitución prevalece sobre todo lo demás. Ante un conflicto se corrige lo demás o se enmienda la constitución; nunca se ignora.
2. Toda enmienda es un cambio de clase `constitution` que explica el motivo, incrementa la versión y añade una entrada al historial. Si la enmienda lo exige, incluye en el mismo cambio la adaptación de specs, tests, código y herramientas.
3. Versionado semántico de la constitución:
   - **MAJOR**: se elimina o redefine un principio de forma incompatible.
   - **MINOR**: se añade un artículo o se amplía sustancialmente una regla.
   - **PATCH**: aclaraciones y correcciones de redacción.
4. Los agentes de IA están sujetos a las mismas reglas que las personas. Pueden redactar specs, requisitos, mejoras y propuestas de enmienda, pero sólo la persona propietaria del producto aprueba requisitos y ratifica enmiendas.

---

## Anexo A · Plantilla de requisito

```markdown
### CONV-001 · Conversión de HEX a RGB

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario introduzca un color HEX válido, el sistema deberá mostrar sus componentes RGB.
- **Criterios de aceptación:**
  1. Dado `#FF8800FF`, cuando se convierte a RGB, entonces el resultado es `rgb(255, 136, 0)` con alfa 1.
  2. Dado `#ff8800ff`, cuando se convierte a RGB, entonces el resultado es el mismo que en el criterio 1.
- **Notas:** (informativo)
```

Patrones EARS admitidos:

| Patrón | Plantilla |
|---|---|
| Ubicuo | El sistema deberá `<respuesta>`. |
| Por evento | Cuando `<disparador>`, el sistema deberá `<respuesta>`. |
| Por estado | Mientras `<estado>`, el sistema deberá `<respuesta>`. |
| Opcional | Donde `<característica presente>`, el sistema deberá `<respuesta>`. |
| No deseado | Si `<condición no deseada>`, entonces el sistema deberá `<respuesta>`. |

## Anexo B · Trailers de commit

Los trailers van en el mensaje del commit de integración:

```text
feat(conv): accept 6-digit HEX without alpha

Change-Type: behavior
Spec-Refs: CONV-001, CONV-004
```

- `Change-Type`: obligatorio. Uno de `behavior`, `refactor`, `editorial`, `chore`, `constitution`.
- `Spec-Refs`: obligatorio en `behavior` y `editorial`; prohibido en `refactor` y `chore`.

## Anexo C · Lista de revisión (Definition of Done)

- [ ] La clase de cambio declarada es la correcta y respeta su tabla de permisos.
- [ ] Ningún requisito `approved` o `implemented` contiene `[NEEDS CLARIFICATION]`.
- [ ] No queda ningún requisito `draft` ni `approved` en el resultado.
- [ ] Cada requisito tocado tiene enunciado EARS y criterios de aceptación con valores concretos.
- [ ] Cada criterio de aceptación tiene al menos un test marcado con su ID.
- [ ] Los tests se escribieron antes que el código y se vieron fallar.
- [ ] Todo lo que hace cada módulo modificado está cubierto por los requisitos de su `Spec:` (el checker no puede comprobarlo función a función).
- [ ] La mejora implementada se ha eliminado de `mejoras.md`.
- [ ] `tareas.md` está al día.
- [ ] `design.md` está al día si cambiaron la arquitectura o las dependencias.
- [ ] La verificación completa pasa, incluido el empaquetado.

## Historial de enmiendas

| Versión | Fecha | Clase | Cambio |
|---|---|---|---|
| 0.1.0 | 2026-10-24 | constitution | Borrador inicial. |
| 0.2.0 | 2026-10-24 | constitution | Resueltas Q1, Q2, Q5–Q9, Q12–Q14: alcance del producto, PySide6, sólo Windows, ejecutable desde el principio, specs en Markdown, modelo de ramas `dev`/`main`, backlog en `mejoras.md`, idiomas, Python 3.13 y aprobación exclusiva de la persona propietaria del producto. |
| 0.3.0 | 2026-10-24 | constitution | Resueltas Q10 y Q11: anclaje en código por módulo (con su riesgo asumido y compensaciones); cumplimiento con hooks de git y Claude Code, sin integración continua remota, lo que obliga a integrar en local; dos niveles de verificación (rápida y completa); invariantes reorganizados en *Siempre* y *Al integrar*. |
| 1.0.0 | 2026-10-24 | constitution | Ratificación por la persona propietaria del producto. Entra en vigor. |
| 1.1.0 | 2026-10-24 | constitution | Se reconoce `tareas.md` como plan y seguimiento del proyecto (V.9), modificable en cualquier clase de cambio. `behavior` y `refactor` pueden tocar los ficheros no anclados que el cambio necesite (configuración, dependencias, hooks, `CLAUDE.md`…), y se define *fichero no anclado*. INV-4 prohíbe referenciar tareas. Ratificada por la persona propietaria del producto. |
| 2.0.0 | 2026-10-24 | constitution | Se eliminan las ramas de trabajo (`feature/*`, `fix/*`, `hotfix/*`): todo el desarrollo se hace en `dev`. La unidad de anclaje pasa a ser cada commit en `dev`; los estados intermedios sólo existen en la copia de trabajo. La verificación rápida se aplica a la copia de trabajo y la completa a todo commit. Ordenada por la persona propietaria del producto. |
