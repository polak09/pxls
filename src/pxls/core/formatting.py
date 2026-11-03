"""Escritura de un color como texto en RGB, HSL y HSV.

Spec: COLOR-005, COLOR-007, COLOR-009, CLIP-001
"""

from collections.abc import Callable

from pxls.core.color import OPAQUE, Color
from pxls.core.conversions import FULL_TURN, round_half_up, to_hsl, to_hsv


def alpha_fraction(alpha: int) -> str:
    """Escribe el alfa como fracción entre 0 y 1 con dos decimales como máximo."""
    return f"{alpha / OPAQUE:.2f}".rstrip("0").rstrip(".")


def to_rgb_text(color: Color) -> str:
    """Escribe ``rgb(R, G, B)`` si el color es opaco y ``rgba(R, G, B, A)`` si no (COLOR-005)."""
    values = f"{color.red}, {color.green}, {color.blue}"
    return _with_alpha("rgb", values, color.alpha)


def to_hsl_text(color: Color) -> str:
    """Escribe ``hsl(H, S%, L%)`` o ``hsla(H, S%, L%, A)`` con números enteros (COLOR-007)."""
    hsl = to_hsl(color)
    values = _hue_and_percents(hsl.hue, hsl.saturation, hsl.lightness)
    return _with_alpha("hsl", values, color.alpha)


def to_hsv_text(color: Color) -> str:
    """Escribe ``hsv(H, S%, V%)`` o ``hsva(H, S%, V%, A)`` con números enteros (COLOR-009)."""
    hsv = to_hsv(color)
    values = _hue_and_percents(hsv.hue, hsv.saturation, hsv.value)
    return _with_alpha("hsv", values, color.alpha)


def _hue_and_percents(hue: float, first: float, second: float) -> str:
    # Un tono que se redondea a 360 se escribe como 0.
    whole_hue = round_half_up(hue) % int(FULL_TURN)
    return f"{whole_hue}, {round_half_up(first)}%, {round_half_up(second)}%"


def _with_alpha(name: str, values: str, alpha: int) -> str:
    if alpha == OPAQUE:
        return f"{name}({values})"
    return f"{name}a({values}, {alpha_fraction(alpha)})"


FORMATS: dict[str, Callable[[Color], str]] = {
    "HEX": Color.to_hex,
    "RGB": to_rgb_text,
    "HSL": to_hsl_text,
    "HSV": to_hsv_text,
}
"""Formatos en los que se muestra y se copia un color, en el orden del panel (CLIP-001)."""
