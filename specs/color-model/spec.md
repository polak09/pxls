---
capability: color-model
prefix: COLOR
owner: Bartosz Kucmierz
---

# Modelo de color y formatos

## Propósito

Dar a `pxls` una única forma de representar un color y de convertirlo entre los formatos con los que trabaja quien lo usa: HEX, RGB, HSL y HSV, todos con canal alfa. El cuentagotas, el selector, el portapapeles, el historial y las paletas se apoyan en esta capacidad, así que una conversión incorrecta aquí se propagaría a todas ellas.

## Alcance

- Representación de un color con canal alfa.
- Lectura de colores escritos en HEX.
- Escritura de un color en HEX, RGB, HSL y HSV.
- Conversiones entre RGB, HSL y HSV en ambos sentidos.

## Fuera de alcance

- Leer colores escritos en RGB, HSL o HSV (p. ej. `rgb(255, 0, 0)`): se decide con la edición manual de valores del selector (MEJ-005).
- Otros formatos: CMYK, OKLCH, nombres de color CSS.
- Espacios de color distintos de sRGB y gestión del color (perfiles ICC).

## Glosario

- **Color**: cuatro componentes enteros entre 0 y 255: rojo (R), verde (G), azul (B) y alfa (A, la opacidad; 255 es opaco).
- **Opaco**: color con alfa 255.
- **Tono (H)**: ángulo en grados, en el intervalo [0, 360).
- **Saturación (S), luminosidad (L) y valor (V)**: porcentajes entre 0 y 100.

## Requisitos

### COLOR-001 · Color con alfa

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá representar un color mediante sus componentes rojo, verde, azul y alfa, cada uno un entero entre 0 y 255, y deberá rechazar cualquier componente fuera de ese intervalo. El alfa se guarda igual que en HEX; los formatos que lo muestran como fracción lo convierten al escribirlo.
- **Criterios de aceptación:**
  1. Dados R 255, G 136, B 0 y A 255, cuando se crea el color, entonces sus componentes son exactamente esos.
  2. Dado un componente 256 o −1, cuando se crea el color, entonces se rechaza indicando qué componente está fuera de rango.
  3. Dados dos colores con los mismos cuatro componentes, cuando se comparan, entonces son iguales.

### COLOR-002 · Leer HEX

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se introduzca un color en HEX con la forma `#RRGGBBAA`, `#RRGGBB` (alfa 255), `#RGBA` o `#RGB` (cada dígito se duplica), con o sin `#`, en mayúsculas o minúsculas y con o sin espacios al principio y al final, el sistema deberá obtener sus cuatro componentes.
- **Criterios de aceptación:**
  1. Dado `#FF8800FF`, cuando se lee, entonces el color es R 255, G 136, B 0, A 255.
  2. Dado `#ff880080`, cuando se lee, entonces el color es R 255, G 136, B 0, A 128.
  3. Dado `#FF8800`, cuando se lee, entonces el color es R 255, G 136, B 0, A 255.
  4. Dado `#F808`, cuando se lee, entonces el color es R 255, G 136, B 0, A 136.
  5. Dado `  f80 ` (sin `#` y con espacios), cuando se lee, entonces el color es R 255, G 136, B 0, A 255.

### COLOR-003 · HEX no válido

- **Estado:** implemented
- **Enunciado (EARS):** Si el texto introducido no es un color HEX válido, entonces el sistema deberá rechazarlo con un mensaje en español que explique el motivo.
- **Criterios de aceptación:**
  1. Dado `#GG0000FF`, cuando se lee, entonces se rechaza porque `G` no es un dígito hexadecimal.
  2. Dado `#12345`, cuando se lee, entonces se rechaza porque la longitud no es válida.
  3. Dado un texto vacío, cuando se lee, entonces se rechaza.

### COLOR-004 · Escribir HEX

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá escribir un color en HEX como `#RRGGBBAA`, en mayúsculas, también cuando el color es opaco.
- **Criterios de aceptación:**
  1. Dado R 255, G 136, B 0, A 255, cuando se escribe en HEX, entonces el resultado es `#FF8800FF`.
  2. Dado R 0, G 0, B 0, A 128, cuando se escribe en HEX, entonces el resultado es `#00000080`.

### COLOR-005 · Escribir RGB

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá escribir un color en RGB como `rgb(R, G, B)` si es opaco y como `rgba(R, G, B, A)` si no lo es, con el alfa como fracción entre 0 y 1 con dos decimales como máximo.
- **Criterios de aceptación:**
  1. Dado R 255, G 136, B 0, A 255, cuando se escribe en RGB, entonces el resultado es `rgb(255, 136, 0)`.
  2. Dado R 0, G 0, B 0, A 128, cuando se escribe en RGB, entonces el resultado es `rgba(0, 0, 0, 0.5)`.
  3. Dado R 10, G 20, B 30, A 64, cuando se escribe en RGB, entonces el resultado es `rgba(10, 20, 30, 0.25)`.

