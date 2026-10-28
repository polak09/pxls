"""Ventana principal de pxls.

Spec: APP-002, APP-003, APP-004, APP-005, PICK-001, PICK-009, PICK-010, SEL-007, SEL-008,
    SEL-009, CLIP-001, CLIP-002, CLIP-003, CLIP-004, CLIP-005, HIST-001, HIST-005, HIST-007,
    HIST-008, HIST-009, HIST-010, PAL-006, PAL-009, PAL-011, PAL-012, PAL-013, PAL-016
"""

from collections.abc import Callable
from functools import partial
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
from pxls.core.history import History, HistorySaveError, HistoryStore, LoadedHistory
from pxls.core.palettes import LoadedPalettes, Palettes, PalettesStore
from pxls.core.picker import PickerSession
from pxls.core.storage import SaveError
from pxls.ui.color_panel import ColorPanel
from pxls.ui.history_view import HistoryView
from pxls.ui.palettes_view import PalettesView
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
HISTORY_SAVE_WARNING = (
    "No se ha podido guardar el historial en {location}; se conserva mientras pxls siga abierto."
)
PALETTES_SAVE_WARNING = (
    "No se han podido guardar las paletas en {location}; se conservan mientras pxls siga abierto."
)


def icon_path() -> Path:
    """Devuelve la ruta del icono de pxls, también dentro del ejecutable."""
    return Path(str(files("pxls.ui").joinpath("assets", "pxls.ico")))


def app_icon() -> QIcon:
    """Devuelve el icono de pxls con todas sus resoluciones."""
    return QIcon(str(icon_path()))


class MainWindow(QMainWindow):
    """Ventana principal: cuentagotas, selector, color actual, copiar, historial y paletas."""

    def __init__(
        self,
        app_version: str | None = None,
        session: PickerSession | None = None,
        clipboard: Clipboard | None = None,
        history_store: HistoryStore | None = None,
        palettes_store: PalettesStore | None = None,
    ) -> None:
        """Crea la ventana; sin almacenes, el historial y las paletas sólo viven en memoria."""
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
        self._failed_saves: set[str] = set()
        # Sólo lo capturado, lo confirmado en el HEX y lo copiado entra en el historial (HIST-001).
        self.history_store = history_store
        loaded_history = history_store.load() if history_store is not None else LoadedHistory(())
        self.history = History(loaded_history.colors)
        if history_store is not None:
            self.history.on_change(self._save_history)
        self.picker.captured.connect(self.history.add)
        self.panel.hex_entered.connect(self.history.add)
        self.history_view = HistoryView(self.history)
        self.history_view.color_chosen.connect(session.set_current)
        self.palettes_store = palettes_store
        no_palettes = LoadedPalettes(Palettes())
        loaded_palettes = palettes_store.load() if palettes_store is not None else no_palettes
        self.palettes = loaded_palettes.palettes
        if palettes_store is not None:
            self.palettes.on_change(self._save_palettes)
        self.palettes_view = PalettesView(self.palettes, lambda: session.current)
        # Recuperar un color de una paleta no lo usa: no entra en el historial (PAL-009).
        self.palettes_view.color_chosen.connect(session.set_current)
        self.palettes_view.message.connect(self.statusBar().showMessage)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.history_view, "Historial")
        self.tabs.addTab(self.palettes_view, "Paletas")
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
        warnings = [w for w in (loaded_history.warning, loaded_palettes.warning) if w is not None]
        if warnings:
            self.statusBar().showMessage(" ".join(warnings), WARNING_MS)

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
        if self.history_store is not None:
            save = partial(self.history_store.save, entries)
            self._save("history", save, HISTORY_SAVE_WARNING)

    def _save_palettes(self) -> None:
        if self.palettes_store is not None:
            save = partial(self.palettes_store.save, self.palettes)
            self._save("palettes", save, PALETTES_SAVE_WARNING)

    def _save(self, key: str, save: Callable[[], None], warning: str) -> None:
        """Guarda; si falla, avisa una vez hasta que vuelva a guardar bien (HIST-010, PAL-013)."""
        try:
            save()
        except (HistorySaveError, SaveError) as error:
            if key not in self._failed_saves:
                self.statusBar().showMessage(warning.format(location=error.location), WARNING_MS)
            self._failed_saves.add(key)
            return
        self._failed_saves.discard(key)
