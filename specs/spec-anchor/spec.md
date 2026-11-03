---
capability: spec-anchor
prefix: ANCH
owner: Bartosz Kucmierz
---

# spec-anchor

## Propósito

`spec-anchor` hace cumplir automáticamente el anclaje entre specs, tests y código que exige la constitución (Artículos II, III y XI). Sin esta herramienta las reglas dependen de la memoria y la disciplina de quien trabaja. Con ella, un commit que rompe el anclaje no llega a crearse y un agente de IA no puede terminar un turno dejando el repositorio en un estado incoherente.

En esta spec, **el sistema** es `spec-anchor` junto con los hooks de git y la configuración de Claude Code que instala.

## Alcance

- Leer las specs, los tests y los módulos anclados del repositorio.
- Comprobar los invariantes INV-1 a INV-7.
- Comprobar las reglas de clase de cambio y los trailers de cada commit.
- Ofrecer los dos niveles de verificación: rápida y completa.
- Instalar y ejecutar los hooks de git.
- Configurar Claude Code para que un agente de IA no pueda saltarse las verificaciones.

## Fuera de alcance

- Integración continua remota (constitución XI.6).
- Comprobar que un `refactor` no cambia *lo que afirma* un test, o que un `editorial` no cambia el significado de un texto: requiere criterio humano y se revisa con el Anexo C de la constitución.
- Comprobar `design.md`.
- Anclaje función a función: el anclaje en código es por módulo (constitución III.3).
- Publicar versiones o ejecutables.

## Glosario

- **Copia de trabajo**: el estado de los ficheros en disco, incluidos los cambios sin commitear.
- **Commit en curso**: el commit que se está intentando crear, es decir, el contenido preparado (*staged*) y su mensaje.
- **Fichero de test**: fichero `test_*.py` bajo `tests/`.
- **Función de test**: función cuyo nombre empieza por `test` dentro de un fichero de test, incluidas las de clases cuyo nombre empieza por `Test`.
- **Módulo anclado**: fichero `.py` bajo `src/` o `tools/`.
- **Referencia**: aparición de un ID en un marcador `spec` de un test o en la línea `Spec:` del docstring de un módulo.
- **Error**: incumplimiento detectado. Una verificación con al menos un error falla.

## Requisitos

### Lectura de specs

#### ANCH-001 · Descubrimiento de specs

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá tratar como spec todo fichero `specs/<capacidad>/spec.md`, y sólo esos.
- **Criterios de aceptación:**
  1. Dado un repositorio con `specs/color-model/spec.md`, `specs/color-model/design.md` y `docs/spec.md`, cuando se analiza, entonces la única spec es `specs/color-model/spec.md`.

#### ANCH-002 · Cabecera obligatoria

- **Estado:** implemented
- **Enunciado (EARS):** Si una spec no empieza con una cabecera delimitada por dos líneas `---` que contenga, en pares `clave: valor` de una línea, los campos `capability`, `prefix` y `owner`, entonces el sistema deberá informar de un error con el fichero y el campo que falta.
- **Criterios de aceptación:**
  1. Dada una spec con cabecera `capability: color-model`, `prefix: COLOR` y `owner: Bartosz Kucmierz`, cuando se verifica, entonces no hay error de cabecera.
  2. Dada una spec cuya cabecera no tiene `owner`, cuando se verifica, entonces hay un error que nombra el fichero y el campo `owner`.
  3. Dada una spec sin cabecera, cuando se verifica, entonces hay un error que nombra el fichero.

#### ANCH-003 · Capacidad coherente con la carpeta

- **Estado:** implemented
- **Enunciado (EARS):** Si el campo `capability` de una spec no coincide con el nombre de su carpeta, entonces el sistema deberá informar de un error que muestre ambos valores.
- **Criterios de aceptación:**
  1. Dada `specs/history/spec.md` con `capability: historial`, cuando se verifica, entonces hay un error que muestra `history` e `historial`.

#### ANCH-004 · Prefijo válido y único

