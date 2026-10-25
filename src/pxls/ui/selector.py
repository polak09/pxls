"""Selector visual: cuadrado de saturación y valor, barra de tono y barra y campo por componente.

Spec: SEL-001, SEL-002, SEL-003, SEL-004, SEL-005, SEL-006, SEL-008, CLIP-002
"""

from functools import partial

from PySide6.QtCore import QPoint, QPointF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QValidator,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from pxls.core.color import Color
from pxls.core.conversions import FULL_TURN, PERCENT, from_hsv, round_half_up
from pxls.core.picker import PickerSession
from pxls.core.selector import CHANNEL_MAXIMUM, SelectorState, clamp

# Con 181 píxeles de alto, cada píxel de la barra de tono son 2 grados exactos.
SQUARE_WIDTH = 221
SQUARE_HEIGHT = 181
HUE_BAR_WIDTH = 20
HUE_BAR_HEIGHT = 181
ALPHA_BAR_HEIGHT = 16
_MARKER_RADIUS = 5
_TILE = 6

COMPONENT_LABELS = ("Rojo", "Verde", "Azul", "Tono", "Saturación", "Valor", "Alfa")
_CHANNELS = {"Rojo": 0, "Verde": 1, "Azul": 2}
_MAXIMA = {
    "Rojo": CHANNEL_MAXIMUM,
    "Verde": CHANNEL_MAXIMUM,
    "Azul": CHANNEL_MAXIMUM,
    "Tono": int(FULL_TURN),
    "Saturación": int(PERCENT),
    "Valor": int(PERCENT),
    "Alfa": int(PERCENT),
}
_SUFFIXES = {"Tono": "°", "Saturación": " %", "Valor": " %", "Alfa": " %"}


def _qcolor(color: Color) -> QColor:
    return QColor(*color.channels())


class _DragArea(QWidget):
    """Base de las áreas que responden a pulsar y arrastrar con el botón izquierdo."""

    def __init__(self) -> None:
        super().__init__()
        # Al pulsarla toma el foco, así Ctrl+C deja de ir al campo HEX (CLIP-002).
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._dragging = False

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._pick(event.position())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging:
            self._pick(event.position())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._pick(event.position())
            self._dragging = False

    def _pick(self, position: QPointF) -> None:
        raise NotImplementedError


class SvSquare(_DragArea):
    """Cuadrado con la saturación en horizontal y el valor en vertical (SEL-001)."""

    changed = Signal(float, float)

    def __init__(self) -> None:
        """Crea el cuadrado con el tamaño fijo del diseño."""
        super().__init__()
        self.setFixedSize(SQUARE_WIDTH, SQUARE_HEIGHT)
        self._hue, self._saturation, self._value = 0.0, 0.0, PERCENT

    def show_state(self, hue: float, saturation: float, value: float) -> None:
        """Pinta el tono actual y mueve el indicador (SEL-003)."""
        self._hue, self._saturation, self._value = hue, saturation, value
        self.update()

    def marker(self) -> QPoint:
        """Posición del indicador de la saturación y el valor actuales (SEL-003)."""
        x = round(self._saturation / PERCENT * (self.width() - 1))
        y = round((1 - self._value / PERCENT) * (self.height() - 1))
        return QPoint(x, y)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Pinta el tono puro, el degradado al blanco, el degradado al negro y el indicador."""
        painter = QPainter(self)
        area = self.rect()
        painter.fillRect(area, _qcolor(from_hsv(self._hue, PERCENT, PERCENT)))
        to_white = QLinearGradient(0, 0, area.width() - 1, 0)
        to_white.setColorAt(0, QColor(255, 255, 255, 255))
        to_white.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(area, to_white)
        to_black = QLinearGradient(0, 0, 0, area.height() - 1)
        to_black.setColorAt(0, QColor(0, 0, 0, 0))
        to_black.setColorAt(1, QColor(0, 0, 0, 255))
        painter.fillRect(area, to_black)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        centre = QPointF(self.marker())
        painter.setPen(QPen(QColor(0, 0, 0), 3))
        painter.drawEllipse(centre, _MARKER_RADIUS, _MARKER_RADIUS)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawEllipse(centre, _MARKER_RADIUS, _MARKER_RADIUS)
        painter.end()

    def _pick(self, position: QPointF) -> None:
        saturation = clamp(position.x() / (self.width() - 1) * PERCENT, PERCENT)
        value = clamp(PERCENT - position.y() / (self.height() - 1) * PERCENT, PERCENT)
        self.changed.emit(saturation, value)


class HueBar(_DragArea):
    """Barra vertical de tonos, del 0 arriba al 360 abajo (SEL-002)."""

    changed = Signal(float)

    def __init__(self) -> None:
        """Crea la barra con el tamaño fijo del diseño."""
        super().__init__()
        self.setFixedSize(HUE_BAR_WIDTH, HUE_BAR_HEIGHT)
        self._hue = 0.0

    def show_hue(self, hue: float) -> None:
        """Mueve el indicador al tono actual (SEL-003)."""
        self._hue = hue
        self.update()

    def marker(self) -> int:
        """Fila del indicador del tono actual (SEL-003)."""
        return round(self._hue / FULL_TURN * (self.height() - 1))

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Pinta los tonos de 0 a 360 y el indicador."""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height() - 1)
        for step in range(7):
            gradient.setColorAt(step / 6, _qcolor(from_hsv(step * 60, PERCENT, PERCENT)))
        painter.fillRect(self.rect(), gradient)
        y = self.marker()
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(0, y - 2, self.width() - 1, 4)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(1, y, self.width() - 2, y)
        painter.end()

    def _pick(self, position: QPointF) -> None:
        self.changed.emit(clamp(position.y() / (self.height() - 1) * FULL_TURN, FULL_TURN))


