"""Ventanas superpuestas del modo cuentagotas, una por pantalla.

Spec: PICK-001, PICK-002, PICK-003, PICK-004, PICK-005, PICK-006, HIST-001
"""

from PySide6.QtCore import QObject, QRect, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QCursor,
    QGuiApplication,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QScreen,
)
from PySide6.QtWidgets import QWidget

from pxls.core.color import Color
from pxls.core.conversions import to_hsl
from pxls.core.magnifier import LENS_PIXELS, ZOOM, lens_origin, neighbourhood
from pxls.core.picker import PickerSession
from pxls.core.screen import Point, Rect, Screenshot

LABEL_HEIGHT = 22
_FRAME = QColor(31, 41, 55)
_OUTSIDE = QColor(60, 60, 60)

_ARROWS = {
    Qt.Key.Key_Left: (-1, 0),
    Qt.Key.Key_Right: (1, 0),
    Qt.Key.Key_Up: (0, -1),
    Qt.Key.Key_Down: (0, 1),
}
_CAPTURE_KEYS = frozenset({Qt.Key.Key_Return, Qt.Key.Key_Enter})


def physical_rect(screen: QScreen) -> Rect:
    """Rectángulo de una pantalla en píxeles físicos: Qt conserva el origen y escala el tamaño."""
    geometry, ratio = screen.geometry(), screen.devicePixelRatio()
    width, height = round(geometry.width() * ratio), round(geometry.height() * ratio)
    return Rect(geometry.x(), geometry.y(), width, height)


def desktop_image(screenshot: Screenshot) -> QImage:
    """Convierte la captura en una imagen de Qt con sus propios datos."""
    bounds = screenshot.bounds
    image = QImage(
        screenshot.bgra(), bounds.width, bounds.height, bounds.width * 4, QImage.Format.Format_RGB32
    )
    return image.copy()


class PickerController(QObject):
    """Abre y cierra las ventanas superpuestas y traduce sus eventos a la sesión."""

    finished = Signal()
    captured = Signal(Color)

    def __init__(self, session: PickerSession) -> None:
        """Crea el controlador del modo cuentagotas de ``session``."""
        super().__init__()
        self.session = session
        self.overlays: list[PickerOverlay] = []

    @property
    def active(self) -> bool:
        """Indica si el modo cuentagotas está activo."""
        return self.session.active

    def start(self) -> None:
        """Congela la pantalla y cubre cada pantalla con su trozo de la captura (PICK-001)."""
        if self.active:
            return
        screenshot = self.session.start()
        desktop = desktop_image(screenshot)
        self.overlays = [
            PickerOverlay(self, screen, desktop, screenshot.bounds)
            for screen in QGuiApplication.screens()
        ]
        for overlay in self.overlays:
            overlay.show()
        under_cursor = QGuiApplication.screenAt(QCursor.pos())
        focused = next((o for o in self.overlays if o.screen() is under_cursor), self.overlays[0])
        focused.activateWindow()
        focused.setFocus()

    def capture(self) -> None:
        """Captura el color bajo el cursor y cierra el modo (PICK-004); avisa con ``captured``."""
        color = self.session.capture()
        self._close()
        if color is not None:
            self.captured.emit(color)

    def cancel(self) -> None:
        """Cierra el modo sin cambiar el color actual (PICK-005)."""
        self.session.cancel()
        self._close()

    def nudge(self, dx: int, dy: int) -> None:
        """Mueve el cursor un píxel físico (PICK-006)."""
        self.session.nudge(dx, dy)
        for overlay in self.overlays:
            overlay.update()

    def _close(self) -> None:
        for overlay in self.overlays:
            overlay.close()
        self.finished.emit()