- **Estado:** implemented
- **Enunciado (EARS):** Si el prefijo de una spec no está formado por 3 a 5 letras mayúsculas, es `MEJ` o lo usa otra spec, entonces el sistema deberá informar de un error.
- **Criterios de aceptación:**
  1. Dado `prefix: Co`, cuando se verifica, entonces hay un error de formato.
  2. Dado `prefix: MEJ`, cuando se verifica, entonces hay un error de prefijo reservado.
  3. Dadas dos specs con `prefix: COLOR`, cuando se verifica, entonces hay un error que nombra las dos specs.

#### ANCH-005 · Reconocimiento de requisitos

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá reconocer como requisito todo encabezado de nivel 3 o 4 situado dentro de la sección `## Requisitos` cuyo texto empiece por un ID seguido de ` · `.
- **Criterios de aceptación:**
  1. Dado `#### COLOR-001 · Conversión de HEX a RGB` bajo `## Requisitos`, cuando se analiza, entonces existe el requisito `COLOR-001`.
  2. Dado `### Conversiones` bajo `## Requisitos`, cuando se analiza, entonces no es un requisito.
  3. Dado `### COLOR-009 · Ejemplo` bajo `## Notas`, cuando se analiza, entonces no es un requisito.

#### ANCH-006 · IDs bien formados (INV-1)

- **Estado:** implemented
- **Enunciado (EARS):** Si el ID de un requisito no está formado por el prefijo de su spec, un guion y tres dígitos, entonces el sistema deberá informar de un error.
- **Criterios de aceptación:**
  1. Dado el requisito `COLOR-1` en la spec de prefijo `COLOR`, cuando se verifica, entonces hay un error de formato.
  2. Dado el requisito `PAL-001` en la spec de prefijo `COLOR`, cuando se verifica, entonces hay un error de prefijo.

#### ANCH-007 · IDs únicos (INV-1)

- **Estado:** implemented
- **Enunciado (EARS):** Si dos requisitos tienen el mismo ID, entonces el sistema deberá informar de un error con las dos ubicaciones.
- **Criterios de aceptación:**
  1. Dados dos encabezados `COLOR-001` en la misma spec, cuando se verifica, entonces hay un error que muestra las dos líneas.

#### ANCH-008 · Estado obligatorio

- **Estado:** implemented
- **Enunciado (EARS):** Si un requisito no tiene una línea `**Estado:**` o su valor no es `draft`, `approved`, `implemented` ni `retired`, entonces el sistema deberá informar de un error.
- **Criterios de aceptación:**
  1. Dado un requisito sin línea de estado, cuando se verifica, entonces hay un error con su ID.
  2. Dado `**Estado:** hecho`, cuando se verifica, entonces hay un error con su ID y el valor `hecho`.

#### ANCH-009 · Sin dudas en requisitos aprobados o implementados (INV-1)

- **Estado:** implemented
- **Enunciado (EARS):** Si un requisito `approved` o `implemented` contiene una duda abierta (la marca `NEEDS CLARIFICATION` precedida de un corchete de apertura), entonces el sistema deberá informar de un error con su ID.
- **Criterios de aceptación:**
  1. Dado un requisito `draft` con una duda abierta, cuando se verifica, entonces no hay error.
  2. Dado un requisito `approved` con una duda abierta, cuando se verifica, entonces hay un error con su ID.

#### ANCH-010 · Requisitos retirados

- **Estado:** implemented
- **Enunciado (EARS):** Si un requisito `retired` no tiene una línea `**Motivo:**`, entonces el sistema deberá informar de un error con su ID.
- **Criterios de aceptación:**
  1. Dado un requisito `retired` con `**Motivo:** sustituido por COLOR-012`, cuando se verifica, entonces no hay error.
  2. Dado un requisito `retired` sin motivo, cuando se verifica, entonces hay un error con su ID.

### Lectura de tests y código

