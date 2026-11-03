---
capability: history
prefix: HIST
owner: Bartosz Kucmierz
---

# Historial

## Propósito

Recordar los colores con los que se ha trabajado para recuperarlos sin tener que volver a capturarlos o a ajustarlos, también después de cerrar y abrir `pxls`.

## Alcance

- Qué colores entran en el historial y en qué orden.
- Límite de colores y duplicados.
- Recuperar un color del historial.
- Quitar colores y vaciar el historial.
- Conservar el historial entre sesiones y qué hacer si su fichero está dañado o no se puede guardar.
- Dónde se muestra en la ventana.

## Fuera de alcance

- Nombrar, agrupar o exportar colores: es cosa de las paletas (MEJ-008).
- Sincronizar el historial entre equipos.

## Glosario

- **Entrada**: un color del historial.
- **Usar un color**: capturarlo con el cuentagotas, confirmarlo en el campo HEX o copiarlo al portapapeles. Los pasos intermedios del selector no cuentan.

## Requisitos

### HIST-001 · Qué entra en el historial

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario use un color (capturarlo con el cuentagotas, confirmarlo en el campo HEX o copiarlo al portapapeles), el sistema deberá añadirlo al historial; los pasos intermedios del selector no deberán entrar, porque llenarían el historial de colores de paso.
- **Criterios de aceptación:**
  1. Dado un historial vacío, cuando se captura `#FF8800FF` con el cuentagotas, entonces el historial contiene `#FF8800FF`.
  2. Dado un historial vacío, cuando se arrastra por el cuadrado del selector sin copiar, entonces el historial sigue vacío.
  3. Dado un historial vacío, cuando se confirma `#3A86FF` en el campo HEX y después se copia en RGB, entonces el historial contiene sólo `#3A86FFFF`.

### HIST-002 · Orden

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar el historial con el color usado más recientemente en primer lugar.
- **Criterios de aceptación:**
  1. Dados los colores usados `#FF0000FF`, `#00FF00FF` y `#0000FFFF`, en ese orden, cuando se observa el historial, entonces su orden es `#0000FFFF`, `#00FF00FF`, `#FF0000FF`.

### HIST-003 · Límite

- **Estado:** implemented
- **Enunciado (EARS):** Si al añadir un color el historial supera el límite de 20 entradas, entonces el sistema deberá quitar la más antigua.
- **Criterios de aceptación:**
  1. Dado un historial con 20 entradas, cuando se usa un color nuevo, entonces el historial sigue teniendo 20 entradas, el color nuevo es el primero y la entrada más antigua ya no está.

### HIST-004 · Duplicados

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario use un color que ya está en el historial, el sistema deberá moverlo al primer lugar en vez de repetirlo.
- **Criterios de aceptación:**
  1. Dado el historial `#0000FFFF`, `#FF0000FF`, cuando se usa `#FF0000FF`, entonces el historial es `#FF0000FF`, `#0000FFFF`.

### HIST-005 · Recuperar un color

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse una entrada del historial, el sistema deberá convertirla en el color actual sin cambiar el orden del historial.
- **Criterios de aceptación:**
  1. Dado el historial `#0000FFFF`, `#FF0000FF`, cuando se pulsa `#FF0000FF`, entonces el color actual es `#FF0000FF` y el orden del historial no cambia.
  2. Dada una entrada, cuando se deja el puntero encima, entonces se ve su HEX.

### HIST-006 · Quitar y vaciar

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Quitar del historial» en el menú del clic derecho de una entrada, el sistema deberá quitarla; cuando pulse «Vaciar historial» y confirme, deberá vaciar todo el historial.
- **Criterios de aceptación:**
  1. Dado el historial `#0000FFFF`, `#FF0000FF`, cuando se quita `#0000FFFF`, entonces el historial es `#FF0000FF`.
  2. Dado un historial con entradas, cuando se vacía y se confirma, entonces queda vacío.
  3. Dado un historial con entradas, cuando se pide vaciarlo y se cancela, entonces no cambia.

