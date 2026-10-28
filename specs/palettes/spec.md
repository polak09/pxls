---
capability: palettes
prefix: PAL
owner: Bartosz Kucmierz
---

# Paletas de color

## Propósito

Organizar los colores de un proyecto en paletas con nombre, que el usuario crea, ordena y conserva entre sesiones, y que puede llevar a otras herramientas o traer de ellas.

## Alcance

- Crear, renombrar y borrar paletas, y elegir la paleta activa.
- Añadir el color actual a una paleta, quitar colores y reordenarlos.
- Recuperar un color de una paleta.
- Límites de colores por paleta.
- Conservar las paletas entre sesiones, y qué hacer si su fichero está dañado o no se puede guardar.
- Exportar e importar paletas.
- Dónde se muestran en la ventana.

## Fuera de alcance

- Poner nombre a cada color de una paleta.
- Añadir a una paleta un color del historial sin convertirlo antes en el color actual.
- Sincronizar o compartir paletas entre equipos.

## Glosario

- **Paleta**: lista ordenada de colores con un nombre.
- **Paleta activa**: la paleta elegida en la pestaña «Paletas»; sobre ella actúan añadir, quitar, reordenar, renombrar, borrar y exportar.
- **Menú «Paleta»**: el menú del botón «Paleta» de la pestaña, con «Nueva paleta…», «Renombrar…», «Borrar…», «Importar…» y «Exportar…» (PAL-016).
- **Nombre válido**: el que cumple PAL-002.

## Requisitos

### PAL-001 · Crear una paleta

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Nueva paleta…» en el menú «Paleta» y confirme un nombre válido, el sistema deberá crear una paleta vacía con ese nombre y convertirla en la paleta activa.
- **Criterios de aceptación:**
  1. Dado que no hay paletas, cuando se elige «Nueva paleta…», se escribe `Web` y se confirma, entonces existe la paleta `Web`, vacía y activa.
  2. Dado el diálogo de «Nueva paleta…», cuando se cancela, entonces no se crea ninguna paleta.
  3. Dado que nunca se ha usado la aplicación, cuando se abre, entonces no hay ninguna paleta, «Añadir color actual» está desactivado y en el menú «Paleta» sólo están disponibles «Nueva paleta…» e «Importar…».

### PAL-002 · Nombre de una paleta

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá quitar los espacios del principio y del final del nombre de una paleta y exigir que tenga entre 1 y 40 caracteres y que no coincida, sin distinguir mayúsculas, con el de otra paleta; mientras el nombre no lo cumpla, no deberá permitir confirmar el diálogo y deberá explicar en él por qué.
- **Criterios de aceptación:**
  1. Dado el diálogo de «Nueva paleta…», cuando se escribe `  Web  ` y se confirma, entonces la paleta se llama `Web`.
  2. Dada la paleta `Web`, cuando en el diálogo de «Nueva paleta…» se escribe `web`, entonces no se puede confirmar y el diálogo dice que ya hay una paleta con ese nombre.
  3. Dado el diálogo de «Nueva paleta…», cuando el nombre está vacío o sólo tiene espacios, entonces no se puede confirmar y el diálogo dice que el nombre no puede estar vacío.
  4. Dado el diálogo de «Nueva paleta…», cuando se intenta escribir un nombre de 41 caracteres, entonces el campo se queda en 40.

### PAL-003 · Renombrar una paleta

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Renombrar…» en el menú «Paleta» y confirme un nombre válido, el sistema deberá cambiar el nombre de la paleta activa sin cambiar sus colores; el nombre actual de la propia paleta no cuenta como repetido.
- **Criterios de aceptación:**
  1. Dada la paleta activa `Web` con `#FF0000FF` y `#0000FFFF`, cuando se renombra a `Marca`, entonces se llama `Marca` y sus colores son `#FF0000FF` y `#0000FFFF`.
  2. Dada la paleta activa `Web`, cuando se renombra a `WEB`, entonces se puede confirmar y se llama `WEB`.
  3. Dado el diálogo de «Renombrar…», cuando se cancela, entonces el nombre no cambia.

