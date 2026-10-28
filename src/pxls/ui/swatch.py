"""Muestra de color de 24 px para la rejilla de las paletas.

Spec: PAL-009, PAL-016
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget

from pxls.core.color import Color

SWATCH_SIZE = 24
COLUMNS = 10
GAP = 4
_TILE = 6


class Swatch(QAbstractButton):
    """Muestra de un color, con cuadros debajo para que se vea la transparencia."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Crea la muestra vacía."""
        super().__init__(parent)
        self.setFixedSize(SWATCH_SIZE, SWATCH_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.color: Color | None = None
        self.show_color(None)

    def show_color(self, color: Color | None) -> None:
        """Muestra ``color``, o ninguno; su HEX es la pista de la muestra (PAL-009)."""
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