#### ANCH-011 · Marcadores de test

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá obtener, para cada función de test, los IDs de todos los marcadores `spec` puestos sobre la propia función o sobre su clase `Test*`; los marcadores de módulo (`pytestmark`) no cuentan.
- **Criterios de aceptación:**
  1. Dado `@pytest.mark.spec("COLOR-001", "COLOR-002")` sobre `test_hex`, cuando se analiza, entonces `test_hex` referencia `COLOR-001` y `COLOR-002`.
  2. Dados dos marcadores `spec("COLOR-001")` y `spec("COLOR-003")` sobre el mismo test, cuando se analiza, entonces el test referencia `COLOR-001` y `COLOR-003`.
  3. Dada una clase `TestHex` con `@pytest.mark.spec("COLOR-001")` y dos métodos de test sin marcador, cuando se analiza, entonces los dos tests referencian `COLOR-001`.
  4. Dado un módulo con `pytestmark = pytest.mark.spec("COLOR-001")` y un test sin marcador, cuando se analiza, entonces ese test no referencia ningún ID.

#### ANCH-012 · Tests sin marcador (INV-2)

- **Estado:** implemented
- **Enunciado (EARS):** Si una función de test no tiene ningún marcador `spec`, entonces el sistema deberá informar de un error con su fichero, línea y nombre.
- **Criterios de aceptación:**
  1. Dado `tests/core/test_hex.py` con `def test_parse()` sin marcadores, cuando se verifica, entonces hay un error que muestra `tests/core/test_hex.py`, la línea y `test_parse`.

#### ANCH-013 · Declaración `Spec:` de los módulos

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá obtener, para cada módulo anclado, los IDs separados por comas de la línea `Spec:` de su docstring de módulo y de las líneas sangradas que la siguen inmediatamente.
- **Criterios de aceptación:**
  1. Dado un módulo cuyo docstring contiene `Spec: COLOR-001, COLOR-003`, cuando se analiza, entonces el módulo referencia `COLOR-001` y `COLOR-003`.
  2. Dado un docstring con `Spec: COLOR-001,` seguido de una línea sangrada `COLOR-002`, cuando se analiza, entonces el módulo referencia `COLOR-001` y `COLOR-002`.
  3. Dado un docstring con `Spec: COLOR-001` seguido de una línea en blanco y una línea sangrada `COLOR-002`, cuando se analiza, entonces el módulo sólo referencia `COLOR-001`.
- **Notas:** la continuación permite listas largas sin superar el límite de 100 caracteres por línea del lint.

#### ANCH-014 · Módulos sin `Spec:` (INV-3)

- **Estado:** implemented
- **Enunciado (EARS):** Si un módulo anclado define funciones o clases en su nivel superior y su docstring no contiene una línea `Spec:` con al menos un ID, entonces el sistema deberá informar de un error con el fichero.
- **Criterios de aceptación:**
  1. Dado un módulo con `def to_hex()` y sin docstring, cuando se verifica, entonces hay un error con el fichero.
  2. Dado un `__init__.py` que sólo importa y reexporta, cuando se verifica, entonces no hay error.
  3. Dado un módulo con una clase y la línea `Spec:` vacía, cuando se verifica, entonces hay un error con el fichero.

#### ANCH-015 · Referencias válidas (INV-4)

- **Estado:** implemented
- **Enunciado (EARS):** Si una referencia no corresponde a ningún requisito, corresponde a un requisito `retired`, o es una mejora `MEJ-NNN` o una tarea `T-NNN`, entonces el sistema deberá informar de un error con el lugar de la referencia.
- **Criterios de aceptación:**
  1. Dado `spec("COLOR-099")` sin requisito `COLOR-099`, cuando se verifica, entonces hay un error con el fichero, la línea y `COLOR-099`.
  2. Dado `Spec: MEJ-003` en un módulo, cuando se verifica, entonces hay un error.
  3. Dado `spec("T-012")` en un test, cuando se verifica, entonces hay un error.
  4. Dada una referencia a un requisito `retired`, cuando se verifica, entonces hay un error.

### Invariantes al integrar

#### ANCH-016 · Requisitos implementados anclados (INV-5)

