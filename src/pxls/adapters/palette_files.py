"""Exportar e importar paletas en los ficheros ``.gpl`` y ``.txt`` que elige el usuario.

Spec: PAL-014, PAL-015
"""

from collections.abc import Sequence
from pathlib import Path

from pxls.adapters.data_file import DataFile
from pxls.core.color import Color
from pxls.core.palette_formats import GPL, TXT, from_gpl, from_txt, to_gpl, to_txt
from pxls.core.palettes import PaletteFormatError


def export_palette(path: Path, name: str, colors: Sequence[Color]) -> None:
    """Escribe la paleta en el formato de la extensión de ``path``; si falla, no cambia nada.

    Lanza ``OSError`` si no se puede escribir y ``PaletteFormatError`` si la extensión no es
    ``.gpl`` ni ``.txt`` (PAL-014).
    """
    suffix = path.suffix.lower()
    if suffix == GPL:
        text = to_gpl(name, colors)
    elif suffix == TXT:
        text = to_txt(colors)
    else:
        raise PaletteFormatError(f"la extensión {suffix!r} no es .gpl ni .txt")
    DataFile(path).write(text)


def import_palette_file(path: Path) -> tuple[str, tuple[Color, ...]]:
    """Lee el nombre y los colores de una paleta ``.gpl`` o ``.txt`` (PAL-015).

    El nombre es el ``Name:`` del ``.gpl`` o, si no lo hay, el del fichero sin extensión. Lanza
    ``OSError`` si no se puede leer y ``ValueError`` si no es una paleta válida.
    """
    suffix = path.suffix.lower()
    if suffix not in (GPL, TXT):
        raise PaletteFormatError(f"la extensión {suffix!r} no es .gpl ni .txt")
    text = path.read_bytes().decode("utf-8-sig")
    if suffix == TXT:
        return path.stem, from_txt(text)
    name, colors = from_gpl(text)
    return name or path.stem, colors
