# Diseño de `palettes`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Modelo | `Palettes` en `core`: un diccionario nombre → lista de colores y el nombre de la paleta activa, con avisos de cambio (`on_change`). Valida los nombres (PAL-002), los duplicados (PAL-006), el límite de 20 (PAL-010), el orden alfabético (PAL-005), la paleta activa tras borrar (PAL-004) y el nombre de una paleta importada (PAL-015). | Una clase `Palette` con su propia lista de oyentes: la vista tendría que suscribirse a cada paleta. |
| Errores de nombre | `PaletteNameError` con el texto que muestra el diálogo: «El nombre no puede estar vacío.», «El nombre no puede tener más de 40 caracteres.» y «Ya hay una paleta con ese nombre.». | Códigos de error que la interfaz traduce: dos sitios que mantener. |
| Formato de guardado | JSON en UTF-8: `{"version": 1, "active": "Web", "palettes": [{"name": "Web", "colors": ["#FF0000FF", …]}, …]}`. Si un nombre no es válido, se repite, una paleta pasa de 20 colores o los repite, o la activa no existe, el fichero cuenta como dañado. | Un fichero por paleta: más ficheros que apartar si alguno se daña. |
| Ubicación | `%APPDATA%\pxls\palettes.json`, en la misma carpeta que el historial. | — |
| Fichero de datos | `DataFile` en `adapters/data_file.py` hace lo mismo que `HistoryFile`: leer, apartar el fichero dañado con fecha, no escribir encima de uno ilegible y escribir con un temporal y `os.replace`; `PalettesFile` sólo pone el formato y sus textos. Que el historial también lo use es un `refactor` aparte (T-086), porque un commit `behavior` de las paletas no puede tocar los módulos del historial sin cambiar su spec. | Dejar para siempre dos copias del mismo cuidado con los datos del usuario. |
| Fallo al guardar | `SaveError(location)` en `core/storage.py`, del que hereda `PalettesSaveError` (y `HistorySaveError` tras T-086). La ventana guarda historial y paletas con la misma función, que avisa una vez hasta el siguiente guardado bueno (HIST-010, PAL-013). | Una función por almacén: la regla de repetición quedaría duplicada. |
| Formatos de intercambio | `core/palette_formats.py`, sin disco: `to_gpl`, `to_txt`, `from_gpl` y `from_txt`, que lanzan `PaletteFormatError`. `.gpl`: cabecera `GIMP Palette`, `Name:`, `Columns: 10`, `#` y una línea `R G B<tab>#RRGGBB` por color; al leer, se admiten comentarios, líneas vacías y `Columns:`. `.txt`: un HEX por línea; al leer, se ignoran las líneas vacías y cualquier línea que no sea un HEX válido invalida el fichero. | Ignorar las líneas que no se entienden: un fichero equivocado acabaría como una paleta vacía sin avisar. |
| Leer y escribir esos ficheros | `adapters/palette_files.py`: lee en UTF-8 (también con BOM) y escribe con `DataFile`, así que un fallo deja el fichero como estaba (PAL-014). | — |
| Vista | `PalettesView` en `ui/palettes_view.py`: lista desplegable, botón «Paleta» con su menú, rejilla de 2 × 10 muestras y «Añadir color actual». Avisa a la ventana con la señal `message(texto, ms)`, que acaba en la barra de estado. | Que la vista escriba en la barra de estado: tendría que conocer la ventana. |
| Muestras | `Swatch` en `ui/swatch.py`, igual que la del historial; `PaletteSwatch` añade el arrastre. El historial pasa a usarla en T-086. | Que las paletas importen la muestra de `ui/history_view.py`: dependería de la pestaña del historial. |
| Arrastrar y soltar | Sin `QDrag`: la muestra pulsada recibe el movimiento y la suelta (Qt le da el ratón mientras el botón está pulsado), pasa a modo arrastre tras la distancia de arrastre del sistema y, al soltar, emite la posición; la vista busca la muestra que hay debajo. Soltar sobre una muestra vacía lleva el color al final. | `QDrag`: su bucle modal no se puede probar sin un ratón real. |
| Diálogos | `NameDialog` (título «Nueva paleta» o «Renombrar paleta», etiqueta «Nombre:», campo de 40 caracteres como máximo, explicación en rojo y «Aceptar» desactivado mientras el nombre no es válido). Borrar pregunta «¿Borrar la paleta «Web»? No se puede deshacer.» con «No» por defecto. Exportar e importar usan los diálogos de ficheros del sistema, con los filtros «Paleta de GIMP (*.gpl)» y «Texto con un HEX por línea (*.txt)»; si el nombre elegido no tiene extensión, se añade la del filtro. Las cuatro preguntas son funciones inyectables para los tests. | — |
| Avisos | Los de la vista duran 4 s; el de fallo al guardar, 10 s. Si al arrancar hay avisos del historial y de las paletas, la barra de estado muestra los dos seguidos. | — |
| Tamaño | Con la pestaña «Paletas», el contenido ocupa 729 de los 759 px de la ventana de 420 × 780 (boceto en Windows). | — |

## Módulos

| Módulo | Contenido | Requisitos |
|---|---|---|
| `pxls/core/palettes.py` | `Palettes`, `PaletteNameError`, `PalettesStore`, `LoadedPalettes`, `PalettesSaveError`, `PaletteFormatError` (para el JSON y para los formatos de intercambio), `dump_palettes` y `load_palettes`. | PAL-001 a PAL-008, PAL-010 a PAL-013, PAL-015 |
| `pxls/core/palette_formats.py` | `to_gpl`, `to_txt`, `from_gpl` y `from_txt`. | PAL-014, PAL-015 |
| `pxls/core/storage.py` | `SaveError`. | PAL-013 |
| `pxls/adapters/data_file.py` | `DataFile` y la carpeta de datos de `pxls`. | PAL-011, PAL-012, PAL-013 |
| `pxls/adapters/palettes_file.py` | `PalettesFile` y `default_palettes_path()`. | PAL-011, PAL-012, PAL-013 |
| `pxls/adapters/palette_files.py` | `export_palette` e `import_palette_file`. | PAL-014, PAL-015 |
| `pxls/ui/swatch.py` | `Swatch`. | PAL-009, PAL-016 |
| `pxls/ui/palettes_view.py` | `PalettesView`, `PaletteSwatch`, `NameDialog` y las preguntas. | PAL-001 a PAL-010, PAL-014 a PAL-016 |
| `pxls/ui/main_window.py` | Pestaña «Paletas», carga, guardado y avisos. | PAL-009, PAL-011, PAL-012, PAL-013, PAL-016 |
| `pxls/ui/app.py` | `main()` usa el fichero de las paletas; la prueba de humo no lo toca. | PAL-011 |

## Tests

- Núcleo: reglas de `Palettes`, JSON y formatos de intercambio, sin Qt ni disco.
- Adaptadores: `PalettesFile`, exportar e importar sobre `tmp_path`.
- Vista y ventana: almacenes falsos o ficheros en `tmp_path` y preguntas inyectadas; el arrastre se prueba enviando los eventos del ratón a la muestra.
