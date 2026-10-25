"""Pestaña «Historial»: rejilla de muestras de los colores usados, quitar y vaciar.

Spec: HIST-002, HIST-005, HIST-006, HIST-009, APP-006
"""

from collections.abc import Callable
from functools import partial

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
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

SWATCH_SIZE = 24
COLUMNS = 10
_GAP = 4
_TILE = 6


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


class HistorySwatch(QAbstractButton):
    """Muestra de una entrada, con cuadros debajo para que se vea la transparencia."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Crea la muestra vacía."""
        super().__init__(parent)
        self.setFixedSize(SWATCH_SIZE, SWATCH_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.color: Color | None = None
        self.show_color(None)

    def show_color(self, color: Color | None) -> None:
        """Muestra ``color``, o ninguno; su HEX es la pista de la muestra (HIST-005)."""
        self.color = color
        self.setEnabled(color is not None)
        self.setToolTip(color.to_hex() if color is not None else "")
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Pinta los cuadros y el color, o sólo el borde si la muestra está vacía."""
        painter = QPainter(self)
        inside = self.rect().adjusted(1, 1, -1, -1)
        if self.color is not None:
            for row in range(inside.top(), inside.bottom() + 1, _TILE):
                for column in range(inside.left(), inside.right() + 1, _TILE):
                    odd = ((row - inside.top()) // _TILE + (column - inside.left()) // _TILE) % 2
                    shade = 204 if odd else 255
                    painter.fillRect(column, row, _TILE, _TILE, QColor(shade, shade, shade))
            painter.fillRect(inside, QColor(*self.color.channels()))
        border = self.palette().color(QPalette.ColorRole.Mid)
        painter.setPen(QPen(border, 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()


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
        grid.setSpacing(_GAP)
        self.swatches: list[HistorySwatch] = []
        for index in range(LIMIT):
            swatch = HistorySwatch(self)
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

    def menu_for(self, swatch: HistorySwatch) -> QMenu:
        """Crea el menú del clic derecho de una muestra (HIST-006)."""
        menu = QMenu(self)
        if swatch.color is not None:
            menu.addAction("Quitar del historial", partial(self.history.remove, swatch.color))
        return menu

    def _choose(self, swatch: HistorySwatch) -> None:
        # Recuperar un color no lo usa: el historial no cambia de orden (HIST-005).
        if swatch.color is not None:
            self.color_chosen.emit(swatch.color)

    def _open_menu(self, swatch: HistorySwatch, position: QPoint) -> None:
        menu = self.menu_for(swatch)
        menu.exec(swatch.mapToGlobal(position))
        menu.deleteLater()

    def _clear(self) -> None:
        if self.confirm(self):
            self.history.clear()
