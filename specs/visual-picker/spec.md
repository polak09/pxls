---
capability: visual-picker
prefix: SEL
owner: Bartosz Kucmierz
---

# Selector visual

## Propósito

Permitir crear o ajustar un color sin necesidad de encontrarlo en la pantalla: eligiéndolo sobre un cuadrado de saturación y brillo con una barra de tono, regulando su transparencia y retocando cada componente con precisión. El selector trabaja siempre sobre el color actual, el mismo que captura el cuentagotas y que muestra el panel.

## Alcance

- Cuadrado de saturación y valor, y barra de tono.
- Control del alfa.
- Una barra y un campo numérico por componente.
- Edición manual del color en HEX.
- Sincronía con el color actual.

## Fuera de alcance

- Escribir a mano un color en RGB, HSL o HSV como texto (`rgb(…)`): los campos por componente cubren esa necesidad.
- Otros modelos de selector (rueda de color, HSL, OKLCH).
- Armonías y paletas sugeridas.

## Glosario

- **Cuadrado SV**: área en la que el eje horizontal es la saturación (0 % a la izquierda, 100 % a la derecha) y el vertical el valor (100 % arriba, 0 % abajo), pintada con el tono actual.
- **Barra de tono**: área con los tonos de 0 a 360 grados.
- **Componentes**: rojo, verde y azul (0–255), tono (0–360), saturación y valor (0–100 %) y alfa (0–100 %).

## Requisitos

### SEL-001 · Cuadrado de saturación y valor

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse o arrastre sobre el cuadrado SV, el sistema deberá cambiar la saturación y el valor del color actual según la posición del puntero, sin cambiar el tono ni el alfa.
- **Criterios de aceptación:**
  1. Dado el tono 0, cuando se pulsa la esquina superior derecha del cuadrado, entonces el color actual es `#FF0000FF`.
  2. Dado cualquier tono, cuando se pulsa la esquina superior izquierda, entonces el color actual es `#FFFFFFFF`.
  3. Dado cualquier tono, cuando se pulsa el borde inferior, entonces el color actual es `#000000FF`.
  4. Dado un color con alfa 128, cuando se pulsa en el cuadrado, entonces el alfa sigue siendo 128.
  5. Dado un arrastre que sale del cuadrado, cuando continúa fuera, entonces la saturación y el valor se quedan en el borde más cercano.

### SEL-002 · Barra de tono

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse o arrastre sobre la barra de tono, el sistema deberá cambiar el tono del color actual sin cambiar la saturación, el valor ni el alfa. La barra es vertical, está a la derecha del cuadrado y va del tono 0 (arriba) al 360 (abajo).
- **Criterios de aceptación:**
  1. Dado el color `#FF0000FF`, cuando se pulsa la barra en la posición del tono 120, entonces el color actual es `#00FF00FF`.
  2. Dado un color con saturación 50 % y valor 80 %, cuando se cambia el tono, entonces la saturación y el valor no cambian.

### SEL-003 · Indicadores de posición

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá marcar en el cuadrado SV y en la barra de tono la posición que corresponde al color actual, y moverla cada vez que este cambie.
- **Criterios de aceptación:**
  1. Dado el color `#FF0000FF`, cuando se observa el selector, entonces el indicador del cuadrado está en la esquina superior derecha y el de la barra en el tono 0.
  2. Dado un color capturado con el cuentagotas, cuando termina la captura, entonces los indicadores se mueven a su posición.

### SEL-004 · Conservar tono y saturación

- **Estado:** implemented
- **Enunciado (EARS):** Mientras el usuario ajusta el color con el selector, el sistema deberá conservar el tono y la saturación elegidos aunque el color pase por el negro o por un gris, en los que no están definidos.
- **Criterios de aceptación:**
  1. Dado el tono 200 y la saturación 80 %, cuando se baja el valor a 0 % y se vuelve a subir, entonces el tono sigue siendo 200 y la saturación 80 %.
  2. Dado el tono 200, cuando se lleva la saturación a 0 % y se vuelve a subir, entonces el tono sigue siendo 200.