### PAL-004 · Borrar una paleta

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Borrar…» en el menú «Paleta» y confirme, el sistema deberá borrar la paleta activa; la nueva paleta activa deberá ser la siguiente de la lista o, si era la última, la anterior.
- **Criterios de aceptación:**
  1. Dadas las paletas `A`, `B` y `C` con `B` activa, cuando se borra y se confirma, entonces quedan `A` y `C` y `C` es la activa.
  2. Dadas las paletas `A` y `B` con `B` activa, cuando se borra y se confirma, entonces queda `A` y es la activa.
  3. Dada una sola paleta, cuando se borra y se confirma, entonces no hay ninguna paleta.
  4. Dada la paleta activa `Web`, cuando se pide borrarla y se cancela, entonces sigue existiendo.

### PAL-005 · Elegir la paleta activa

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar las paletas en una lista desplegable, por orden alfabético sin distinguir mayúsculas, y mostrar los colores de la paleta que se elija en ella, que pasa a ser la paleta activa.
- **Criterios de aceptación:**
  1. Dadas las paletas `web`, `Fotos` y `Marca`, cuando se abre la lista, entonces su orden es `Fotos`, `Marca`, `web`.
  2. Dada la paleta activa `Web` y la paleta `Marca` con `#00FF00FF`, cuando se elige `Marca`, entonces `Marca` es la activa y la rejilla muestra `#00FF00FF`.

### PAL-006 · Añadir el color actual

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse «Añadir color actual», el sistema deberá añadir el color actual al final de la paleta activa; si ya está en ella, no deberá repetirlo: la paleta no cambia y la barra de estado avisa durante 4 segundos con «`<HEX>` ya está en la paleta `<nombre>`».
- **Criterios de aceptación:**
  1. Dada la paleta activa `Web` con `#FF0000FF` y el color actual `#0000FFFF`, cuando se pulsa «Añadir color actual», entonces `Web` es `#FF0000FF`, `#0000FFFF`.
  2. Dada la paleta activa `Web` con `#FF0000FF` y el color actual `#FF0000FF`, cuando se pulsa «Añadir color actual», entonces `Web` sigue siendo `#FF0000FF` y la barra de estado muestra «#FF0000FF ya está en la paleta Web».

### PAL-007 · Quitar un color

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Quitar de la paleta» en el menú del clic derecho de un color de la paleta activa, el sistema deberá quitarlo sin cambiar el orden de los demás.
- **Criterios de aceptación:**
  1. Dada la paleta activa con `#FF0000FF`, `#00FF00FF` y `#0000FFFF`, cuando se quita `#00FF00FF`, entonces la paleta es `#FF0000FF`, `#0000FFFF`.

### PAL-008 · Reordenar los colores

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario arrastre un color de la paleta activa y lo suelte sobre otra posición de la rejilla, o elija «Mover a la izquierda» o «Mover a la derecha» en el menú de su clic derecho, el sistema deberá colocarlo en esa posición y desplazar los demás sin cambiar su orden. Soltarlo sobre una posición vacía lo lleva al final.
- **Criterios de aceptación:**
  1. Dada la paleta activa con `#FF0000FF`, `#00FF00FF` y `#0000FFFF`, cuando se arrastra `#0000FFFF` y se suelta sobre `#FF0000FF`, entonces la paleta es `#0000FFFF`, `#FF0000FF`, `#00FF00FF`.
  2. Dada la misma paleta, cuando se arrastra `#FF0000FF` y se suelta sobre una posición vacía, entonces la paleta es `#00FF00FF`, `#0000FFFF`, `#FF0000FF`.
  3. Dada la misma paleta, cuando se elige «Mover a la derecha» en `#FF0000FF`, entonces la paleta es `#00FF00FF`, `#FF0000FF`, `#0000FFFF`.
  4. Dada la misma paleta, cuando se elige «Mover a la izquierda» en `#0000FFFF`, entonces la paleta es `#FF0000FF`, `#0000FFFF`, `#00FF00FF`.
  5. Dada la misma paleta, cuando se abre el menú del clic derecho de `#FF0000FF`, entonces «Mover a la izquierda» está desactivado, y en el de `#0000FFFF`, «Mover a la derecha».

