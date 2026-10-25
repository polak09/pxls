"""Panel del color actual: muestra, cuatro formatos con su botón «Copiar» y HEX editable.

Spec: PICK-009, PICK-010, SEL-007, CLIP-001
"""

from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QWidget

from pxls.core.color import Color, ColorError
from pxls.core.formatting import FORMATS

SWATCH_HEIGHT = 48
_ERROR_STYLE = "color: #C62828;"


class ColorPanel(QWidget):
    """Muestra del color actual y sus valores en HEX, RGB, HSL y HSV (PICK-009)."""

    hex_entered = Signal(Color)
    copy_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Crea el panel vacío; ``show_color`` le da su primer color."""
        super().__init__(parent)
        self.swatch = QFrame(self)
        self.swatch.setMinimumHeight(SWATCH_HEIGHT)
        self.swatch.setAutoFillBackground(True)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.swatch, 0, 0, 1, 3)
        layout.setColumnStretch(1, 1)
        self.hex_field = QLineEdit(self)
        self.hex_field.returnPressed.connect(self._enter_hex)
        self.error = QLabel(self)
        self.error.setStyleSheet(_ERROR_STYLE)
        self.error.hide()
        self._values: dict[str, QLabel | QLineEdit] = {}
        self.copy_buttons: dict[str, QPushButton] = {}
        row = 1
        for name in FORMATS:
            value: QLabel | QLineEdit = self.hex_field
            if name != "HEX":
                value = QLabel(self)
                value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            button = QPushButton("Copiar", self)
            button.clicked.connect(partial(self.copy_requested.emit, name))
            layout.addWidget(QLabel(name, self), row, 0)
            layout.addWidget(value, row, 1)
            layout.addWidget(button, row, 2)
            self._values[name] = value
            self.copy_buttons[name] = button
            row += 1
            if name == "HEX":
                layout.addWidget(self.error, row, 1)
                row += 1

    def show_color(self, color: Color) -> None:
        """Pinta la muestra y escribe el color en los cuatro formatos."""
        palette = self.swatch.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(*color.channels()))
        self.swatch.setPalette(palette)
        for name, write in FORMATS.items():
            self._values[name].setText(write(color))

    def values(self) -> dict[str, str]:
        """Devuelve el texto mostrado para cada formato."""
        return {name: widget.text() for name, widget in self._values.items()}

    def _enter_hex(self) -> None:
        """Convierte en color actual el HEX escrito o explica por qué no es válido (SEL-007)."""
        try:
            color = Color.from_hex(self.hex_field.text())
        except ColorError as error:
            self.error.setText(str(error))
            self.error.show()
            return
        self.error.hide()
        self.hex_entered.emit(color)
