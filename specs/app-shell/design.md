# Diseño de `app-shell`

Documento informativo (constitución V.7). Describe *cómo* se implementa [spec.md](spec.md); si algo de aquí contradice la spec, manda la spec.

## Decisiones

| Decisión | Elección | Alternativas descartadas |
|---|---|---|
| Interfaz | **PySide6-Essentials** (Qt 6), acotado a `>=6.12,<7`. Trae QtCore, QtGui y QtWidgets, y las traducciones oficiales de Qt (`qtbase_es.qm`). | El paquete `PySide6` completo: añade módulos (QtWebEngine, Qt3D…) que no se usan y multiplican el tamaño del `.exe`. Tkinter: descartado en la constitución (VIII). |
| Empaquetado | **PyInstaller** (`>=6.22,<7`, dependencia de desarrollo) en modo un único fichero, sin consola. | Nuitka: compila a C y arranca más rápido, pero tarda varios minutos por build y complica la verificación de cada commit. cx_Freeze: no genera un único fichero. |
| Tests de interfaz | **pytest-qt** (`>=4.5,<5`), con la plataforma Qt `offscreen` para no abrir ventanas durante los tests. | Tests manuales: no se pueden repetir en cada commit. |
| Versión | `importlib.metadata.version("pxls")`: lee la de `pyproject.toml`. PyInstaller copia los metadatos del paquete en el ejecutable. | Duplicar el número en el código: dos fuentes que acabarían divergiendo. |

## Módulos

| Módulo | Responsabilidad | Requisitos |
|---|---|---|
| `pxls/ui/main_window.py` | `MainWindow`: título, tamaños, icono y barra de estado con la versión. | APP-002 a APP-005 |
| `pxls/ui/app.py` | `create_app` (aplicación Qt, traducciones al español, icono), `run` (bucle de eventos), `smoke_test` y `main` (punto de entrada del comando `pxls` y del `.exe`). | APP-001, APP-004, APP-006, APP-007, APP-009 |
| `pxls/ui/assets/` | `pxls.svg` (fuente del icono) y `pxls.ico` (16, 24, 32, 48, 64, 128 y 256 px, en PNG). El `.ico` se generó una vez desde el `.svg` con QtSvg; si cambia el `.svg`, hay que regenerarlo. El `.svg` no usa `clip-path` porque QtSvg sólo implementa SVG Tiny. | APP-004 |
| `pxls/__main__.py` | Permite `python -m pxls`. Sin definiciones. | — |
| `pxls.spec` (raíz) | Configuración de PyInstaller: `src/pxls/__main__.py` como entrada, icono, recursos y metadatos. | APP-008 |

Todo vive en la capa `ui`: esta capacidad no tiene dominio ni adaptadores.

## Prueba de humo (APP-009)

`pxls --smoke-test` crea la aplicación (con las traducciones, que tienen que cargarse) y la ventana principal **sin mostrarla**, procesa los eventos pendientes y termina con 0. Cualquier excepción durante el arranque termina con 1. La plataforma Qt `offscreen` no hace falta: crear una ventana sin mostrarla no pinta nada en pantalla.

## Tests del ejecutable (APP-001, APP-004, APP-008, APP-009)

- Un fixture de sesión genera el `.exe` **una sola vez por ejecución de la suite**, con PyInstaller y en una carpeta temporal.
- Sobre ese `.exe` se comprueba: que es un único fichero; que la prueba de humo pasa también copiado fuera del proyecto y con un `PATH` sin Python; que el icono del ejecutable es el de `pxls`; y que el arranque (medido con la prueba de humo, que hace el mismo trabajo que un arranque normal salvo pintar la ventana) dura menos de 5 s.
- Como esos tests generan y ejecutan el `.exe` en cada verificación completa, **el empaquetado forma parte de la verificación completa a través de la suite de tests**, sin configurar `[tool.spec-anchor]`. Generarlo además desde la puerta ANCH-033 lo haría dos veces por commit.
- Coste: el build de PyInstaller añade alrededor de un minuto a cada verificación completa.

## Idioma (APP-006)

`create_app` instala un `QTranslator` con `qtbase_es` desde la carpeta de traducciones de Qt; si no se puede cargar, el arranque falla (y con él la prueba de humo), para detectar un ejecutable empaquetado sin traducciones.