- **Estado:** implemented
- **Enunciado (EARS):** Si un requisito `implemented` no está referenciado por ningún test o por ningún módulo anclado, entonces el sistema deberá informar de un error que diga cuál de los dos falta.
- **Criterios de aceptación:**
  1. Dado `COLOR-001` `implemented`, referenciado por un módulo y por ningún test, cuando se verifica, entonces hay un error «sin tests» para `COLOR-001`.
  2. Dado `COLOR-001` `implemented`, referenciado por un test y por ningún módulo, cuando se verifica, entonces hay un error «sin código» para `COLOR-001`.

#### ANCH-017 · Sin requisitos pendientes (INV-6)

- **Estado:** implemented
- **Enunciado (EARS):** Si el commit en curso contiene un requisito `draft` o `approved`, entonces el sistema deberá informar de un error con su ID.
- **Criterios de aceptación:**
  1. Dado un commit en curso con `COLOR-004` en `approved`, cuando se verifica, entonces hay un error con `COLOR-004`.

#### ANCH-018 · Tests en verde (INV-7)

- **Estado:** implemented
- **Enunciado (EARS):** Si algún test falla, entonces el sistema deberá informar de un error con los tests que fallan.
- **Criterios de aceptación:**
  1. Dado un test que falla, cuando se ejecuta la verificación completa, entonces hay un error con el nombre de ese test.

### Clases de cambio y trailers

#### ANCH-019 · Trailer `Change-Type`

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se intente un commit en `dev`, el sistema deberá rechazarlo si su mensaje no tiene exactamente un trailer `Change-Type` con uno de los valores `behavior`, `refactor`, `editorial`, `chore` o `constitution`.
- **Criterios de aceptación:**
  1. Dado un mensaje sin `Change-Type`, cuando se intenta el commit, entonces se rechaza.
  2. Dado `Change-Type: feature`, cuando se intenta el commit, entonces se rechaza.
  3. Dados dos trailers `Change-Type`, cuando se intenta el commit, entonces se rechaza.

#### ANCH-020 · Trailer `Spec-Refs`

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se intente un commit en `dev`, el sistema deberá rechazarlo si falta `Spec-Refs` en un `behavior` o un `editorial`, si aparece en un `refactor` o un `chore`, o si contiene un valor que no es una lista de IDs separados por comas. En un commit `constitution`, `Spec-Refs` es opcional.
- **Criterios de aceptación:**
  1. Dado `Change-Type: behavior` sin `Spec-Refs`, cuando se intenta el commit, entonces se rechaza.
  2. Dado `Change-Type: chore` con `Spec-Refs: COLOR-001`, cuando se intenta el commit, entonces se rechaza.
  3. Dado `Spec-Refs: COLOR-001; COLOR-002`, cuando se intenta el commit, entonces se rechaza.
  4. Dado `Change-Type: constitution` sin `Spec-Refs`, cuando se intenta el commit, entonces no se rechaza por este motivo.

#### ANCH-021 · `behavior`: cada ID declarado cambia en spec y tests

- **Estado:** implemented
- **Enunciado (EARS):** Si en un commit `behavior` algún ID declarado no cambia su texto normativo, o no se añade, modifica o elimina ningún test marcado con él, entonces el sistema deberá rechazar el commit indicando el ID.
- **Criterios de aceptación:**
  1. Dado un `behavior` que declara `COLOR-004`, cambia sus criterios de aceptación y modifica un test marcado con `COLOR-004`, cuando se intenta el commit, entonces se acepta.
  2. Dado un `behavior` que declara `COLOR-004` y sólo cambia sus notas, cuando se intenta el commit, entonces se rechaza.
  3. Dado un `behavior` que declara `COLOR-004`, cambia sus criterios y no toca ningún test, cuando se intenta el commit, entonces se rechaza.
  4. Dado un `behavior` que añade `COLOR-010` y un test nuevo marcado con él, cuando se intenta el commit, entonces se acepta.

#### ANCH-022 · `behavior`: el código cambiado pertenece a los IDs declarados

