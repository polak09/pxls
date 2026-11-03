"""Pestaña «Historial»: rejilla de muestras de los colores usados, quitar y vaciar.

Spec: HIST-002, HIST-005, HIST-006, HIST-009, APP-006
"""

from collections.abc import Callable
from functools import partial

from PySide6.QtCore import QPoint, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pxls.core.color import Color
from pxls.core.history import LIMIT, History

# COLUMNS y SWATCH_SIZE se siguen ofreciendo desde aquí: los tests del historial los importan.
from pxls.ui.swatch import COLUMNS as COLUMNS
from pxls.ui.swatch import GAP, Swatch
from pxls.ui.swatch import SWATCH_SIZE as SWATCH_SIZE


def ask_to_clear(parent: QWidget) -> bool:
    """Pregunta si se vacía el historial; «No» es la respuesta por defecto (HIST-006)."""
    buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    box = QMessageBox(
        QMessageBox.Icon.Question,
        "Vaciar historial",
        "¿Vaciar el historial? No se puede deshacer.",
        buttons,
        parent,
    )
    box.setDefaultButton(QMessageBox.StandardButton.No)
    return box.exec() == QMessageBox.StandardButton.Yes


class HistoryView(QWidget):
    """Rejilla de dos filas de diez muestras y botón «Vaciar historial» (HIST-009)."""

    color_chosen = Signal(Color)

    def __init__(
        self,
        history: History,
        confirm: Callable[[QWidget], bool] = ask_to_clear,
        parent: QWidget | None = None,
    ) -> None:
        """Muestra ``history`` y lo sigue; ``confirm`` pregunta antes de vaciarlo."""
        super().__init__(parent)
        self.history = history
        self.confirm = confirm
        grid = QGridLayout()
        grid.setSpacing(GAP)
        self.swatches: list[Swatch] = []
        for index in range(LIMIT):
            swatch = Swatch(self)
            swatch.clicked.connect(partial(self._choose, swatch))
            swatch.customContextMenuRequested.connect(partial(self._open_menu, swatch))
            grid.addWidget(swatch, index // COLUMNS, index % COLUMNS)
            self.swatches.append(swatch)
        self.clear_button = QPushButton("Vaciar historial", self)
        self.clear_button.clicked.connect(self._clear)
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(self.clear_button)
        layout = QVBoxLayout(self)
        layout.addLayout(grid)
        layout.addLayout(footer)
        history.on_change(self.show_entries)
        self.show_entries(history.entries)

    def show_entries(self, entries: tuple[Color, ...]) -> None:
        """Pinta las entradas en orden, la más reciente primero (HIST-002)."""
        for index, swatch in enumerate(self.swatches):
            swatch.show_color(entries[index] if index < len(entries) else None)
        self.clear_button.setEnabled(bool(entries))

    def menu_for(self, swatch: Swatch) -> QMenu:
        """Crea el menú del clic derecho de una muestra (HIST-006)."""
        menu = QMenu(self)
        if swatch.color is not None:
            menu.addAction("Quitar del historial", partial(self.history.remove, swatch.color))
        return menu

    def _choose(self, swatch: Swatch) -> None:
        # Recuperar un color no lo usa: el historial no cambia de orden (HIST-005).
        if swatch.color is not None:
            self.color_chosen.emit(swatch.color)

    def _open_menu(self, swatch: Swatch, position: QPoint) -> None:
        menu = self.menu_for(swatch)
        menu.exec(swatch.mapToGlobal(position))
        menu.deleteLater()

    def _clear(self) -> None:
        if self.confirm(self):
            self.history.clear()