class AlphaBar(_DragArea):
    """Barra del alfa, de transparente a opaco, sobre un fondo de cuadros (SEL-005)."""

    valueChanged = Signal(int)  # noqa: N815 - mismo nombre que la señal de QSlider

    def __init__(self) -> None:
        """Crea la barra con el alto fijo del diseño y ancho flexible."""
        super().__init__()
        self.setFixedHeight(ALPHA_BAR_HEIGHT)
        self.setMinimumWidth(100)
        self._value = int(PERCENT)
        self._color = Color(0, 0, 0)

    def value(self) -> int:
        """Alfa mostrado, en porcentaje."""
        return self._value

    def setValue(self, value: int) -> None:  # noqa: N802 - mismo nombre que en QSlider
        """Mueve el indicador al alfa ``value`` sin emitir ``valueChanged``."""
        self._value = value
        self.update()

    def show_color(self, color: Color) -> None:
        """Pinta el degradado con el color actual."""
        self._color = color
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Pinta los cuadros, el degradado de transparente a opaco y el indicador."""
        painter = QPainter(self)
        for row in range(0, self.height(), _TILE):
            for column in range(0, self.width(), _TILE):
                shade = 255 if (row // _TILE + column // _TILE) % 2 == 0 else 204
                painter.fillRect(column, row, _TILE, _TILE, QColor(shade, shade, shade))
        red, green, blue, _ = self._color.channels()
        gradient = QLinearGradient(0, 0, self.width() - 1, 0)
        gradient.setColorAt(0, QColor(red, green, blue, 0))
        gradient.setColorAt(1, QColor(red, green, blue, 255))
        painter.fillRect(self.rect(), gradient)
        x = round(self._value / PERCENT * (self.width() - 1))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(x - 2, 0, 4, self.height() - 1)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(x, 1, x, self.height() - 2)
        painter.end()

    def _pick(self, position: QPointF) -> None:
        value = round_half_up(clamp(position.x() / (self.width() - 1) * PERCENT, PERCENT))
        self.setValue(value)
        self.valueChanged.emit(value)


class ClampingSpinBox(QSpinBox):
    """Campo numérico que acepta un número fuera de rango y lo limita al terminar (SEL-006)."""

    def __init__(self, maximum: int, suffix: str) -> None:
        """Crea el campo de 0 a ``maximum``; sólo avisa del cambio al terminar de escribir."""
        super().__init__()
        self.setRange(0, maximum)
        self.setSuffix(suffix)
        self.setCorrectionMode(QAbstractSpinBox.CorrectionMode.CorrectToNearestValue)
        self.setKeyboardTracking(False)

    def validate(self, text: str, position: int) -> tuple[QValidator.State, str, int]:
        """Trata un número fuera de rango como incompleto, para corregirlo al máximo."""
        result = super().validate(text, position)
        digits = text.removesuffix(self.suffix()).strip()
        if result[0] == QValidator.State.Invalid and digits.isdigit():
            return QValidator.State.Intermediate, text, position
        return result

    def fixup(self, text: str) -> str:
        """Limita al máximo un número fuera de rango al terminar de escribirlo."""
        digits = text.removesuffix(self.suffix()).strip()
        if digits.isdigit():
            return f"{min(int(digits), self.maximum())}{self.suffix()}"
        return text


class ComponentRows(QWidget):
    """Una fila por componente con su etiqueta, su barra y su campo (SEL-005, SEL-006)."""

    changed = Signal(str, int)

    def __init__(self) -> None:
        """Crea las siete filas de componentes."""
        super().__init__()
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)
        self._bars: dict[str, QSlider | AlphaBar] = {}
        self._fields: dict[str, ClampingSpinBox] = {}
        self.alpha_bar = AlphaBar()
        for row, name in enumerate(COMPONENT_LABELS):
            bar: QSlider | AlphaBar = self.alpha_bar
            if name != "Alfa":
                bar = QSlider(Qt.Orientation.Horizontal)
                bar.setRange(0, _MAXIMA[name])
            field = ClampingSpinBox(_MAXIMA[name], _SUFFIXES.get(name, ""))
            grid.addWidget(QLabel(name, self), row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(field, row, 2)
            bar.valueChanged.connect(partial(self.changed.emit, name))
            field.valueChanged.connect(partial(self.changed.emit, name))
            self._bars[name], self._fields[name] = bar, field

    def bar(self, name: str) -> QSlider | AlphaBar:
        """Barra del componente ``name``."""
        return self._bars[name]

    def field(self, name: str) -> ClampingSpinBox:
        """Campo del componente ``name``."""
        return self._fields[name]

    def show_values(self, values: dict[str, int], color: Color) -> None:
        """Muestra los valores sin volver a avisar del cambio."""
        self.alpha_bar.show_color(color)
        for name, value in values.items():
            bar, field = self._bars[name], self._fields[name]
            with QSignalBlocker(bar), QSignalBlocker(field):
                bar.setValue(value)
                field.setValue(value)


class SelectorWidget(QWidget):
    """Selector visual conectado al color actual de la sesión (SEL-008)."""

    def __init__(self, session: PickerSession) -> None:
        """Crea el selector y lo sincroniza con el color actual de ``session``."""
        super().__init__()
        self.session = session
        self.state = SelectorState(session.current)
        self.square = SvSquare()
        self.hue_bar = HueBar()
        self.rows = ComponentRows()
        top = QHBoxLayout()
        top.addWidget(self.square)
        top.addWidget(self.hue_bar)
        top.addStretch()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(top)
        layout.addWidget(self.rows)
        self.square.changed.connect(self._set_sv)
        self.hue_bar.changed.connect(self._set_hue)
        self.rows.changed.connect(self._set_component)
        session.on_change(self._follow)
        self._refresh()

    def _set_sv(self, saturation: float, value: float) -> None:
        self.session.set_current(self.state.set_sv(saturation, value))

    def _set_hue(self, hue: float) -> None:
        self.session.set_current(self.state.set_hue(hue))

    def _set_component(self, name: str, value: int) -> None:
        if name in _CHANNELS:
            color = self.state.set_channel(_CHANNELS[name], value)
        elif name == "Tono":
            color = self.state.set_hue(value)
        elif name == "Saturación":
            color = self.state.set_sv(value, self.state.value)
        elif name == "Valor":
            color = self.state.set_sv(self.state.saturation, value)
        else:
            color = self.state.set_alpha_percent(value)
        self.session.set_current(color)

    def _follow(self, color: Color) -> None:
        self.state.sync(color)
        self._refresh()

    def _refresh(self) -> None:
        self.square.show_state(self.state.hue, self.state.saturation, self.state.value)
        self.hue_bar.show_hue(self.state.hue)
        red, green, blue, _ = self.state.color.channels()
        values = {
            "Rojo": red,
            "Verde": green,
            "Azul": blue,
            "Tono": round_half_up(self.state.hue),
            "Saturación": round_half_up(self.state.saturation),
            "Valor": round_half_up(self.state.value),
            "Alfa": self.state.alpha_percent(),
        }
        self.rows.show_values(values, self.state.color)