- **Estado:** implemented
- **Enunciado (EARS):** Si en un commit `behavior` un módulo anclado modificado que define funciones o clases no incluye en su `Spec:` ninguno de los IDs declarados, entonces el sistema deberá rechazar el commit indicando el módulo.
- **Criterios de aceptación:**
  1. Dado un `behavior` con `Spec-Refs: COLOR-004` que modifica un módulo con `Spec: COLOR-001`, cuando se intenta el commit, entonces se rechaza.
  2. Dado un `behavior` con `Spec-Refs: COLOR-004` que añade un `__init__.py` que sólo reexporta, cuando se intenta el commit, entonces no se rechaza por este motivo.
- **Notas:** los módulos sin definiciones están exentos de declarar `Spec:` (constitución III.3) y, por coherencia, también de esta regla.

#### ANCH-023 · `refactor`

- **Estado:** implemented
- **Enunciado (EARS):** Si un commit `refactor` modifica una spec, o tras él algún requisito queda referenciado por menos tests que antes, entonces el sistema deberá rechazar el commit.
- **Criterios de aceptación:**
  1. Dado un `refactor` que modifica `specs/color-model/spec.md`, cuando se intenta el commit, entonces se rechaza.
  2. Dado un `refactor` que elimina uno de los dos tests marcados con `COLOR-001`, cuando se intenta el commit, entonces se rechaza.
  3. Dado un `refactor` que sólo modifica módulos anclados y la suite pasa, cuando se intenta el commit, entonces se acepta.

#### ANCH-024 · `editorial`

- **Estado:** implemented
- **Enunciado (EARS):** Si un commit `editorial` modifica un fichero que no es `.md`, modifica `CONSTITUTION.md` o `mejoras.md`, cambia el estado de un requisito, o añade o elimina requisitos, entonces el sistema deberá rechazar el commit.
- **Criterios de aceptación:**
  1. Dado un `editorial` que corrige una errata en el enunciado de `COLOR-001`, cuando se intenta el commit, entonces se acepta.
  2. Dado un `editorial` que corrige `README.md` y un `design.md`, cuando se intenta el commit, entonces se acepta.
  3. Dado un `editorial` que pasa `COLOR-001` a `retired`, cuando se intenta el commit, entonces se rechaza.
  4. Dado un `editorial` que modifica `mejoras.md` o `pyproject.toml`, cuando se intenta el commit, entonces se rechaza.

#### ANCH-025 · `chore`

- **Estado:** implemented
- **Enunciado (EARS):** Si un commit `chore` modifica una spec, un fichero de test o un módulo anclado, entonces el sistema deberá rechazar el commit.
- **Criterios de aceptación:**
  1. Dado un `chore` que sólo modifica `pyproject.toml`, cuando se intenta el commit, entonces se acepta.
  2. Dado un `chore` que modifica un módulo de `src/`, cuando se intenta el commit, entonces se rechaza.

#### ANCH-026 · `constitution`

- **Estado:** implemented
- **Enunciado (EARS):** Si un commit `constitution` no modifica `CONSTITUTION.md`, no incrementa su versión o no añade al historial de enmiendas una fila con la versión nueva, entonces el sistema deberá rechazar el commit.
- **Criterios de aceptación:**
  1. Dado un `constitution` que pasa la versión de 1.1.0 a 1.2.0 y añade la fila `1.2.0` al historial, cuando se intenta el commit, entonces se acepta.
  2. Dado un `constitution` que modifica `CONSTITUTION.md` sin cambiar la versión, cuando se intenta el commit, entonces se rechaza.

#### ANCH-027 · `tareas.md` en cualquier clase

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá aceptar cambios en `tareas.md` en cualquier clase de cambio.
- **Criterios de aceptación:**
  1. Dado un `chore` que modifica `pyproject.toml` y `tareas.md`, cuando se intenta el commit, entonces se acepta.
  2. Dado un `editorial` que modifica una spec y `tareas.md`, cuando se intenta el commit, entonces se acepta.

#### ANCH-028 · Sólo `dev` y `main`

- **Estado:** implemented
- **Enunciado (EARS):** Si se intenta un commit en una rama distinta de `dev` y `main`, entonces el sistema deberá rechazarlo.
- **Criterios de aceptación:**
  1. Dada la rama `feature/x`, cuando se intenta un commit, entonces se rechaza con un mensaje que remite a la constitución II.6.

