"""Modo cuentagotas y color actual, sin depender de la interfaz.

Spec: PICK-002, PICK-004, PICK-005, PICK-006, PICK-010
"""

from collections.abc import Callable

from pxls.core.color import Color
from pxls.core.screen import Pointer, ScreenGrabber, Screenshot

INITIAL_COLOR = Color(255, 255, 255)


class PickerSession:
    """Color actual de pxls y estado del modo cuentagotas."""

    def __init__(self, grabber: ScreenGrabber, pointer: Pointer) -> None:
        """Crea la sesión con blanco opaco como color actual (PICK-010)."""
        self.grabber = grabber
        self.pointer = pointer
        self.current = INITIAL_COLOR
        self.screenshot: Screenshot | None = None
        self._listeners: list[Callable[[Color], None]] = []

    @property
    def active(self) -> bool:
        """Indica si el modo cuentagotas está activo."""
        return self.screenshot is not None

    def on_change(self, listener: Callable[[Color], None]) -> None:
        """Registra una función que se llama cada vez que cambia el color actual."""
        self._listeners.append(listener)

    def start(self) -> Screenshot:
        """Entra en modo cuentagotas congelando la pantalla en este momento (PICK-002)."""
        self.screenshot = self.grabber.grab()
        return self.screenshot

    def capture(self) -> Color:
        """Toma el color del píxel bajo el cursor y sale del modo (PICK-004)."""
        if self.screenshot is not None:
            color = self.screenshot.color_at(self.pointer.position())
            self.screenshot = None
            if color is not None:
                self.set_current(color)
        return self.current

    def cancel(self) -> None:
        """Sale del modo sin cambiar el color actual (PICK-005)."""
        self.screenshot = None

    def nudge(self, dx: int, dy: int) -> None:
        """Mueve el cursor ``dx`` y ``dy`` píxeles físicos en modo cuentagotas (PICK-006)."""
        if self.active:
            self.pointer.move_to(self.pointer.position().moved(dx, dy))

    def set_current(self, color: Color) -> None:
        """Cambia el color actual y avisa a quien lo haya pedido."""
        self.current = color
        for listener in self._listeners:
            listener(color)