### PAL-009 · Recuperar un color de una paleta

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario pulse un color de la paleta activa, el sistema deberá convertirlo en el color actual sin cambiar la paleta ni el historial.
- **Criterios de aceptación:**
  1. Dada la paleta activa con `#FF0000FF` y `#0000FFFF` y un historial vacío, cuando se pulsa `#0000FFFF`, entonces el color actual es `#0000FFFF`, la paleta no cambia y el historial sigue vacío.
  2. Dado un color de la paleta, cuando se deja el puntero encima, entonces se ve su HEX.

### PAL-010 · Límite de colores

- **Estado:** implemented
- **Enunciado (EARS):** Mientras la paleta activa tenga 20 colores, el máximo por paleta, el sistema deberá desactivar «Añadir color actual». El número de paletas no tiene límite.
- **Criterios de aceptación:**
  1. Dada la paleta activa con 20 colores, cuando se observa, entonces «Añadir color actual» está desactivado.
  2. Dada la paleta activa con 19 colores, cuando se añade el color actual, entonces tiene 20 y «Añadir color actual» se desactiva.

### PAL-011 · Conservar entre sesiones

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá conservar las paletas, sus colores en orden y cuál es la paleta activa al cerrar la aplicación, y recuperarlos al volver a abrirla.
- **Criterios de aceptación:**
  1. Dadas las paletas `Web` (`#FF0000FF`, `#0000FFFF`) y `Marca` (`#00FF00FF`) con `Marca` activa, cuando se cierra y se vuelve a abrir la aplicación, entonces están las dos paletas con los mismos colores en el mismo orden y `Marca` es la activa.

### PAL-012 · Fichero de las paletas dañado

- **Estado:** implemented
- **Enunciado (EARS):** Si al arrancar las paletas guardadas no se pueden leer o están dañadas, entonces el sistema deberá arrancar sin paletas, avisar en la barra de estado y conservar una copia del fichero dañado para no perderlo, como con el historial (HIST-008, `specs/history/spec.md`).
- **Criterios de aceptación:**
  1. Dado un fichero de paletas con contenido no válido, cuando se abre la aplicación, entonces no hay ninguna paleta, la barra de estado avisa y la copia del fichero dañado existe.

### PAL-013 · Fallo al guardar las paletas

- **Estado:** implemented
- **Enunciado (EARS):** Si no se pueden guardar las paletas, entonces el sistema deberá conservarlas en memoria mientras la aplicación siga abierta, volver a intentar guardarlas en cada cambio y avisar en la barra de estado durante 10 segundos con «No se han podido guardar las paletas en `<ruta del fichero>`; se conservan mientras pxls siga abierto.», con las mismas reglas de repetición que HIST-010 (`specs/history/spec.md`).
- **Criterios de aceptación:**
  1. Dado un fichero de paletas que no se puede escribir, cuando se crea la paleta `Web`, entonces `Web` existe y la barra de estado muestra el aviso con la ruta del fichero.
  2. Dado que el guardado ya ha fallado y se ha avisado, cuando se borra el aviso, se añade un color y el guardado vuelve a fallar, entonces la barra de estado no muestra ningún aviso nuevo.
  3. Dado que el guardado ha fallado y después vuelve a funcionar, cuando se añade un color, entonces el fichero guardado contiene todas las paletas.

### PAL-014 · Exportar una paleta

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Exportar…» en el menú «Paleta» y elija un fichero `.gpl` o `.txt`, el sistema deberá escribir en él la paleta activa y confirmarlo en la barra de estado con «Paleta exportada a `<ruta>`». En `.gpl` (GIMP Palette, que leen GIMP, Inkscape, Krita y Aseprite) se escriben su nombre y sus colores sin transparencia; si algún color no era opaco, la confirmación añade « sin transparencia: el formato .gpl no la guarda». En `.txt` se escribe un HEX `#RRGGBBAA` por línea, que sí la conserva. Si el fichero no se puede escribir, el sistema no deberá cambiar ningún fichero y deberá avisar con «No se ha podido exportar la paleta a `<ruta>`».
- **Criterios de aceptación:**
  1. Dada la paleta activa `Web` con `#FF0000FF` y `#0000FF80`, cuando se exporta a `web.txt`, entonces el fichero tiene las líneas `#FF0000FF` y `#0000FF80`.
  2. Dada la paleta activa `Web` con `#FF0000FF`, cuando se exporta a `web.gpl`, entonces el fichero empieza por `GIMP Palette`, tiene la línea `Name: Web` y una línea de color con los valores 255, 0 y 0.
  3. Dada la paleta activa con `#0000FF80`, cuando se exporta a `web.gpl`, entonces la barra de estado muestra «Paleta exportada a `<ruta>` sin transparencia: el formato .gpl no la guarda» y el color se escribe con los valores 0, 0 y 255.
  4. Dado un fichero que no se puede escribir, cuando se exporta, entonces la barra de estado muestra «No se ha podido exportar la paleta a `<ruta>`» y el fichero no cambia.