#### ANCH-029 · Commits en `main`

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se intente un commit en `main`, el sistema deberá aceptarlo sólo si es un merge de `dev` cuyo resultado pasa la verificación completa, sin exigir trailers ni aplicar las reglas de clase.
- **Criterios de aceptación:**
  1. Dado `git merge --no-ff dev` en `main` con un resultado que pasa la verificación completa, cuando se intenta el commit, entonces se acepta.
  2. Dado un commit normal (no merge) en `main`, cuando se intenta, entonces se rechaza.

### Niveles de verificación

#### ANCH-030 · Verificación rápida

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se pida la verificación rápida, el sistema deberá comprobar sobre la copia de trabajo el formato, el lint y los invariantes INV-1 a INV-4, sin ejecutar los tests.
- **Criterios de aceptación:**
  1. Dada una copia de trabajo con un test sin marcador, cuando se ejecuta la verificación rápida, entonces falla con un error INV-2.
  2. Dada una copia de trabajo con un test que falla y todo lo demás correcto, cuando se ejecuta la verificación rápida, entonces pasa.

#### ANCH-031 · Verificación completa

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se intente un commit, el sistema deberá ejecutar la verificación completa: la rápida, los tipos, los tests, la cobertura, los contratos de arquitectura, los invariantes INV-5 a INV-7 y, en `dev`, los trailers y las reglas de clase de cambio.
- **Criterios de aceptación:**
  1. Dado un commit en curso con un error de tipos, cuando se intenta el commit, entonces se rechaza.
  2. Dado un commit en curso en el que `core` importa `adapters`, cuando se intenta el commit, entonces se rechaza.

#### ANCH-032 · Umbrales de cobertura

- **Estado:** implemented
- **Enunciado (EARS):** Si la cobertura por ramas total es menor del 85 % o la de `src/pxls/core` es menor del 95 %, entonces el sistema deberá informar de un error con el valor obtenido.
- **Criterios de aceptación:**
  1. Dada una cobertura total del 84,9 %, cuando se verifica, entonces hay un error que muestra 84,9 %.
  2. Dada una cobertura total del 90 % y del 94 % en `core`, cuando se verifica, entonces hay un error que muestra 94 % en `core`.

#### ANCH-033 · Empaquetado

- **Estado:** implemented
- **Enunciado (EARS):** Donde el proyecto tenga el empaquetado configurado, la verificación completa deberá generar el ejecutable y ejecutar su prueba de humo, y fallar si alguna de las dos cosas falla.
- **Criterios de aceptación:**
  1. Dado un proyecto sin empaquetado configurado, cuando se ejecuta la verificación completa, entonces no se intenta empaquetar.
  2. Dado un ejecutable que no supera la prueba de humo, cuando se ejecuta la verificación completa, entonces falla.

#### ANCH-034 · El commit es todo lo que hay en disco

- **Estado:** implemented
- **Enunciado (EARS):** Si al intentar un commit hay cambios sin preparar o ficheros sin seguimiento que no están ignorados, entonces el sistema deberá rechazar el commit y listarlos.
- **Criterios de aceptación:**
  1. Dado un fichero modificado y no preparado, cuando se intenta el commit, entonces se rechaza y se lista el fichero.
  2. Dado un fichero nuevo que está ignorado por `.gitignore`, cuando se intenta el commit, entonces no se tiene en cuenta.
- **Notas:** las verificaciones se ejecutan sobre el disco; si el disco no coincidiera con el commit, su resultado no valdría para el commit.

#### ANCH-035 · Informe de errores

- **Estado:** implemented
- **Enunciado (EARS):** Cuando una verificación termine, el sistema deberá mostrar en español cada error con la regla que incumple (p. ej. `INV-2` o `ANCH-021`), el fichero y la línea cuando apliquen, y un resumen con el número de errores.
- **Criterios de aceptación:**
  1. Dada una verificación con dos errores, cuando termina, entonces muestra dos líneas de error y un resumen que dice que hay 2 errores.

