# Diseño de `history`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Modelo | `History` en `core`: una lista de colores, el más reciente primero, con `add`, `remove`, `clear` y avisos de cambio (`on_change`). Las reglas de orden, límite y duplicados (HIST-002 a HIST-004) viven sólo aquí. | Guardar el historial en la vista: las reglas no se podrían probar sin Qt. |
| Qué cuenta como usar un color | Lo decide la ventana, que es la única que conoce el origen de cada cambio: añade al historial lo capturado (`PickerController.captured`), lo confirmado en el HEX (`ColorPanel.hex_entered`) y lo copiado con éxito. No escucha `PickerSession.on_change`, que también avisa de cada paso del selector (HIST-001). | Escuchar `on_change` y filtrar: no sabe de dónde viene el cambio. |
| Captura sin color | `PickerSession.capture()` devuelve `None` si el cursor no estaba sobre ninguna pantalla, y el controlador sólo emite `captured` con un color real. | Comparar el color antes y después: capturar el mismo color que el actual también es usarlo. |
| Puerto de almacenamiento | `HistoryStore` en `core`, con `load()` → `LoadedHistory(colors, warning)` y `save(colors)`. La ventana sin almacén (tests, prueba de humo) guarda el historial sólo en memoria. | Que la ventana lea y escriba ficheros: no se podría probar sin disco. |
| Formato | JSON en UTF-8: `{"version": 1, "colors": ["#RRGGBBAA", …]}`, el más reciente primero. La conversión entre texto y colores es pura y está en `core` (`dump_history`, `load_history`). | Una línea por color: no deja sitio para cambiar el formato. |
| Ubicación | `%APPDATA%\pxls\history.json`; sin `APPDATA`, `~\AppData\Roaming\pxls\history.json`. Los tests pasan una ruta temporal. | Junto al ejecutable: puede estar en una carpeta sin permiso de escritura. |
| Cuándo se guarda | En cada cambio del historial, escribiendo un fichero temporal en la misma carpeta y sustituyendo el anterior con `os.replace`. | Sólo al cerrar: un cierre inesperado perdería la sesión entera. |
| Fichero dañado (HIST-008) | Si el JSON no es válido, no tiene la estructura esperada o algún color no es un HEX válido, se renombra a `history-dañado-AAAAMMDD-HHMMSS.json` en la misma carpeta, se arranca vacío y la barra de estado avisa durante 10 s con la ruta de la copia. Si ni siquiera se puede leer o renombrar, el almacén deja de escribir en esta sesión para no sobrescribirlo, y el aviso lo dice. | Borrarlo: se perdería; copiarlo con un nombre fijo: un segundo fallo sobrescribiría la primera copia. |
| Fallo al guardar (HIST-010) | `HistoryFile.save` convierte cualquier `OSError` en `HistorySaveError(ruta)`, borra el fichero temporal y deja el anterior intacto. La ventana guarda a través de `_save_history`, que avisa sólo cuando pasa de guardar bien a fallar, y vuelve a intentarlo en cada cambio. Al copiar, el historial se actualiza después de mostrar «Copiado: …», para que el aviso la sustituya. Los avisos no incluyen el mensaje del sistema, que puede venir en inglés (APP-006). | Avisar en cada fallo: taparía cada confirmación de copia mientras dure el problema. |
| Vista | Pestaña «Historial» de un `QTabWidget` debajo del panel, con una rejilla de 2 × 10 muestras de 24 px (las vacías, sólo con borde) y el botón «Vaciar historial». Cada muestra pinta cuadros debajo del color, como la barra de alfa, para que se vea la transparencia. | Una lista con el texto de cada color: ocupa mucho más. |
| Recuperar, quitar y vaciar | Clic en una muestra → `session.set_current` sin tocar el historial (HIST-005); clic derecho → menú con «Quitar del historial»; «Vaciar historial» pregunta con un `QMessageBox` («¿Vaciar el historial?», botones Sí y No). La pregunta es una función inyectable para poder probarla sin diálogo. | Vaciar sin preguntar: no se puede deshacer. |
| Tamaño | La ventana pasa a 420 × 780 (APP-003); el contenido con la pestaña necesitaba 751 px, y 697 px desde que la muestra del color va junto a la barra de tono (PICK-009). | — |

## Módulos

| Módulo | Contenido | Requisitos |
|---|---|---|
| `pxls/core/history.py` | `History`, `HistoryStore`, `LoadedHistory`, `HistoryFormatError`, `HistorySaveError`, `dump_history` y `load_history`. | HIST-002, HIST-003, HIST-004, HIST-006, HIST-007, HIST-008, HIST-010 |
| `pxls/core/picker.py` | `capture()` devuelve `None` si no hay color. | HIST-001 |
| `pxls/adapters/history_file.py` | `HistoryFile(path)` y `default_history_path()`: lectura, copia del fichero dañado, escritura atómica y `HistorySaveError` si no se puede escribir. | HIST-007, HIST-008, HIST-010 |
| `pxls/ui/picker_overlay.py` | Señal `PickerController.captured`. | HIST-001 |
| `pxls/ui/history_view.py` | `HistoryView`: rejilla, pista con el HEX, menú del clic derecho y «Vaciar historial». | HIST-005, HIST-006, HIST-009 |
| `pxls/ui/main_window.py` | Qué entra en el historial, pestaña, carga y guardado, avisos y tamaño 420 × 780. | HIST-001, HIST-005, HIST-007, HIST-008, HIST-009, HIST-010, APP-003 |
| `pxls/ui/app.py` | `main()` usa el fichero del historial; la prueba de humo no lo toca. | HIST-007 |

## Tests

- Núcleo: reglas de `History` y conversión de JSON, sin Qt ni disco.
- Adaptador: `HistoryFile` sobre `tmp_path` (guardar y releer, fichero que no existe, dañado, ilegible).
- Ventana: un almacén falso o `HistoryFile` sobre `tmp_path`; nunca el historial real del equipo. La persistencia entre sesiones se prueba creando una segunda ventana con el mismo fichero.

## Notas

- Cuando `pxls` se ejecuta desde un terminal integrado en una aplicación empaquetada como MSIX (por ejemplo, la app de escritorio de Claude), Windows puede redirigir `%APPDATA%` a una carpeta virtual de esa aplicación. Para comprobar a mano dónde queda `history.json`, conviene arrancar `pxls` desde un terminal normal.
