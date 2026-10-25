"""Ventana principal de pxls.

Spec: APP-002, APP-003, APP-004, APP-005, PICK-001, PICK-009, PICK-010, SEL-007, SEL-008,
    SEL-009, CLIP-001, CLIP-002, CLIP-003, CLIP-004, CLIP-005
"""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pxls.adapters.qt_clipboard import QtClipboard
from pxls.adapters.windows_screen import WindowsPointer, WindowsScreenGrabber
from pxls.core.clipboard import Clipboard, ClipboardError, copy_color
from pxls.core.picker import PickerSession
from pxls.ui.color_panel import ColorPanel
from pxls.ui.picker_overlay import PickerController
from pxls.ui.selector import SelectorWidget

TITLE = "pxls"
INITIAL_SIZE = QSize(420, 640)
MINIMUM_SIZE = QSize(360, 480)
PICK_SHORTCUT = "Ctrl+Shift+C"
SHORTCUT_FORMAT = "HEX"
CONFIRMATION_MS = 2000
ERROR_MS = 4000


def icon_path() -> Path:
    """Devuelve la ruta del icono de pxls, también dentro del ejecutable."""
    return Path(str(files("pxls.ui").joinpath("assets", "pxls.ico")))


def app_icon() -> QIcon:
    """Devuelve el icono de pxls con todas sus resoluciones."""
    return QIcon(str(icon_path()))


class MainWindow(QMainWindow):
    """Ventana principal: cuentagotas, selector, color actual, copiar y versión."""

    def __init__(
        self,
        app_version: str | None = None,
        session: PickerSession | None = None,
        clipboard: Clipboard | None = None,
    ) -> None:
        """Crea la ventana; los argumentos sustituyen a los reales en los tests."""
        super().__init__()
        self.setWindowTitle(TITLE)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(MINIMUM_SIZE)
        self.resize(INITIAL_SIZE)
        if session is None:
            session = PickerSession(WindowsScreenGrabber(), WindowsPointer())
        self.clipboard: Clipboard = clipboard if clipboard is not None else QtClipboard()
        # El cuentagotas no toca el portapapeles al capturar: sólo se copia a petición (CLIP-004).
        self.picker = PickerController(session)
        self.pick_button = QPushButton("Capturar color")
        self.pick_button.clicked.connect(self.picker.start)
        QShortcut(QKeySequence(PICK_SHORTCUT), self, self.picker.start)
        # Un campo de texto con el foco se queda Ctrl+C para copiar su selección (CLIP-002).
        QShortcut(QKeySequence.StandardKey.Copy, self, lambda: self.copy(SHORTCUT_FORMAT))
        self.selector = SelectorWidget(session)
        self.panel = ColorPanel()
        self.panel.show_color(session.current)
        session.on_change(self.panel.show_color)
        self.panel.hex_entered.connect(session.set_current)
        self.panel.copy_requested.connect(self.copy)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self.pick_button)
        layout.addWidget(self.selector)
        layout.addWidget(self.panel)
        layout.addStretch()
        # Más baja que su contenido, la ventana se desplaza en vertical (APP-003).
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(content)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(self.scroll_area)
        shown_version = app_version if app_version is not None else version("pxls")
        self.statusBar().addPermanentWidget(QLabel(f"v{shown_version}"))

    def copy(self, format_name: str) -> None:
        """Copia el color actual en un formato y lo confirma en la barra de estado."""
        try:
            text = copy_color(self.clipboard, self.picker.session.current, format_name)
        except ClipboardError as error:
            self.statusBar().showMessage(f"No se ha podido copiar: {error}", ERROR_MS)
            return
        self.statusBar().showMessage(f"Copiado: {text}", CONFIRMATION_MS)