#### ANCH-036 · Código de salida

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá terminar cada verificación con el código 0 si no hay errores y con el código 1 si hay alguno.
- **Criterios de aceptación:**
  1. Dada una verificación sin errores, cuando termina, entonces el código de salida es 0.
  2. Dada una verificación con un error, cuando termina, entonces el código de salida es 1.

#### ANCH-037 · Duración de la verificación rápida

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá completar la verificación rápida del repositorio del proyecto en menos de 10 segundos.
- **Criterios de aceptación:**
  1. Dado el repositorio del proyecto, cuando se ejecuta la verificación rápida, entonces termina en menos de 10 segundos.
- **Notas:** la verificación completa no tiene límite de tiempo.

### Hooks de git

#### ANCH-038 · Instalación de los hooks

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se ejecute el comando de instalación, el sistema deberá instalar en el clon los hooks `pre-commit`, `pre-merge-commit` y `commit-msg`, de forma que ejecutarlo de nuevo deje el mismo resultado.
- **Criterios de aceptación:**
  1. Dado un clon sin hooks, cuando se ejecuta la instalación, entonces existen los tres hooks.
  2. Dado un clon con los hooks ya instalados, cuando se ejecuta de nuevo la instalación, entonces termina sin error y los hooks no cambian.

#### ANCH-039 · Hooks ajenos

- **Estado:** implemented
- **Enunciado (EARS):** Si ya existe un hook ajeno al sistema con uno de esos nombres, entonces el sistema deberá no sobrescribirlo e informar de un error que lo nombre.
- **Criterios de aceptación:**
  1. Dado un `pre-commit` escrito a mano, cuando se ejecuta la instalación, entonces ese hook no cambia y hay un error que lo nombra.
- **Notas:** para instalar los hooks del sistema, el hook ajeno se quita a mano.

#### ANCH-040 · Commit bloqueado

- **Estado:** implemented
- **Enunciado (EARS):** Si la verificación completa falla al intentar un commit, entonces el sistema deberá impedir que el commit se cree y mostrar el informe de errores.
- **Criterios de aceptación:**
  1. Dado un commit en curso con un test sin marcador, cuando se intenta el commit, entonces no se crea y se muestra el error INV-2.

#### ANCH-041 · Aviso de hooks no instalados

- **Estado:** implemented
- **Enunciado (EARS):** Mientras los hooks no estén instalados en el clon, la verificación rápida deberá fallar con un error que indique cómo instalarlos.
- **Criterios de aceptación:**
  1. Dado un clon sin hooks, cuando se ejecuta la verificación rápida, entonces falla y el error muestra el comando de instalación.

### Claude Code

#### ANCH-042 · Instrucciones para agentes

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá incluir en la raíz del repositorio un `CLAUDE.md` que obligue a leer `CONSTITUTION.md` antes de cualquier cambio y a mantener `tareas.md`.
- **Criterios de aceptación:**
  1. Dado el repositorio, cuando se abre `CLAUDE.md`, entonces enlaza `CONSTITUTION.md` y `tareas.md` y describe ambas obligaciones.

#### ANCH-043 · Verificación al final de cada turno

- **Estado:** implemented
- **Enunciado (EARS):** Cuando un agente de IA termine un turno en el repositorio, el sistema deberá ejecutar la verificación rápida y, si falla, impedir que el turno termine y devolver el informe al agente.
- **Criterios de aceptación:**
  1. Dado un turno que deja un módulo con funciones y sin `Spec:`, cuando el agente intenta terminar, entonces no puede y recibe el error INV-3.
  2. Dado un turno que deja la copia de trabajo correcta, cuando el agente intenta terminar, entonces termina.

#### ANCH-044 · Sin `--no-verify`

- **Estado:** implemented
- **Enunciado (EARS):** Si un agente de IA intenta ejecutar un comando git con `--no-verify`, o `git commit` con `-n`, entonces el sistema deberá bloquear el comando y explicar el motivo.
- **Criterios de aceptación:**
  1. Dado `git commit --no-verify -m x` pedido por el agente, cuando se va a ejecutar, entonces se bloquea.
  2. Dado `git push --no-verify` pedido por el agente, cuando se va a ejecutar, entonces se bloquea.

#### ANCH-045 · El agente no hace commits

