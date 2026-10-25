"""Color sRGB con canal alfa y su lectura y escritura en HEX.

Spec: COLOR-001, COLOR-002, COLOR-003, COLOR-004, COLOR-013
"""

from dataclasses import dataclass
from string import hexdigits
from typing import Self

_CHANNEL_NAMES = ("rojo", "verde", "azul", "alfa")
_HEX_LENGTHS = (3, 4, 6, 8)
OPAQUE = 255


class ColorError(ValueError):
    """Valor que no describe un color válido; el mensaje explica el motivo en español."""


@dataclass(frozen=True, slots=True)
class Color:
    """Color con componentes rojo, verde, azul y alfa enteros entre 0 y 255."""

    red: int
    green: int
    blue: int
    alpha: int = OPAQUE

    def __post_init__(self) -> None:
        """Rechaza cualquier componente fuera del intervalo de 0 a 255 (COLOR-001)."""
        for name, value in zip(_CHANNEL_NAMES, self.channels(), strict=True):
            if not 0 <= value <= OPAQUE:
                raise ColorError(f"el componente {name} debe estar entre 0 y 255, no {value}")

    @property
    def opaque(self) -> bool:
        """Indica si el color es totalmente opaco (alfa 255)."""
        return self.alpha == OPAQUE

    def channels(self) -> tuple[int, int, int, int]:
        """Devuelve los componentes en el orden rojo, verde, azul y alfa."""
        return self.red, self.green, self.blue, self.alpha

    @classmethod
    def from_hex(cls, text: str) -> Self:
        """Lee un color en HEX: ``#RRGGBBAA``, ``#RRGGBB``, ``#RGBA`` o ``#RGB`` (COLOR-002)."""
        digits = text.strip()
        if not digits:
            raise ColorError("el texto está vacío")
        digits = digits.removeprefix("#")
        invalid = next((char for char in digits if char not in hexdigits), None)
        if invalid is not None:
            raise ColorError(f"`{invalid}` no es un dígito hexadecimal")
        if len(digits) not in _HEX_LENGTHS:
            lengths = "un color HEX tiene 3, 4, 6 u 8 dígitos"
            raise ColorError(f"la longitud no es válida: {lengths}, no {len(digits)}")
        if len(digits) <= 4:
            digits = "".join(char * 2 for char in digits)
        if len(digits) == 6:
            digits += "FF"
        red, green, blue, alpha = (int(digits[i : i + 2], 16) for i in range(0, 8, 2))
        return cls(red, green, blue, alpha)

    def to_hex(self) -> str:
        """Escribe el color como ``#RRGGBBAA`` en mayúsculas (COLOR-004)."""
        return "#" + "".join(f"{value:02X}" for value in self.channels())
