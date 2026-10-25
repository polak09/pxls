"""Ventana principal de pxls.

Spec: APP-002, APP-003, APP-004, APP-005, PICK-001, PICK-009, PICK-010, SEL-007, SEL-008,
    SEL-009, CLIP-001, CLIP-002, CLIP-003, CLIP-004, CLIP-005, HIST-001, HIST-005, HIST-007,
    HIST-008, HIST-009, HIST-010
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pxls.adapters.qt_clipboard import QtClipboard
from pxls.adapters.windows_screen import WindowsPointer, WindowsScreenGrabber
from pxls.core.clipboard import Clipboard, ClipboardError, copy_color
from pxls.core.color import Color
from pxls.core.history import History, HistorySaveError, HistoryStore
from pxls.core.picker import PickerSession
from pxls.ui.color_panel import ColorPanel
from pxls.ui.history_view import HistoryView
from pxls.ui.picker_overlay import PickerController
from pxls.ui.selector import SelectorWidget

TITLE = "pxls"
INITIAL_SIZE = QSize(420, 780)
MINIMUM_SIZE = QSize(360, 480)
PICK_SHORTCUT = "Ctrl+Shift+C"
SHORTCUT_FORMAT = "HEX"
CONFIRMATION_MS = 2000
ERROR_MS = 4000
WARNING_MS = 10000


def icon_path() -> Path:
    """Devuelve la ruta del icono de pxls, también dentro del ejecutable."""
    return Path(str(files("pxls.ui").joinpath("assets", "pxls.ico")))


def app_icon() -> QIcon:
    """Devuelve el icono de pxls con todas sus resoluciones."""
    return QIcon(str(icon_path()))


class MainWindow(QMainWindow):
    """Ventana principal: cuentagotas, selector, color actual, copiar, historial y versión."""

    def __init__(
        self,
        app_version: str | None = None,
        session: PickerSession | None = None,
        clipboard: Clipboard | None = None,
        history_store: HistoryStore | None = None,
    ) -> None:
        """Crea la ventana; sin ``history_store``, el historial sólo vive en memoria."""
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
        self.panel = ColorPanel()
        self.selector = SelectorWidget(session, self.panel.swatch)
        self.panel.show_color(session.current)
        session.on_change(self.panel.show_color)
        self.panel.hex_entered.connect(session.set_current)
        self.panel.copy_requested.connect(self.copy)
        # Sólo lo capturado, lo confirmado en el HEX y lo copiado entra en el historial (HIST-001).
        self.history_store = history_store
        loaded = history_store.load() if history_store is not None else None
        self.history = History(loaded.colors if loaded is not None else ())
        self._save_failed = False
        if history_store is not None:
            self.history.on_change(self._save_history)
        self.picker.captured.connect(self.history.add)
        self.panel.hex_entered.connect(self.history.add)
        self.history_view = HistoryView(self.history)
        self.history_view.color_chosen.connect(session.set_current)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.history_view, "Historial")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self.pick_button)
        layout.addWidget(self.selector)
        layout.addWidget(self.panel)
        layout.addWidget(self.tabs)
        layout.addStretch()
        # Más baja que su contenido, la ventana se desplaza en vertical (APP-003).
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidget(content)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(self.scroll_area)
        shown_version = app_version if app_version is not None else version("pxls")
        self.statusBar().addPermanentWidget(QLabel(f"v{shown_version}"))
        if loaded is not None and loaded.warning is not None:
            self.statusBar().showMessage(loaded.warning, WARNING_MS)

    def copy(self, format_name: str) -> None:
        """Copia el color actual en un formato y lo confirma en la barra de estado."""
        try:
            text = copy_color(self.clipboard, self.picker.session.current, format_name)
        except ClipboardError as error:
            self.statusBar().showMessage(f"No se ha podido copiar: {error}", ERROR_MS)
            return
        self.statusBar().showMessage(f"Copiado: {text}", CONFIRMATION_MS)
        # Después de la confirmación: si no se puede guardar, el aviso la sustituye (HIST-010).
        self.history.add(self.picker.session.current)

    def _save_history(self, entries: tuple[Color, ...]) -> None:
        """Guarda el historial; si falla, avisa una vez hasta que se vuelva a guardar (HIST-010)."""
        if self.history_store is None:
            return
        try:
            self.history_store.save(entries)
        except HistorySaveError as error:
            if not self._save_failed:
                warning = (
                    f"No se ha podido guardar el historial en {error.location}; "
                    "se conserva mientras pxls siga abierto."
                )
                self.statusBar().showMessage(warning, WARNING_MS)
            self._save_failed = True
            return
        self._save_failed = False