- **Estado:** implemented
- **Enunciado (EARS):** Si un agente de IA intenta ejecutar un comando git que crea commits (`commit`, `merge`, `cherry-pick`, `revert`, `rebase` o `am`), entonces el sistema deberá bloquear el comando y explicar el motivo.
- **Criterios de aceptación:**
  1. Dado `git commit -m x` pedido por el agente, cuando se va a ejecutar, entonces se bloquea.
  2. Dado `git status` pedido por el agente, cuando se va a ejecutar, entonces se permite.

#### ANCH-046 · Protección de la configuración

- **Estado:** implemented
- **Enunciado (EARS):** Si un agente de IA intenta modificar la configuración de Claude Code del repositorio, los hooks de git del clon o el ajuste `core.hooksPath`, entonces el sistema deberá bloquearlo.
- **Criterios de aceptación:**
  1. Dado un agente que intenta editar `.claude/settings.json`, cuando se va a aplicar el cambio, entonces se bloquea.
  2. Dado `git config core.hooksPath /tmp` pedido por el agente, cuando se va a ejecutar, entonces se bloquea.
- **Notas:** una vez instalada la configuración, sólo la persona propietaria del producto la cambia.

#### ANCH-047 · Salida tras bloqueos repetidos

- **Estado:** implemented
- **Enunciado (EARS):** Si la verificación del final de turno ha impedido terminar al agente dos veces seguidas, entonces el sistema deberá dejarle terminar y mostrar a la persona que la verificación sigue fallando.
- **Criterios de aceptación:**
  1. Dado un agente al que la verificación ha bloqueado dos veces seguidas, cuando intenta terminar por tercera vez con la verificación aún fallando, entonces termina y la persona ve el informe de errores.
  2. Dado un agente bloqueado una vez que arregla el fallo, cuando intenta terminar, entonces termina sin aviso.
- **Notas:** evita que un agente que no sabe arreglar un fallo quede en un bucle infinito.

## Notas

### Trazabilidad con la constitución

| Regla de la constitución | Requisitos |
|---|---|
| Formato de specs e IDs (III.1, IV, V) | ANCH-001 a ANCH-005, ANCH-008, ANCH-010 |
| INV-1 | ANCH-006, ANCH-007, ANCH-009 |
| INV-2 | ANCH-011, ANCH-012 |
| INV-3 | ANCH-013, ANCH-014 |
| INV-4 | ANCH-015 |
| INV-5 | ANCH-016 |
| INV-6 | ANCH-017 |
| INV-7 | ANCH-018 |
| Trailers (II.5, Anexo B) | ANCH-019, ANCH-020 |
| Clase `behavior` | ANCH-021, ANCH-022 |
| Clase `refactor` | ANCH-023 |
| Clase `editorial` | ANCH-024 |
| Clase `chore` | ANCH-025 |
| Clase `constitution` | ANCH-026 |
| `tareas.md` en cualquier clase (II) | ANCH-027 |
| Ramas (II.6) | ANCH-028, ANCH-029 |
| Verificación rápida (XI.2) | ANCH-030, ANCH-037 |
| Verificación completa (XI.2, X) | ANCH-031 a ANCH-034 |
| Informe y salida | ANCH-035, ANCH-036 |
| Capa local: hooks de git (XI.3) | ANCH-038 a ANCH-041 |
| Capa Claude Code (XI.3, XII.4) | ANCH-042 a ANCH-047 |

### Otras notas

- **Arranque.** El commit que introduce `spec-anchor` (T-023) es el primero que verifican sus propios hooks: hay que instalarlos antes de hacerlo.
- **Empaquetado.** ANCH-033 no tiene efecto hasta que MEJ-002 configure el empaquetado (T-028).
- **Límite asumido.** Una persona puede saltarse los hooks con `--no-verify`. La constitución lo prohíbe (XI.5), pero sólo ANCH-044 lo impide, y únicamente para los agentes de IA.
- **Aprobación de `editorial`.** Como sólo la persona propietaria del producto hace commits (ANCH-045), el propio commit `editorial` es su aprobación explícita.
