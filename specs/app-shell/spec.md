---
capability: app-shell
prefix: APP
owner: Bartosz Kucmierz
---

# Esqueleto de la aplicación

## Propósito

Que `pxls` exista como aplicación de escritorio desde la primera versión: arranca, muestra su ventana principal, se cierra limpiamente y se distribuye como ejecutable de Windows. Es la base sobre la que se montan el cuentagotas, el selector y el resto de capacidades. Resolver el empaquetado ahora, sin funcionalidad, evita descubrir sus problemas cuando la aplicación ya sea grande.

## Alcance

- Arranque y cierre de la aplicación.
- Ventana principal: título, tamaño e icono.
- Versión visible para quien usa la aplicación.
- Idioma de la interfaz.
- Ejecutable de Windows y su prueba de humo.

## Fuera de alcance

- Cualquier funcionalidad de color (MEJ-003 en adelante).
- Instalador, firma de código y actualizaciones automáticas.
- Recordar la posición y el tamaño de la ventana entre sesiones.
- Varias instancias abiertas a la vez, varios monitores y escalado de pantalla: se especifican con el cuentagotas (MEJ-004).

## Glosario

- **Ventana principal**: la ventana que se abre al iniciar la aplicación y cuyo cierre la termina.
- **Prueba de humo**: ejecución automática del ejecutable que comprueba que la aplicación es capaz de arrancar, sin intervención de nadie.

## Requisitos

### APP-001 · Arranque

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario inicie la aplicación, el sistema deberá mostrar la ventana principal en menos de 5 segundos desde que se inicia el ejecutable.
- **Criterios de aceptación:**
  1. Dado el ejecutable de la aplicación, cuando se inicia, entonces la ventana principal está lista en menos de 5 segundos.

### APP-002 · Título de la ventana

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar en la barra de título de la ventana principal el texto `pxls`.
- **Criterios de aceptación:**
  1. Dada la ventana principal abierta, cuando se lee su título, entonces es exactamente `pxls`.

### APP-003 · Tamaño de la ventana

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se abra la ventana principal, el sistema deberá mostrarla con un tamaño inicial de 420 × 640 píxeles lógicos, deberá permitir redimensionarla, no deberá permitir reducirla por debajo de 360 × 480 píxeles lógicos y, cuando sea más baja que su contenido, deberá mostrar una barra de desplazamiento vertical.
- **Criterios de aceptación:**
  1. Dada la aplicación recién iniciada, cuando se mide la ventana principal, entonces mide 420 × 640 píxeles lógicos.
  2. Dada la ventana principal, cuando se redimensiona a 300 × 300, entonces mide 360 × 480.
  3. Dada la ventana principal, cuando se redimensiona a 600 × 700, entonces mide 600 × 700.
  4. Dada la ventana principal de 360 × 480, cuando se observa, entonces muestra una barra de desplazamiento vertical que da acceso a todo su contenido.

### APP-004 · Icono

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar el icono de `pxls` en la ventana principal, en la barra de tareas y en el propio fichero ejecutable: un cuentagotas sobre un cuadrado de color, disponible en varias resoluciones.
- **Criterios de aceptación:**
  1. Dada la ventana principal, cuando se consulta su icono, entonces es el icono de `pxls` y no el genérico.
  2. Dado el ejecutable generado, cuando se lee su icono, entonces es el icono de `pxls`.

### APP-005 · Versión visible

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar el número de versión de la aplicación, que coincide con el del proyecto, en la barra de estado al pie de la ventana principal, con el formato `v<versión>`.
- **Criterios de aceptación:**
  1. Dado un proyecto con versión `0.1.0`, cuando se abre la ventana principal, entonces la barra de estado muestra `v0.1.0`.

### APP-006 · Idioma de la interfaz

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar todos los textos de la interfaz en español, incluidos los textos estándar que aporta el propio sistema de ventanas (botones de diálogos, menús contextuales). Se exceptúan el nombre del producto, su versión, los nombres de los formatos de color (HEX, RGB, HSL, HSV) y los colores escritos en esos formatos.
- **Criterios de aceptación:**
  1. Dada la ventana principal, cuando se recorren sus textos visibles, entonces cada uno está en español o es una de las excepciones del enunciado.
  2. Dado un diálogo estándar con el botón «Cancel», cuando se muestra, entonces el botón dice «Cancelar».

### APP-007 · Cierre

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario cierre la ventana principal, el sistema deberá terminar la aplicación con el código de salida 0.
- **Criterios de aceptación:**
  1. Dada la aplicación abierta, cuando se cierra la ventana principal, entonces el proceso termina con el código 0.

### APP-008 · Ejecutable de Windows

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá poder distribuirse como un único fichero `pxls.exe` que se ejecuta en Windows 10 y 11 de 64 bits sin tener Python instalado.
- **Criterios de aceptación:**
  1. Dado el ejecutable copiado a una carpeta fuera del proyecto y un `PATH` sin ningún Python, cuando se inicia con `--smoke-test`, entonces termina con el código 0.
  2. Dado el comando de empaquetado del proyecto, cuando se ejecuta, entonces genera un único fichero `pxls.exe`.

### APP-009 · Prueba de humo

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el ejecutable se inicie con la opción `--smoke-test`, el sistema deberá crear la ventana principal sin mostrarla y terminar con el código 0 si la aplicación ha arrancado correctamente, o con un código distinto de 0 si no.
- **Criterios de aceptación:**
  1. Dado un ejecutable correcto, cuando se inicia con `--smoke-test`, entonces termina con el código 0 en menos de 10 segundos y sin mostrar ninguna ventana.
  2. Dado un ejecutable al que le falta una dependencia, cuando se inicia con `--smoke-test`, entonces termina con un código distinto de 0.
- **Notas:** es la prueba que la verificación completa ejecuta en cada commit (ANCH-033 en `specs/spec-anchor/spec.md`).

## Notas

- La versión del proyecto es la única fuente del número de versión: el ejecutable, la ventana y la etiqueta `vX.Y.Z` de `main` muestran el mismo.
