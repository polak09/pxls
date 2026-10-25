"""Puerto del portapapeles y copia del color actual en un formato.

Spec: CLIP-001, CLIP-005
"""

from typing import Protocol

from pxls.core.color import Color
from pxls.core.formatting import FORMATS


class ClipboardError(Exception):
    """No se ha podido escribir en el portapapeles; el mensaje explica el motivo en español."""


class Clipboard(Protocol):
    """Portapapeles del sistema, en el que sólo se escribe texto."""

    def set_text(self, text: str) -> None:
        """Pone ``text`` en el portapapeles o lanza ``ClipboardError`` (CLIP-005)."""
        ...


def copy_color(clipboard: Clipboard, color: Color, format_name: str) -> str:
    """Copia el texto del color en el formato indicado y lo devuelve (CLIP-001)."""
    text = FORMATS[format_name](color)
    clipboard.set_text(text)
    return text
