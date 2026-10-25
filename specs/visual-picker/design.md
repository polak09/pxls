# Diseño de `visual-picker`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Estado del selector | `SelectorState` en `core`: guarda tono, saturación y valor como números reales y el alfa, y calcula el color. | Derivar siempre el HSV del color RGB: pierde el tono y la saturación en negros y grises (SEL-004). |
| Color actual | Sigue siendo el de `PickerSession` (`specs/screen-picker`). El selector escucha sus cambios y los provoca con `set_current`; panel, cuentagotas y selector quedan sincronizados (SEL-008). | Un segundo modelo de color actual: dos fuentes de verdad. |
| Cuadrado SV, barra de tono y barra de alfa | Widgets propios pintados con degradados de Qt. | Imágenes precalculadas: hay que regenerarlas con cada tono. |
| Barras de rojo, verde, azul, tono, saturación y valor | `QSlider` con un `QSpinBox` al lado. El alfa usa una barra propia con fondo de cuadros y también un `QSpinBox`. | Un único tipo de barra pintada para todo: más código sin beneficio para los componentes opacos. |
| Bucles de señales | Al reflejar un cambio en un widget se bloquean sus señales (`QSignalBlocker`), para que no vuelva a emitir el cambio. | Comparar valores antes de emitir: frágil con los redondeos. |
| HEX editable | El valor HEX del panel pasa a ser un `QLineEdit`; un error se muestra debajo en rojo, con el mensaje de `ColorError`. | Un campo HEX aparte: duplicaría el que ya muestra el panel. |
| Tamaño | La parte central de la ventana va dentro de un `QScrollArea` sin marco; con 420 × 640 no aparece la barra de desplazamiento (APP-003, SEL-009). | Fijar el mínimo al alto del contenido: Bartosz eligió mantener 360 × 480 con desplazamiento. |

## Reglas de `SelectorState` (SEL-004)

Cuando el color llega de fuera (cuentagotas, HEX, campos RGB):

- si es el mismo color que ya representa el estado, no cambia nada (conserva tono y saturación);
- si su valor es 0 (negro), conserva tono y saturación y sólo cambia el valor;
- si su saturación es 0 (gris), conserva el tono;
- en otro caso, toma el tono, la saturación y el valor del color.

## Módulos

| Módulo | Contenido | Requisitos |
|---|---|---|
| `pxls/core/selector.py` | `SelectorState` y las conversiones de los campos (alfa en %, componentes con límites). | SEL-001, SEL-002, SEL-004, SEL-005, SEL-006 |
| `pxls/ui/selector.py` | `SvSquare`, `HueBar`, `AlphaBar`, `ComponentRows` y `SelectorWidget`, que los reúne y los conecta con la `PickerSession`. | SEL-001 a SEL-006, SEL-008 |
| `pxls/ui/color_panel.py` | HEX editable. | SEL-007 |
| `pxls/ui/main_window.py` | Selector entre el botón y el panel, `QScrollArea` y nuevo tamaño inicial. | SEL-008, SEL-009, APP-003 |

## Medidas

Comprobado con un boceto en la plataforma real: con el cuadrado a 220 × 180 px, siete filas de barra y campo, una muestra de 48 px y las cuatro filas de formatos, el contenido necesita 581 px de alto.
