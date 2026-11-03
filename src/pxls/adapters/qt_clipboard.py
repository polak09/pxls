"""Portapapeles del sistema a través de Qt.

Spec: CLIP-001, CLIP-005
"""

from PySide6.QtGui import QGuiApplication

from pxls.core.clipboard import ClipboardError


class QtClipboard:
    """Escribe texto en el portapapeles del sistema y comprueba que ha llegado."""

    def set_text(self, text: str) -> None:
        """Pone ``text`` en el portapapeles; si otra aplicación lo impide, lanza ``ClipboardError``.

        ``QClipboard.setText`` no informa de errores: el texto se relee para comprobarlo.
        """
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        if clipboard.text() != text:
            raise ClipboardError("no se ha podido escribir en el portapapeles: está ocupado")