### COLOR-006 · Calcular HSL

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá calcular el tono, la saturación y la luminosidad de un color con el modelo HSL estándar; cuando la saturación sea 0, el tono deberá ser 0.
- **Criterios de aceptación:**
  1. Dado R 255, G 0, B 0, cuando se calcula su HSL, entonces es H 0, S 100, L 50.
  2. Dado R 255, G 136, B 0, cuando se calcula su HSL, entonces es H 32, S 100, L 50.
  3. Dado R 128, G 128, B 128, cuando se calcula su HSL, entonces H y S son 0 y L está entre 50,1 y 50,2.

### COLOR-007 · Escribir HSL

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá escribir un color en HSL con el tono en grados y la saturación y la luminosidad en porcentaje, redondeados a números enteros como en COLOR-010, como `hsl(H, S%, L%)` si es opaco y `hsla(H, S%, L%, A)` si no lo es, con el alfa como en COLOR-005.
- **Criterios de aceptación:**
  1. Dado R 255, G 136, B 0, A 255, cuando se escribe en HSL, entonces el resultado es `hsl(32, 100%, 50%)`.
  2. Dado R 128, G 128, B 128, A 255, cuando se escribe en HSL, entonces el resultado es `hsl(0, 0%, 50%)`.
  3. Dado R 255, G 0, B 1, A 255 (tono 359,76), cuando se escribe en HSL, entonces el resultado es `hsl(0, 100%, 50%)`: un tono que se redondea a 360 se escribe como 0.

### COLOR-008 · Calcular HSV

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá calcular el tono, la saturación y el valor de un color con el modelo HSV estándar; cuando la saturación sea 0, el tono deberá ser 0.
- **Criterios de aceptación:**
  1. Dado R 255, G 136, B 0, cuando se calcula su HSV, entonces es H 32, S 100, V 100.
  2. Dado R 102, G 153, B 204, cuando se calcula su HSV, entonces es H 210, S 50, V 80.

### COLOR-009 · Escribir HSV

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá escribir un color en HSV como `hsv(H, S%, V%)` si es opaco y `hsva(H, S%, V%, A)` si no lo es, con el mismo redondeo que HSL (COLOR-007) y el alfa como en RGB (COLOR-005).
- **Criterios de aceptación:**
  1. Dado R 102, G 153, B 204, A 255, cuando se escribe en HSV, entonces el resultado es `hsv(210, 50%, 80%)`.
  2. Dado R 255, G 136, B 0, A 128, cuando se escribe en HSV, entonces el resultado es `hsva(32, 100%, 100%, 0.5)`.

### COLOR-010 · Color desde HSL

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se den un tono, una saturación, una luminosidad y un alfa, el sistema deberá obtener el color correspondiente, redondeando cada componente al entero más cercano (los empates, hacia arriba).
- **Criterios de aceptación:**
  1. Dados H 32, S 100, L 50 y A 255, cuando se obtiene el color, entonces es R 255, G 136, B 0, A 255.
  2. Dados H 0, S 0, L 100 y A 255, cuando se obtiene el color, entonces es R 255, G 255, B 255, A 255.

### COLOR-011 · Color desde HSV

- **Estado:** implemented
- **Enunciado (EARS):** Cuando se den un tono, una saturación, un valor y un alfa, el sistema deberá obtener el color correspondiente con el mismo redondeo que COLOR-010.
- **Criterios de aceptación:**
  1. Dados H 210, S 50, V 80 y A 255, cuando se obtiene el color, entonces es R 102, G 153, B 204, A 255.

### COLOR-012 · Valores HSL y HSV fuera de rango

- **Estado:** implemented
- **Enunciado (EARS):** Si al obtener un color desde HSL o HSV el tono, la saturación, la luminosidad o el valor están fuera de su intervalo, entonces el sistema deberá normalizar el tono dando la vuelta al círculo (420 → 60, −60 → 300) y rechazar una saturación, luminosidad o valor fuera de 0–100.
- **Criterios de aceptación:**
  1. Dados H 420, S 100, L 50, cuando se obtiene el color, entonces es el mismo que con H 60: R 255, G 255, B 0.
  2. Dados H −60, S 100, V 100 en HSV, cuando se obtiene el color, entonces es el mismo que con H 300: R 255, G 0, B 255.
  3. Dada S 101 o L −1, cuando se obtiene el color, entonces se rechaza indicando el valor fuera de rango.

### COLOR-013 · Ida y vuelta sin pérdidas

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá garantizar que, para cualquier color, calcular su HSL o su HSV y obtener de nuevo el color a partir de esos valores, sin redondearlos, devuelve exactamente el color de partida.
- **Criterios de aceptación:**
  1. Dado cualquier color de los 2³² posibles, cuando se pasa a HSL y se vuelve, entonces el color es idéntico.
  2. Dado cualquier color de los 2³² posibles, cuando se pasa a HSV y se vuelve, entonces el color es idéntico.
  3. Dado cualquier color, cuando se escribe en HEX y se vuelve a leer, entonces el color es idéntico.
- **Notas:** se comprueba con tests basados en propiedades (constitución VII.3).

## Notas

- Los formatos de salida usan siempre el punto como separador decimal (`0.5`), aunque la interfaz esté en español: son los que aceptan CSS y la mayoría de herramientas de diseño.
- Los valores redondeados que se muestran (COLOR-007, COLOR-009) no garantizan la ida y vuelta exacta; la garantía de COLOR-013 es para los valores sin redondear.