### PAL-015 · Importar una paleta

- **Estado:** implemented
- **Enunciado (EARS):** Cuando el usuario elija «Importar…» en el menú «Paleta» y elija un fichero en un formato admitido (PAL-014), el sistema deberá crear con sus colores una paleta nueva, convertirla en la paleta activa y confirmarlo en la barra de estado con «Paleta importada: `<nombre>`». La paleta toma el `Name:` del `.gpl` o, si no lo tiene, el nombre del fichero sin extensión, sin los espacios de los extremos y recortado a 40 caracteres (`Paleta importada` si queda vacío); si ya hay una paleta con ese nombre, se le añade « (2)», « (3)»…, recortando antes el nombre para que no pase de 40. Los colores repetidos se quitan y, si quedan más de 20 (PAL-010), se importan los 20 primeros y la confirmación añade «, con 20 de sus `<total>` colores». Si el fichero no se puede leer o no es una paleta válida, el sistema no deberá crear nada y deberá avisar con «No se ha podido importar `<ruta>`: no es una paleta .gpl o .txt válida».
- **Criterios de aceptación:**
  1. Dado un fichero `marca.txt` con `#FF0000FF` y `#0000FF80`, cuando se importa, entonces existe la paleta `marca` con esos dos colores y es la activa.
  2. Dado un fichero `.gpl` con `Name: Web` y la paleta `Web` ya existente, cuando se importa, entonces se crea la paleta `Web (2)`.
  3. Dado un fichero `.gpl` con el color `255 0 0`, cuando se importa, entonces la paleta tiene `#FF0000FF`.
  4. Dado un fichero `.txt` con la línea `rojo`, cuando se importa, entonces no se crea ninguna paleta y la barra de estado muestra «No se ha podido importar `<ruta>`: no es una paleta .gpl o .txt válida».
  5. Dada una paleta exportada a `.txt`, cuando se importa, entonces la paleta nueva tiene los mismos colores en el mismo orden.
  6. Dado un fichero `.txt` con 25 colores distintos, cuando se importa, entonces la paleta nueva tiene los 20 primeros y la barra de estado muestra «Paleta importada: `<nombre>`, con 20 de sus 25 colores».
  7. Dado un fichero `.txt` con `#FF0000FF`, `#0000FFFF` y `#FF0000FF`, cuando se importa, entonces la paleta nueva es `#FF0000FF`, `#0000FFFF`.

### PAL-016 · Ubicación en la ventana

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá mostrar las paletas en una pestaña «Paletas», a la derecha de la pestaña «Historial» (HIST-009, `specs/history/spec.md`), todo visible sin desplazarse con el tamaño inicial de la ventana (APP-003, `specs/app-shell/spec.md`): en la primera fila, la lista desplegable de paletas y, a su derecha, el botón «Paleta», que abre el menú con «Nueva paleta…», «Renombrar…», «Borrar…», «Importar…» y «Exportar…»; debajo, los colores de la paleta activa en una rejilla de dos filas de 10 muestras de 24 px y el botón «Añadir color actual».
- **Criterios de aceptación:**
  1. Dada la ventana principal con su tamaño inicial, cuando se abre la pestaña «Paletas» con una paleta activa llena, entonces la lista, el botón «Paleta», «Añadir color actual» y todos los colores están visibles sin desplazarse.
  2. Dada la ventana principal, cuando se observan sus pestañas, entonces son «Historial» y «Paletas», en ese orden.

## Notas

- Los textos de la pestaña, los diálogos y los avisos van en español, por APP-006 (`specs/app-shell/spec.md`), y no incluyen mensajes de error del sistema, que pueden venir en inglés.
- Añadir un color a una paleta o recuperarlo de ella no cuenta como usarlo: no entra en el historial (HIST-001, `specs/history/spec.md`).