### SEL-005 · Alfa

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario cambie el alfa con su barra o con su campo, de 0 % (transparente) a 100 % (opaco), el sistema deberá cambiar el alfa del color actual sin cambiar sus otros componentes; la barra del alfa se pinta sobre un fondo de cuadros que deja ver la transparencia.
- **Criterios de aceptación:**
  1. Dado `#FF8800FF`, cuando se lleva el alfa al 50 %, entonces el color actual es `#FF880080`.
  2. Dado cualquier color, cuando se cambia el alfa, entonces sus componentes rojo, verde y azul no cambian.

### SEL-006 · Barra y campo por componente

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá ofrecer para cada componente (Rojo, Verde y Azul de 0 a 255, Tono de 0 a 360, Saturación, Valor y Alfa de 0 a 100 %) una barra deslizante y un campo en el que escribir el número, con la etiqueta en español; cuando el usuario cambie la barra o el campo, deberá cambiar sólo ese componente del color actual, y la barra y el campo deberán mostrar siempre el mismo valor.
- **Criterios de aceptación:**
  1. Dado `#FF8800FF`, cuando se escribe 0 en Rojo, entonces el color actual es `#008800FF`.
  2. Dado `#FF0000FF`, cuando se escribe 240 en Tono, entonces el color actual es `#0000FFFF`.
  3. Dado un valor fuera de rango (por ejemplo 300 en Rojo), cuando se escribe, entonces el campo lo limita al máximo permitido.
  4. Dado `#FF8800FF`, cuando se lleva la barra de Rojo a 0, entonces el color actual es `#008800FF` y el campo Rojo muestra 0.
  5. Dado cualquier componente, cuando se escribe un valor en su campo, entonces su barra se mueve a ese valor.

### SEL-007 · Escribir el color en HEX

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario escriba un color en el campo HEX y confirme, el sistema deberá convertirlo en el color actual si es válido según `specs/color-model/spec.md` (COLOR-002) y, si no lo es, deberá mantener el color actual y mostrar el motivo (COLOR-003). Sólo el HEX se escribe como texto; los demás formatos se ajustan con la barra y el campo de cada componente (SEL-006).
- **Criterios de aceptación:**
  1. Dado el campo HEX, cuando se escribe `#3a86ff` y se pulsa `Intro`, entonces el color actual es `#3A86FFFF`.
  2. Dado el campo HEX, cuando se escribe `#GG0000` y se pulsa `Intro`, entonces el color actual no cambia y se muestra que `G` no es un dígito hexadecimal.

### SEL-008 · Sincronía con el color actual

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mantener sincronizados el selector, sus campos, el panel del color actual y el cuentagotas: un cambio en cualquiera de ellos se refleja en todos los demás.
- **Criterios de aceptación:**
  1. Dado un color capturado con el cuentagotas, cuando termina la captura, entonces el selector y los campos muestran ese color.
  2. Dado un cambio en el cuadrado SV, cuando se suelta el ratón, entonces el panel del color actual muestra el nuevo color.

### SEL-009 · Ubicación en la ventana

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar el selector en la ventana principal, entre el botón «Capturar color» y el panel del color actual, sin que haga falta desplazarse con el tamaño inicial de la ventana (APP-003).
- **Criterios de aceptación:**
  1. Dada la ventana principal con su tamaño inicial, cuando se observa, entonces el cuadrado, la barra de tono, las barras y campos de los siete componentes y el panel están visibles por completo.

## Notas

- Las etiquetas de los campos van en español (Rojo, Verde, Azul…) para cumplir APP-006 (`specs/app-shell/spec.md`) sin ampliar sus excepciones.
- SEL-004 implica que el selector guarda su propio tono y saturación además del color actual, porque un color RGB negro o gris no los conserva.