class PickerOverlay(QWidget):
    """Ventana sin marco que muestra la pantalla congelada y recibe ratón y teclado."""

    def __init__(
        self, controller: PickerController, screen: QScreen, desktop: QImage, bounds: Rect
    ) -> None:
        """Cubre ``screen`` con su trozo de ``desktop``, pintado 1:1 en píxeles físicos."""
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        super().__init__(None, flags)
        self._controller = controller
        area = physical_rect(screen)
        piece = desktop.copy(area.x - bounds.x, area.y - bounds.y, area.width, area.height)
        piece.setDevicePixelRatio(screen.devicePixelRatio())
        self._piece = piece
        self._area = area
        self._ratio = screen.devicePixelRatio()
        self.setScreen(screen)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def lens_rect(self) -> QRect | None:
        """Rectángulo de la lupa en esta ventana, o ``None`` si el cursor está en otra pantalla."""
        cursor = self._cursor_in_window()
        if cursor is None:
            return None
        side = LENS_PIXELS * ZOOM
        window = Rect(0, 0, self.width(), self.height())
        origin = lens_origin(cursor, side, side + LABEL_HEIGHT, window)
        return QRect(origin.x, origin.y, side, side + LABEL_HEIGHT)

    def lens_hex(self) -> str | None:
        """HEX del píxel bajo el cursor que muestra la lupa (PICK-003)."""
        screenshot = self._controller.session.screenshot
        if screenshot is None:
            return None
        color = screenshot.color_at(self._controller.session.pointer.position())
        return color.to_hex() if color is not None else None

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        """Pinta la pantalla congelada (PICK-002) y, si el cursor está aquí, la lupa (PICK-003)."""
        painter = QPainter(self)
        painter.drawImage(0, 0, self._piece)
        lens = self.lens_rect()
        screenshot = self._controller.session.screenshot
        if lens is not None and screenshot is not None:
            self._paint_lens(painter, lens, screenshot)
        painter.end()

    def _paint_lens(self, painter: QPainter, lens: QRect, screenshot: Screenshot) -> None:
        cells = neighbourhood(screenshot, self._controller.session.pointer.position())
        for row, colors in enumerate(cells):
            for column, color in enumerate(colors):
                cell = QRect(lens.x() + column * ZOOM, lens.y() + row * ZOOM, ZOOM, ZOOM)
                painter.fillRect(cell, _OUTSIDE if color is None else QColor(*color.channels()))
        centre = cells[LENS_PIXELS // 2][LENS_PIXELS // 2]
        painter.setPen(_contrast(centre))
        middle = LENS_PIXELS // 2 * ZOOM
        painter.drawRect(lens.x() + middle, lens.y() + middle, ZOOM - 1, ZOOM - 1)
        side = LENS_PIXELS * ZOOM
        label = QRect(lens.x(), lens.y() + side, side, LABEL_HEIGHT)
        painter.fillRect(label, _FRAME)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(label, Qt.AlignmentFlag.AlignCenter, self.lens_hex() or "")
        painter.setPen(_FRAME)
        painter.drawRect(lens.adjusted(0, 0, -1, -1))

    def _cursor_in_window(self) -> Point | None:
        pointer = self._controller.session.pointer.position()
        if not self._area.contains(pointer):
            return None
        x = round((pointer.x - self._area.x) / self._ratio)
        y = round((pointer.y - self._area.y) / self._ratio)
        return Point(x, y)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Captura con el botón izquierdo y cancela con el derecho."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._controller.capture()
        elif event.button() == Qt.MouseButton.RightButton:
            self._controller.cancel()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Repinta para que la lupa siga al cursor."""
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Cancela con Esc, captura con Intro y mueve un píxel con las flechas."""
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._controller.cancel()
        elif key in _CAPTURE_KEYS:
            self._controller.capture()
        elif key in _ARROWS:
            self._controller.nudge(*_ARROWS[Qt.Key(key)])
        else:
            super().keyPressEvent(event)


def _contrast(color: Color | None) -> QColor:
    """Negro sobre colores claros y blanco sobre oscuros, para resaltar el píxel central."""
    if color is None or to_hsl(color).lightness < 50:
        return QColor(255, 255, 255)
    return QColor(0, 0, 0)
