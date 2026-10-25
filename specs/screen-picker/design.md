# Diseño de `screen-picker`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Captura | **API de Windows (GDI) con `ctypes`**: una copia `BitBlt` de todo el escritorio virtual en píxeles físicos al activar el cuentagotas. Sin dependencias nuevas. | `QScreen.grabWindow`: devuelve cada pantalla por separado y en coordenadas lógicas; con escalado no permite direccionar cada píxel físico (PICK-008). `mss` o `Pillow`: dependencias que no aportan nada sobre GDI. |
| Coordenadas | **Píxeles físicos del escritorio virtual** en todo el núcleo. La posición del cursor se lee y se cambia con `GetCursorPos`/`SetCursorPos`, con el hilo marcado como *per-monitor DPI aware v2*. | Coordenadas lógicas de Qt: enteras, así que al 150 % no llegan a todos los píxeles físicos ni permiten mover el cursor de uno en uno (PICK-006). |
| Pantalla congelada | Ventanas superpuestas, una por pantalla, sin marco y siempre encima, que pintan su trozo de la captura 1:1 en píxeles físicos y reciben el ratón y el teclado. | Una sola ventana sobre todo el escritorio: Qt no la escala bien cuando las pantallas tienen escalados distintos. |

## Capas

| Capa | Módulo | Contenido | Requisitos |
|---|---|---|---|
| `core` | `pxls/core/screen.py` | Puertos `Screenshot` (píxeles congelados del escritorio virtual), `ScreenGrabber` y `Pointer` (posición física del cursor); `Point` y `Rect` en píxeles físicos. | PICK-002, PICK-007, PICK-008 |
| `core` | `pxls/core/picker.py` | `PickerSession`: estado del modo cuentagotas, color actual, capturar, cancelar y mover con las flechas. Sin Qt. | PICK-004, PICK-005, PICK-006, PICK-010 |
| `core` | `pxls/core/magnifier.py` | Celdas de la lupa (11 × 11 colores alrededor de un punto; `None` fuera del escritorio) y posición de la lupa para que quepa en la pantalla. | PICK-003 |
| `adapters` | `pxls/adapters/windows_screen.py` | `WindowsScreenGrabber` (GDI) y `WindowsPointer` (cursor), con el hilo *per-monitor DPI aware v2* en cada llamada. | PICK-002, PICK-007, PICK-008 |
| `ui` | `pxls/ui/picker_overlay.py` | Ventanas superpuestas: pintan la captura y la lupa y traducen ratón y teclado a la `PickerSession`. | PICK-001, PICK-003 a PICK-006 |
| `ui` | `pxls/ui/color_panel.py` | Muestra del color actual y sus cuatro formatos. | PICK-009, PICK-010 |
| `ui` | `pxls/ui/main_window.py` | Botón «Capturar color», atajo `Ctrl+Mayús+C` y panel. | PICK-001, PICK-009 |

La capa `ui` crea el adaptador real y se lo pasa a la sesión; los tests le pasan *fakes* (constitución VII.4).

## Geometría de cada pantalla

Qt en Windows conserva el origen de cada pantalla en píxeles nativos y escala sólo el tamaño. El rectángulo físico de una pantalla es, por tanto, `origen lógico` + `tamaño lógico × devicePixelRatio`. Comprobado en el equipo de desarrollo (dos pantallas de 1920 × 1080 al 100 %, la segunda a la derecha): Qt y `EnumDisplayMonitors` dan los mismos rectángulos.

## Tests

- **Núcleo** (`core`): sesión, lupa y geometría con capturas falsas, incluidos un escritorio con origen negativo (pantalla a la izquierda, PICK-007) y una captura con píxeles alternos blancos y negros (PICK-008).
- **Adaptador real**: un subproceso abre una ventana de color conocido en cada pantalla, captura con `WindowsScreenGrabber` y comprueba los píxeles exactos, también un patrón de píxeles alternos. Va en un subproceso porque el resto de la suite usa la plataforma Qt `offscreen`, y la aplicación Qt es única por proceso. Durante la verificación completa se verán aparecer y desaparecer esas ventanas un instante.
- **Interfaz**: ventanas superpuestas con `pytest-qt` en `offscreen`, con capturas y cursores falsos.

## Límites conocidos

- En el equipo de desarrollo todas las pantallas están al 100 % y ninguna en coordenadas negativas. PICK-008 (escalado) y la parte de PICK-007 con pantallas a la izquierda se comprueban con datos simulados; con hardware real sólo se comprueban el 100 % y una pantalla a la derecha.
- La captura es de todo el escritorio virtual: con pantallas muy grandes (p. ej. 3 × 4K) ocupa unos 100 MB mientras dura el modo cuentagotas.
