"""Celdas y posición de la lupa del cuentagotas.

Spec: PICK-003
"""

from pxls.core.color import Color
from pxls.core.screen import Point, Rect, Screenshot

LENS_PIXELS = 11
ZOOM = 10
GAP = 16


def neighbourhood(screenshot: Screenshot, centre: Point) -> list[list[Color | None]]:
    """Devuelve los 11 por 11 colores alrededor de ``centre``; ``None`` fuera del escritorio."""
    half = LENS_PIXELS // 2
    return [
        [screenshot.color_at(centre.moved(dx, dy)) for dx in range(-half, half + 1)]
        for dy in range(-half, half + 1)
    ]


def lens_origin(cursor: Point, width: int, height: int, screen: Rect) -> Point:
    """Coloca la lupa abajo a la derecha del cursor o, si no cabe, al otro lado (PICK-003)."""
    x = cursor.x + GAP
    if x + width > screen.right:
        x = cursor.x - GAP - width
    y = cursor.y + GAP
    if y + height > screen.bottom:
        y = cursor.y - GAP - height
    return Point(max(x, screen.x), max(y, screen.y))
