---
capability: screen-picker
prefix: PICK
owner: Bartosz Kucmierz
---

# Cuentagotas de pantalla

## Propósito

Capturar el color exacto de cualquier píxel visible en la pantalla y convertirlo en el color actual de `pxls`. Es la función principal de un color picker de escritorio: la que permite llevarse un color de una web, una imagen o cualquier otra aplicación.

## Alcance

- Activar el modo cuentagotas y salir de él (capturando o cancelando).
- Lupa para apuntar con precisión.
- Varias pantallas y escalado de pantalla.
- Panel del color actual en la ventana principal, con el color en los cuatro formatos de `specs/color-model/spec.md`.

## Fuera de alcance

- Copiar el color al portapapeles (MEJ-006), historial (MEJ-007) y selector visual (MEJ-005).
- Capturar el color medio de una zona.
- Contenido que Windows no deja capturar (ventanas protegidas, pantalla de bloqueo): se captura lo que Windows devuelva para ese píxel.

## Glosario

- **Modo cuentagotas**: estado en el que el cursor se convierte en cuentagotas sobre todas las pantallas y un clic captura un color.
- **Color actual**: el color con el que trabaja `pxls` en cada momento; lo cambian el cuentagotas y, más adelante, el selector, el historial y las paletas.
- **Píxel físico**: un píxel real de la pantalla, independiente del escalado que aplique Windows.

## Requisitos

### PICK-001 · Activar el cuentagotas

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse el botón «Capturar color» de la ventana principal o el atajo `Ctrl+Mayús+C` con la ventana principal en primer plano, el sistema deberá entrar en modo cuentagotas sobre todas las pantallas.
- **Criterios de aceptación:**
  1. Dada la ventana principal, cuando se pulsa «Capturar color», entonces el modo cuentagotas está activo.
  2. Dada la ventana principal con el foco, cuando se pulsa `Ctrl+Mayús+C`, entonces el modo cuentagotas está activo.

### PICK-002 · Qué se captura

- **Estado:** implemented
- **Enunciado (EARS):** Mientras el modo cuentagotas esté activo, el sistema deberá mostrar y capturar la pantalla tal como estaba al activar el cuentagotas (congelada), de modo que la lupa y el color capturado coinciden siempre.
- **Criterios de aceptación:**
  1. Dado un píxel que cambia de color después de activar el cuentagotas, cuando se captura, entonces el color es el que tenía el píxel al activar el cuentagotas.

### PICK-003 · Lupa

- **Estado:** implemented
- **Enunciado (EARS):** Mientras el modo cuentagotas esté activo, el sistema deberá mostrar junto al cursor una lupa con la zona que lo rodea ampliada, el píxel central resaltado y su color en HEX debajo. La zona es de 11 × 11 píxeles físicos ampliados 10 veces y la lupa se coloca al otro lado del cursor cuando no cabe en la pantalla.
- **Criterios de aceptación:**
  1. Dado el cursor sobre un píxel de color conocido rodeado de otro color, cuando se observa la lupa, entonces su celda central tiene el color del píxel, está resaltada y el HEX mostrado es el de ese píxel.
  2. Dado el cursor junto al borde derecho de una pantalla, cuando se observa la lupa, entonces se ve entera dentro de esa pantalla.

### PICK-004 · Capturar con un clic

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario haga clic con el botón izquierdo en modo cuentagotas, el sistema deberá tomar como color actual el del píxel físico bajo el cursor, con alfa 255, y salir del modo cuentagotas.
- **Criterios de aceptación:**
  1. Dado un píxel de color R 255, G 136, B 0 bajo el cursor, cuando se hace clic, entonces el color actual es R 255, G 136, B 0, A 255.
  2. Dado el modo cuentagotas activo, cuando se hace clic, entonces el modo cuentagotas deja de estar activo.

### PICK-005 · Cancelar

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse `Esc` o haga clic con el botón derecho en modo cuentagotas, el sistema deberá salir del modo cuentagotas sin cambiar el color actual.
- **Criterios de aceptación:**
  1. Dado un color actual `#FFFFFFFF` y el modo cuentagotas activo, cuando se pulsa `Esc`, entonces el color actual sigue siendo `#FFFFFFFF` y el modo deja de estar activo.
  2. Igual que el criterio 1, pero con un clic derecho.

### PICK-006 · Ajuste fino con el teclado

- **Estado:** implemented
- **Enunciado (EARS):** Mientras el modo cuentagotas esté activo, el sistema deberá mover el cursor un píxel físico con cada flecha del teclado y capturar con `Intro` como si fuera un clic.
- **Criterios de aceptación:**
  1. Dado el cursor en el píxel (100, 100) en modo cuentagotas, cuando se pulsa la flecha derecha, entonces el cursor está en (101, 100).
  2. Dado el cursor sobre un píxel, cuando se pulsa `Intro`, entonces se captura su color como en PICK-004.

### PICK-007 · Varias pantallas

- **Estado:** implemented
- **Enunciado (EARS):** Mientras el modo cuentagotas esté activo, el sistema deberá permitir capturar en cualquiera de las pantallas conectadas, también en las situadas a la izquierda o por encima de la principal.
- **Criterios de aceptación:**
  1. Dadas dos pantallas, con la secundaria a la izquierda de la principal, cuando se captura un píxel de la secundaria, entonces el color es el de ese píxel.

### PICK-008 · Escalado de pantalla

- **Estado:** implemented
- **Enunciado (EARS):** Mientras una pantalla use un escalado distinto del 100 %, el sistema deberá capturar el color del píxel físico exacto bajo el cursor, no una mezcla de los píxeles vecinos.
- **Criterios de aceptación:**
  1. Dada una pantalla al 150 % con un patrón de píxeles alternos blancos y negros, cuando se captura cualquiera de ellos, entonces el color es exactamente blanco o negro.

### PICK-009 · Panel del color actual

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar en la ventana principal una muestra del color actual y su valor en HEX, RGB, HSL y HSV, con los formatos de `specs/color-model/spec.md`, y actualizarlos cada vez que cambie el color actual.
- **Criterios de aceptación:**
  1. Dado el color actual R 255, G 136, B 0, A 255, cuando se observa el panel, entonces la muestra es de ese color y los valores son `#FF8800FF`, `rgb(255, 136, 0)`, `hsl(32, 100%, 50%)` y `hsv(32, 100%, 100%)`.
  2. Dado un color capturado con el cuentagotas, cuando termina la captura, entonces el panel muestra el nuevo color.

### PICK-010 · Color actual al arrancar

- **Estado:** implemented
- **Enunciado (EARS):** Cuando la aplicación arranque, el sistema deberá tener como color actual el blanco opaco, `#FFFFFFFF`.
- **Criterios de aceptación:**
  1. Dada la aplicación recién iniciada, cuando se observa el panel, entonces muestra `#FFFFFFFF`.

## Notas

- **Impacto en `app-shell`:** el panel añade textos a la ventana principal («Capturar color») y nombres de formatos (HEX, RGB, HSL, HSV). El criterio 1 de APP-006 (`specs/app-shell/spec.md`) sólo admite textos en español, el nombre del producto y su versión; habrá que ampliarlo para admitir los nombres de los formatos y las cadenas de color en el mismo commit que implemente este panel.
