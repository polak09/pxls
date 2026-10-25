"""Estado del selector visual: tono, saturación y valor que sobreviven a negros y grises.

Spec: SEL-001, SEL-002, SEL-004, SEL-005, SEL-006
"""

from pxls.core.color import OPAQUE, Color
from pxls.core.conversions import FULL_TURN, PERCENT, from_hsv, round_half_up, to_hsv

CHANNEL_MAXIMUM = 255


def clamp(value: float, maximum: float) -> float:
    """Limita ``value`` al intervalo de 0 a ``maximum``."""
    return min(max(value, 0.0), maximum)


class SelectorState:
    """Tono, saturación y valor elegidos en el selector, además del color que resulta."""

    def __init__(self, color: Color) -> None:
        """Crea el estado a partir del color actual."""
        hsv = to_hsv(color)
        self.hue, self.saturation, self.value = hsv.hue, hsv.saturation, hsv.value
        self._color = color

    @property
    def color(self) -> Color:
        """Color que representa el estado, con su alfa."""
        return self._color

    def set_sv(self, saturation: float, value: float) -> Color:
        """Cambia saturación y valor, limitados a 0 y 100, sin tocar tono ni alfa (SEL-001)."""
        self.saturation = clamp(saturation, PERCENT)
        self.value = clamp(value, PERCENT)
        return self._update()

    def set_hue(self, hue: float) -> Color:
        """Cambia el tono, limitado a 0 y 360, sin tocar el resto (SEL-002)."""
        self.hue = clamp(hue, FULL_TURN)
        return self._update()

    def set_alpha_percent(self, percent: float) -> Color:
        """Cambia el alfa, en porcentaje limitado a 0 y 100, sin tocar el resto (SEL-005)."""
        alpha = round_half_up(clamp(percent, PERCENT) * OPAQUE / PERCENT)
        red, green, blue, _ = self._color.channels()
        self._color = Color(red, green, blue, alpha)
        return self._color

    def alpha_percent(self) -> int:
        """Alfa del color en porcentaje entero."""
        return round_half_up(self._color.alpha * PERCENT / OPAQUE)

    def set_channel(self, index: int, value: float) -> Color:
        """Cambia el rojo (0), el verde (1) o el azul (2), limitado a 0 y 255 (SEL-006)."""
        channels = list(self._color.channels())
        channels[index] = int(clamp(value, CHANNEL_MAXIMUM))
        self.sync(Color(*channels))
        return self._color

    def sync(self, color: Color) -> None:
        """Adopta un color llegado de fuera conservando lo que no define (SEL-004)."""
        if color == self._color:
            return
        hsv = to_hsv(color)
        if hsv.value == 0:
            self.value = 0.0
        elif hsv.saturation == 0:
            self.saturation, self.value = 0.0, hsv.value
        else:
            self.hue, self.saturation, self.value = hsv.hue, hsv.saturation, hsv.value
        self._color = color

    def _update(self) -> Color:
        self._color = from_hsv(self.hue, self.saturation, self.value, self._color.alpha)
        return self._color
