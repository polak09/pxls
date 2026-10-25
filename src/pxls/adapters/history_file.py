"""Historial guardado en un fichero JSON del perfil del usuario.

Spec: HIST-007, HIST-008, HIST-010
"""

import os
from collections.abc import Callable, Sequence
from contextlib import suppress
from datetime import datetime
from pathlib import Path

from pxls.core.color import Color
from pxls.core.history import (
    HistoryFormatError,
    HistorySaveError,
    LoadedHistory,
    dump_history,
    load_history,
)

FILE_NAME = "history.json"


def default_history_path() -> Path:
    """Devuelve la ruta del historial en la carpeta ``pxls`` de ``APPDATA`` o del perfil."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / "pxls" / FILE_NAME


class HistoryFile:
    """Lee y escribe el historial en ``path``; un fichero dañado se aparta con fecha (HIST-008)."""

    def __init__(self, path: Path, now: Callable[[], datetime] = datetime.now) -> None:
        """Usa ``path``; ``now`` da la fecha de la copia de un fichero dañado."""
        self.path = path
        self.writable = True
        self._now = now

    def load(self) -> LoadedHistory:
        """Recupera el historial; si está dañado, lo aparta y arranca vacío con un aviso."""
        try:
            return LoadedHistory(load_history(self.path.read_bytes().decode("utf-8")))
        except FileNotFoundError:
            return LoadedHistory(())
        except (OSError, UnicodeDecodeError, HistoryFormatError):
            pass
        try:
            copy = self._set_aside()
        except OSError:
            # Sin poder leerlo ni apartarlo, escribir encima lo perdería.
            self.writable = False
            warning = (
                f"No se ha podido leer el historial de {self.path}; no se guardará en esta sesión."
            )
            return LoadedHistory((), warning)
        warning = (
            f"El historial estaba dañado; se ha empezado uno nuevo y el anterior está en {copy}"
        )
        return LoadedHistory((), warning)

    def save(self, colors: Sequence[Color]) -> None:
        """Escribe el historial en un fichero temporal y lo pone en lugar del anterior.

        Si no puede, deja el fichero anterior como estaba y lanza ``HistorySaveError`` (HIST-010).
        """
        if not self.writable:
            return
        temporary = self.path.with_name(f"{self.path.name}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(dump_history(colors), encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError as error:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise HistorySaveError(str(self.path)) from error

    def _set_aside(self) -> Path:
        stamp = self._now().strftime("%Y%m%d-%H%M%S")
        copy = self.path.with_name(f"{self.path.stem}-dañado-{stamp}.json")
        number = 2
        while copy.exists():
            copy = self.path.with_name(f"{self.path.stem}-dañado-{stamp}-{number}.json")
            number += 1
        self.path.rename(copy)
        return copy
