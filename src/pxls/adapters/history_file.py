"""Historial guardado en un fichero JSON del perfil del usuario.

Spec: HIST-007, HIST-008, HIST-010
"""

from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path

from pxls.adapters.data_file import DataFile, data_folder
from pxls.core.color import Color
from pxls.core.history import (
    HistorySaveError,
    LoadedHistory,
    dump_history,
    load_history,
)

FILE_NAME = "history.json"


def default_history_path() -> Path:
    """Devuelve la ruta del historial en la carpeta ``pxls`` de ``APPDATA`` o del perfil."""
    return data_folder() / FILE_NAME


class HistoryFile:
    """Lee y escribe el historial en ``path``; un fichero dañado se aparta con fecha (HIST-008)."""

    def __init__(self, path: Path, now: Callable[[], datetime] = datetime.now) -> None:
        """Usa ``path``; ``now`` da la fecha de la copia de un fichero dañado."""
        self.path = path
        self._file = DataFile(path, now)

    def load(self) -> LoadedHistory:
        """Recupera el historial; si está dañado, lo aparta y arranca vacío con un aviso."""
        read = self._file.read(load_history)
        if read.unreadable:
            warning = (
                f"No se ha podido leer el historial de {self.path}; no se guardará en esta sesión."
            )
            return LoadedHistory((), warning)
        if read.copy is not None:
            warning = (
                f"El historial estaba dañado; se ha empezado uno nuevo y el anterior está en "
                f"{read.copy}"
            )
            return LoadedHistory((), warning)
        return LoadedHistory(read.value if read.value is not None else ())

    def save(self, colors: Sequence[Color]) -> None:
        """Escribe el historial en un fichero temporal y lo pone en lugar del anterior.

        Si no puede, deja el fichero anterior como estaba y lanza ``HistorySaveError`` (HIST-010).
        """
        try:
            self._file.write(dump_history(colors))
        except OSError as error:
            raise HistorySaveError(str(self.path)) from error
