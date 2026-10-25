"""Puertos para leer la pantalla en píxeles físicos y una captura en memoria.

Spec: PICK-002, PICK-006, PICK-007, PICK-008
"""

from dataclasses import dataclass
from typing import Protocol

from pxls.core.color import OPAQUE, Color

_BYTES_PER_PIXEL = 4


@dataclass(frozen=True, slots=True)
class Point:
    """Punto del escritorio virtual en píxeles físicos (puede ser negativo)."""

    x: int
    y: int

    def moved(self, dx: int, dy: int) -> "Point":
        """Devuelve el punto desplazado ``dx`` y ``dy`` píxeles."""
        return Point(self.x + dx, self.y + dy)


@dataclass(frozen=True, slots=True)
class Rect:
    """Rectángulo del escritorio virtual en píxeles físicos."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        """Primera columna a la derecha del rectángulo."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Primera fila por debajo del rectángulo."""
        return self.y + self.height

    def contains(self, point: Point) -> bool:
        """Indica si el punto está dentro del rectángulo."""
        return self.x <= point.x < self.right and self.y <= point.y < self.bottom


class Screenshot(Protocol):
    """Píxeles del escritorio virtual congelados en el momento de la captura."""

    @property
    def bounds(self) -> Rect:
        """Rectángulo del escritorio virtual capturado."""
        ...

    def color_at(self, point: Point) -> Color | None:
        """Devuelve el color del píxel, o ``None`` si está fuera del escritorio."""
        ...

    def bgra(self) -> bytes:
        """Devuelve los píxeles BGRA de todo el escritorio, fila a fila."""
        ...


class ScreenGrabber(Protocol):
    """Puerto para capturar el escritorio virtual completo."""

    def grab(self) -> Screenshot:
        """Captura el escritorio virtual tal como está ahora."""
        ...


class Pointer(Protocol):
    """Puerto para leer y mover el cursor en píxeles físicos."""

    def position(self) -> Point:
        """Devuelve la posición del cursor."""
        ...

    def move_to(self, point: Point) -> None:
        """Lleva el cursor al punto indicado."""
        ...


class BgraScreenshot:
    """Captura en memoria: píxeles BGRA fila a fila, de arriba abajo."""

    def __init__(self, bounds: Rect, pixels: bytes) -> None:
        """Crea la captura copiando ``pixels``, que debe cubrir ``bounds`` exactamente."""
        expected = bounds.width * bounds.height * _BYTES_PER_PIXEL
        if len(pixels) != expected:
            size = f"{bounds.width}x{bounds.height}"
            raise ValueError(f"se esperaban {expected} bytes para {size} píxeles, no {len(pixels)}")
        self._bounds = bounds
        self._pixels = bytes(pixels)

    @property
    def bounds(self) -> Rect:
        """Rectángulo del escritorio virtual capturado."""
        return self._bounds

    def color_at(self, point: Point) -> Color | None:
        """Devuelve el color opaco del píxel, o ``None`` fuera del escritorio (PICK-007)."""
        if not self._bounds.contains(point):
            return None
        row, column = point.y - self._bounds.y, point.x - self._bounds.x
        offset = (row * self._bounds.width + column) * _BYTES_PER_PIXEL
        blue, green, red = self._pixels[offset : offset + 3]
        return Color(red, green, blue, OPAQUE)

    def bgra(self) -> bytes:
        """Devuelve los píxeles BGRA de todo el escritorio, fila a fila."""
        return self._pixels
