"""Formatos de intercambio de paletas: GIMP Palette (``.gpl``) y un HEX por línea (``.txt``).

Spec: PAL-014, PAL-015
"""

from collections.abc import Sequence

from pxls.core.color import Color, ColorError
from pxls.core.palettes import PaletteFormatError

GPL = ".gpl"
TXT = ".txt"
FORMATS = (GPL, TXT)
GPL_HEADER = "GIMP Palette"
GPL_COLUMNS = 10
_NAME = "Name:"
_COLUMNS = "Columns:"


def to_txt(colors: Sequence[Color]) -> str:
    """Escribe un HEX ``#RRGGBBAA`` por línea, con la transparencia (PAL-014)."""
    return "".join(f"{color.to_hex()}\n" for color in colors)


def to_gpl(name: str, colors: Sequence[Color]) -> str:
    """Escribe una GIMP Palette con el nombre y los colores sin transparencia (PAL-014)."""
    lines = [GPL_HEADER, f"{_NAME} {name}", f"{_COLUMNS} {GPL_COLUMNS}", "#"]
    lines += [
        f"{color.red:3d} {color.green:3d} {color.blue:3d}\t{color.to_hex()[:7]}" for color in colors
    ]
    return "\n".join(lines) + "\n"


def loses_alpha(suffix: str, colors: Sequence[Color]) -> bool:
    """Indica si exportar ``colors`` con la extensión ``suffix`` pierde alguna transparencia."""
    return suffix == GPL and any(not color.opaque for color in colors)


def from_txt(text: str) -> tuple[Color, ...]:
    """Lee un HEX por línea, ignorando las vacías; otra línea cualquiera invalida el texto."""
    colors: list[Color] = []
    for number, line in enumerate(text.splitlines(), start=1):
        value = line.strip()
        if not value:
            continue
        try:
            colors.append(Color.from_hex(value))
        except ColorError as error:
            raise PaletteFormatError(f"la línea {number} no es un color: {error}") from error
    return tuple(colors)


def from_gpl(text: str) -> tuple[str | None, tuple[Color, ...]]:
    """Lee el nombre (o ``None``) y los colores opacos de una GIMP Palette."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != GPL_HEADER:
        raise PaletteFormatError(f"no empieza por «{GPL_HEADER}»")
    name: str | None = None
    colors: list[Color] = []
    for number, line in enumerate(lines[1:], start=2):
        value = line.strip()
        if not value or value.startswith(("#", _COLUMNS)):
            continue
        if value.startswith(_NAME):
            name = value.removeprefix(_NAME).strip()
            continue
        try:
            red, green, blue = (int(part) for part in value.split(maxsplit=3)[:3])
            colors.append(Color(red, green, blue))
        except ValueError as error:
            raise PaletteFormatError(f"la línea {number} no es un color") from error
    return name, tuple(colors)
