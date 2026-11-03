"""Sonda para los tests del adaptador real: pinta en las pantallas y captura.

Se ejecuta en un subproceso con la plataforma Qt real (no ``offscreen``) y escribe
el resultado en JSON por la salida estándar.
"""

import json
import time
from typing import Any

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from pxls.adapters.windows_screen import WindowsPointer, WindowsScreenGrabber
from pxls.core.screen import Point, Screenshot

ORANGE = QColor(255, 136, 0)


class Patch(QWidget):
    """Ventana sin marco, siempre encima, con un color liso y un patrón alterno."""

    def __init__(self, area: QRect) -> None:
        super().__init__(
            None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.color = ORANGE
        self.setGeometry(area)

    def paintEvent(self, event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)
        ratio = self.devicePixelRatioF()
        side = round(20 * ratio)
        pattern = QImage(side, side, QImage.Format.Format_RGB32)
        for y in range(side):
            for x in range(side):
                pattern.setPixel(x, y, 0xFFFFFFFF if (x + y) % 2 == 0 else 0xFF000000)
        pattern.setDevicePixelRatio(ratio)
        painter.drawImage(0, 0, pattern)
        painter.end()


def channels(shot: Screenshot, point: Point) -> tuple[int, int, int, int]:
    color = shot.color_at(point)
    assert color is not None, point
    return color.channels()


def physical(widget: QWidget, x: int, y: int) -> Point:
    screen = widget.screen()
    origin, ratio = screen.geometry().topLeft(), screen.devicePixelRatio()
    local = widget.geometry().topLeft() - origin
    return Point(
        origin.x() + round((local.x() + x) * ratio), origin.y() + round((local.y() + y) * ratio)
    )


app = QApplication([])
patches = []
for screen in app.screens():
    g = screen.geometry()
    patch = Patch(QRect(g.x() + 100, g.y() + 100, 80, 80))
    patch.show()
    patches.append(patch)
for _ in range(10):
    app.processEvents()
    time.sleep(0.05)

shot = WindowsScreenGrabber().grab()
for patch in patches:
    patch.color = QColor(0, 0, 255)
    patch.update()
app.processEvents()

result: dict[str, Any] = {"screens": []}
for patch in patches:
    corner = physical(patch, 0, 0)
    centre = physical(patch, 60, 60)
    checker = [
        [channels(shot, Point(corner.x + dx, corner.y + dy)) for dx in range(4)] for dy in range(4)
    ]
    result["screens"].append({"centre": channels(shot, centre), "checker": checker})

pointer = WindowsPointer()
original = pointer.position()
target = physical(patches[-1], 40, 40)
pointer.move_to(target)
result["pointer"] = [pointer.position().x, pointer.position().y, target.x, target.y]
pointer.move_to(original)
print(json.dumps(result))
