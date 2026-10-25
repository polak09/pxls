# Diseño de `clipboard`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Puerto | `Clipboard` en `core` con `set_text(text)`, que lanza `ClipboardError` si no se puede escribir. | Llamar a Qt desde la interfaz: no se podría probar CLIP-005 sin bloquear el portapapeles de verdad. |
| Adaptador | `QtClipboard` en `adapters`, sobre `QGuiApplication.clipboard()`. Como `QClipboard.setText` no informa de errores, el adaptador **relee** el portapapeles y lanza `ClipboardError` si no contiene lo escrito. | La API de Windows (`OpenClipboard`/`SetClipboardData`) con `ctypes`: más código para el mismo resultado; Qt ya gestiona los formatos de texto de Windows. |
| Formatos | El registro de formatos (`HEX`, `RGB`, `HSL`, `HSV` → función que escribe el texto) pasa de `ui/color_panel.py` a `core/formatting.py`, para que panel y portapapeles usen exactamente el mismo texto (CLIP-001). | Duplicar el registro: dos fuentes que podrían divergir. |
| Atajo | `QShortcut(QKeySequence.Copy)` en la ventana. Un `QLineEdit` con el foco reclama `Ctrl+C` para sí antes que los atajos de la ventana (*shortcut override*), así que copiar texto seleccionado sigue funcionando (CLIP-002). | Capturar `Ctrl+C` a mano en `keyPressEvent`: habría que replicar la lógica de foco de Qt. |
| Confirmación y errores | `QStatusBar.showMessage(texto, 2000)`. | Un aviso flotante: más código y tapa la ventana. |

## Módulos

| Módulo | Contenido | Requisitos |
|---|---|---|
| `pxls/core/clipboard.py` | Puerto `Clipboard`, `ClipboardError` y `copy_color(clipboard, color, formato)`. | CLIP-001, CLIP-005 |
| `pxls/core/formatting.py` | Registro `FORMATS`. | CLIP-001 |
| `pxls/adapters/qt_clipboard.py` | `QtClipboard`. | CLIP-001, CLIP-005 |
| `pxls/ui/color_panel.py` | Botón «Copiar» en cada formato. | CLIP-001 |
| `pxls/ui/main_window.py` | Atajo `Ctrl+C`, confirmación y aviso de error. | CLIP-002 a CLIP-005 |

## Tests

- Núcleo y ventana, con un portapapeles falso que registra lo escrito o falla a voluntad.
- Adaptador real, en un subproceso con la plataforma Qt de Windows: escribe con `QtClipboard` y lee con la API de Windows (`GetClipboardData`) para comprobar que el texto llega al portapapeles del sistema. **Guarda el texto que hubiera en el portapapeles y lo restaura al terminar**, porque la suite se ejecuta en el equipo de desarrollo.
