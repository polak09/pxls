"""Conversiones de un color a HSL y HSV y desde ellos.

Spec: COLOR-006, COLOR-008, COLOR-010, COLOR-011, COLOR-012, COLOR-013
"""

import colorsys
import math
from collections.abc import Iterable
from dataclasses import dataclass

from pxls.core.color import OPAQUE, Color, ColorError

FULL_TURN = 360.0
PERCENT = 100.0


@dataclass(frozen=True, slots=True)
class Hsl:
    """Tono en grados, en [0, 360), y saturación y luminosidad en porcentaje."""

    hue: float
    saturation: float
    lightness: float


@dataclass(frozen=True, slots=True)
class Hsv:
    """Tono en grados, en [0, 360), y saturación y valor en porcentaje."""

    hue: float
    saturation: float
    value: float


def round_half_up(value: float) -> int:
    """Redondea al entero más cercano; los empates (.5), hacia arriba."""
    return math.floor(value + 0.5)


def to_hsl(color: Color) -> Hsl:
    """Calcula el HSL estándar de un color; el tono de un gris es 0 (COLOR-006)."""
    hue, lightness, saturation = colorsys.rgb_to_hls(*_fractions(color))
    return Hsl(hue * FULL_TURN, saturation * PERCENT, lightness * PERCENT)


def from_hsl(hue: float, saturation: float, lightness: float, alpha: int = OPAQUE) -> Color:
    """Obtiene el color de un tono, una saturación y una luminosidad (COLOR-010, COLOR-012)."""
    rgb = colorsys.hls_to_rgb(
        normalize_hue(hue) / FULL_TURN,
        _percent("la luminosidad", lightness) / PERCENT,
        _percent("la saturación", saturation) / PERCENT,
    )
    return _color(rgb, alpha)


def to_hsv(color: Color) -> Hsv:
    """Calcula el HSV estándar de un color; el tono de un gris es 0 (COLOR-008)."""
    hue, saturation, value = colorsys.rgb_to_hsv(*_fractions(color))
    return Hsv(hue * FULL_TURN, saturation * PERCENT, value * PERCENT)


def from_hsv(hue: float, saturation: float, value: float, alpha: int = OPAQUE) -> Color:
    """Obtiene el color de un tono, una saturación y un valor (COLOR-011, COLOR-012)."""
    rgb = colorsys.hsv_to_rgb(
        normalize_hue(hue) / FULL_TURN,
        _percent("la saturación", saturation) / PERCENT,
        _percent("el valor", value) / PERCENT,
    )
    return _color(rgb, alpha)


def normalize_hue(hue: float) -> float:
    """Da la vuelta al círculo: 420 → 60 y -60 → 300 (COLOR-012)."""
    return hue % FULL_TURN


def _percent(name: str, value: float) -> float:
    if not 0 <= value <= PERCENT:
        raise ColorError(f"{name} debe estar entre 0 y 100, no {value}")
    return value


def _fractions(color: Color) -> tuple[float, float, float]:
    return color.red / OPAQUE, color.green / OPAQUE, color.blue / OPAQUE


def _color(rgb: Iterable[float], alpha: int) -> Color:
    red, green, blue = (round_half_up(channel * OPAQUE) for channel in rgb)
    return Color(red, green, blue, alpha)
