---
capability: clipboard
prefix: CLIP
owner: Bartosz Kucmierz
---

# Copiar al portapapeles

## Propósito

Llevar el color actual a cualquier otra herramienta (editor de código, programa de diseño, documento) con un solo gesto, en el formato que se necesite. Es el paso que cierra el ciclo del cuentagotas y del selector: capturar o ajustar un color sólo es útil si después se puede usar en otro sitio.

## Alcance

- Copiar el color actual en HEX, RGB, HSL o HSV.
- Atajo de teclado para copiar.
- Confirmación visible de lo copiado.
- Qué ocurre si no se puede escribir en el portapapeles.

## Fuera de alcance

- Pegar un color desde el portapapeles (el HEX ya se puede escribir a mano, SEL-007).
- Copiar varios colores a la vez o una paleta (MEJ-008).
- Formatos que no existen en `specs/color-model/spec.md`.

## Glosario

- **Portapapeles**: el portapapeles de Windows, compartido con el resto de aplicaciones.
- **Texto del formato**: el texto que muestra el panel del color actual para ese formato (PICK-009), por ejemplo `rgb(255, 136, 0)`.

## Requisitos

### CLIP-001 · Copiar en un formato

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse el botón «Copiar» que hay al lado de cada formato (HEX, RGB, HSL y HSV) en el panel del color actual, el sistema deberá poner en el portapapeles exactamente el texto de ese formato, sin espacios ni saltos de línea añadidos.
- **Criterios de aceptación:**
  1. Dado el color actual `#FF8800FF`, cuando se copia en RGB, entonces el portapapeles contiene exactamente `rgb(255, 136, 0)`.
  2. Dado el color actual `#FF880080`, cuando se copia en HSL, entonces el portapapeles contiene exactamente `hsla(32, 100%, 50%, 0.5)`.
  3. Dado cualquier color, cuando se copia en cada uno de los cuatro formatos, entonces el texto copiado coincide con el que muestra el panel.

### CLIP-002 · Atajo de teclado

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse `Ctrl+C` con la ventana principal en primer plano y el foco fuera de un campo de texto, el sistema deberá copiar el color actual en HEX; con el foco en un campo de texto, `Ctrl+C` deberá copiar el texto seleccionado como de costumbre.
- **Criterios de aceptación:**
  1. Dado el color actual `#3A86FFFF` y el foco en el cuadrado del selector, cuando se pulsa `Ctrl+C`, entonces el portapapeles contiene `#3A86FFFF`.
  2. Dado el texto `86FF` seleccionado en el campo HEX, cuando se pulsa `Ctrl+C`, entonces el portapapeles contiene `86FF`.

### CLIP-003 · Confirmación

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se copie un color, el sistema deberá mostrar en la barra de estado `Copiado: <texto>` durante 2 segundos.
- **Criterios de aceptación:**
  1. Dado el color actual `#FF8800FF`, cuando se copia en HEX, entonces la barra de estado dice `Copiado: #FF8800FF` y el mensaje desaparece a los 2 segundos.

### CLIP-004 · Copiar al capturar

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el cuentagotas capture un color, el sistema deberá dejar el portapapeles como estaba, para no sustituir sin avisar lo que hubiera en él; el color se copia con un clic o con `Ctrl+C`.
- **Criterios de aceptación:**
  1. Dado un portapapeles con el texto `hola`, cuando se captura un color con el cuentagotas, entonces el portapapeles sigue conteniendo `hola`.

### CLIP-005 · Portapapeles no disponible

- **Estado:** implemented
- **Enunciado (EARS):** Si no se puede escribir en el portapapeles (por ejemplo, porque otra aplicación lo tiene bloqueado), entonces el sistema deberá avisar en la barra de estado de que no se ha podido copiar, sin cambiar el color actual.
- **Criterios de aceptación:**
  1. Dado un portapapeles que rechaza la escritura, cuando se copia un color, entonces la barra de estado dice que no se ha podido copiar y el color actual no cambia.

## Notas

- Los textos de los botones y de los mensajes van en español («Copiar», «Copiado: …») para cumplir APP-006 (`specs/app-shell/spec.md`).
- El panel crece una columna (los botones «Copiar»); la ventana debe seguir cabiendo en 420 × 640 sin desplazamiento (SEL-009).