### HIST-007 · Conservar entre sesiones

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá conservar el historial al cerrar la aplicación y recuperarlo, con el mismo orden, al volver a abrirla.
- **Criterios de aceptación:**
  1. Dado el historial `#0000FFFF`, `#FF0000FF`, cuando se cierra y se vuelve a abrir la aplicación, entonces el historial es `#0000FFFF`, `#FF0000FF`.
  2. Dado que nunca se ha usado la aplicación, cuando se abre, entonces el historial está vacío.

### HIST-008 · Fichero del historial dañado

- **Estado:** implemented
- **Enunciado (EARS):** Si al arrancar el historial guardado no se puede leer o está dañado, entonces el sistema deberá arrancar con el historial vacío, avisar en la barra de estado y conservar una copia del fichero dañado para no perderlo.
- **Criterios de aceptación:**
  1. Dado un fichero de historial con contenido no válido, cuando se abre la aplicación, entonces el historial está vacío, la barra de estado avisa y la copia del fichero dañado existe.

### HIST-009 · Ubicación en la ventana

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar el historial en la ventana principal como una rejilla de muestras de color, debajo del panel del color actual, visible sin desplazarse con el tamaño inicial de la ventana (420 × 780, APP-003). El historial va en una pestaña «Historial», que compartirá espacio con la futura pestaña «Paletas» (MEJ-008), con dos filas de 10 muestras de 24 px.
- **Criterios de aceptación:**
  1. Dada la ventana principal con su tamaño inicial y un historial lleno, cuando se observa, entonces todas sus entradas están visibles sin desplazarse.

### HIST-010 · Fallo al guardar el historial

- **Estado:** implemented
- **Enunciado (EARS):** Si no se puede guardar el historial (por ejemplo, porque el disco está lleno o la carpeta no admite escritura), entonces el sistema deberá conservarlo en memoria mientras la aplicación siga abierta, volver a intentar guardarlo en cada cambio y avisar en la barra de estado durante 10 segundos con el texto «No se ha podido guardar el historial en `<ruta del fichero>`; se conserva mientras pxls siga abierto.». El aviso se muestra la primera vez que falla y no se repite hasta que el historial se haya vuelto a guardar bien; si coincide con otro mensaje de la barra de estado, como «Copiado: …», lo sustituye.
- **Criterios de aceptación:**
  1. Dado un fichero del historial que no se puede escribir, cuando se confirma `#FF0000` en el campo HEX, entonces el historial contiene `#FF0000FF` y la barra de estado muestra el aviso con la ruta del fichero.
  2. Dado que el guardado ya ha fallado y se ha avisado, cuando se borra el aviso, se confirma `#0000FF` y el guardado vuelve a fallar, entonces la barra de estado no muestra ningún aviso nuevo.
  3. Dado que el guardado ha fallado y después ha vuelto a funcionar, cuando vuelve a fallar, entonces la barra de estado muestra el aviso otra vez.
  4. Dado un fichero del historial que no se puede escribir, cuando se copia el color actual en HEX, entonces el texto está en el portapapeles y la barra de estado muestra el aviso del historial en lugar de «Copiado: …».
  5. Dado que el guardado ha fallado con `#FF0000FF` y después vuelve a funcionar, cuando se confirma `#0000FF`, entonces el fichero guardado contiene `#0000FFFF` y `#FF0000FF`, en ese orden.

## Notas

- Los textos («Historial», «Quitar del historial», «Vaciar historial» y los avisos de HIST-008 y HIST-010) van en español, por APP-006 (`specs/app-shell/spec.md`). Por eso los avisos no incluyen el mensaje de error del sistema, que puede venir en inglés.
- HIST-009 cambia el tamaño inicial de APP-003 (de 420 × 640 a 420 × 780) en el mismo commit.
