"""Arranque, idioma, bucle de eventos y prueba de humo de pxls.

Spec: APP-001, APP-004, APP-006, APP-007, APP-009, HIST-007
"""

import sys
from collections.abc import Sequence

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from pxls.adapters.history_file import HistoryFile, default_history_path
from pxls.ui.main_window import TITLE, MainWindow, app_icon

SMOKE_TEST = "--smoke-test"


def create_app(argv: Sequence[str]) -> QApplication:
    """Crea (o reutiliza) la aplicación Qt con su icono y las traducciones al español."""
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(list(argv))
    app.setApplicationName(TITLE)
    app.setWindowIcon(app_icon())
    translator = QTranslator(app)
    folder = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    spanish = QLocale(QLocale.Language.Spanish, QLocale.Country.Spain)
    if not translator.load(spanish, "qtbase", "_", folder):
        raise RuntimeError(f"no se pueden cargar las traducciones de Qt al español de {folder}")
    app.installTranslator(translator)
    return app


def run(app: QApplication, window: MainWindow) -> int:
    """Muestra la ventana y ejecuta la aplicación hasta que se cierra (APP-007)."""
    window.show()
    return app.exec()


def smoke_test(argv: Sequence[str]) -> int:
    """Arranca la aplicación sin mostrar la ventana; devuelve 0 si lo consigue (APP-009).

    No usa el historial guardado: la prueba de humo no lee ni escribe datos del usuario.
    """
    try:
        app = create_app(argv)
        window = MainWindow()
        app.processEvents()
        window.deleteLater()
    except Exception as error:
        # En el ejecutable sin consola sys.stderr es None y print no escribe nada.
        print(f"pxls: la prueba de humo ha fallado: {error}", file=sys.stderr)
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada del comando ``pxls`` y del ejecutable."""
    arguments = list(sys.argv if argv is None else argv)
    if SMOKE_TEST in arguments:
        return smoke_test(arguments)
    application = create_app(arguments)
    return run(application, MainWindow(history_store=HistoryFile(default_history_path())))
