# Cambios

Notas de cada versión de `pxls`, la más reciente primero. Las versiones siguen el [versionado semántico](https://semver.org/lang/es/).

## 0.1.0 · Primera versión

Color picker de escritorio para Windows, distribuido como un único `pxls.exe` que funciona sin instalar Python.

### Cuentagotas de pantalla

- Captura el color de cualquier píxel visible con el botón «Capturar color» o con `Ctrl+Mayús+C`.
- Una lupa junto al cursor amplía 10 veces la zona de 11 × 11 píxeles que lo rodea y muestra el HEX del píxel central.
- Las flechas mueven el cursor píxel a píxel e `Intro` captura; `Esc` o el clic derecho cancelan.
- Funciona en todas las pantallas conectadas y, con el escalado de Windows, captura el píxel físico exacto.

### Selector visual

- Cuadrado de saturación y valor con barra de tono.
- Barra y campo para cada componente: rojo, verde y azul (0-255), tono (0-360), saturación, valor y alfa (0-100 %).
- El color se puede escribir directamente en HEX.

### Formatos y portapapeles

- El color actual se muestra en HEX, RGB, HSL y HSV, todos con transparencia.
- Cada formato tiene su botón «Copiar»; `Ctrl+C` copia el HEX.
- Capturar un color no toca el portapapeles.

### Historial

- Guarda los últimos 20 colores usados, sin repetidos y el más reciente primero.
- Un clic recupera un color; el menú del clic derecho lo quita, y «Vaciar historial» lo borra todo tras confirmarlo.
- Se conserva entre sesiones en `%APPDATA%\pxls\history.json`.

### Paletas

- Paletas con nombre de hasta 20 colores, que se crean, renombran y borran desde el menú «Paleta».
- Los colores se añaden desde el color actual, se reordenan arrastrándolos y se quitan con el clic derecho.
- Se exportan e importan como paleta de GIMP (`.gpl`, que también leen Inkscape, Krita y Aseprite) o como texto con un HEX por línea (`.txt`, que conserva la transparencia).
- Se conservan entre sesiones en `%APPDATA%\pxls\palettes.json`.

### Datos a salvo

- Si el fichero del historial o de las paletas está dañado, se aparta con la fecha en el nombre y se avisa; no se pierde.
- Si no se puede guardar, los datos se conservan mientras la aplicación siga abierta, se reintenta en cada cambio, el fichero anterior queda intacto y se avisa en la barra de estado.
