"""Paletas guardadas en un fichero JSON del perfil del usuario.

Spec: PAL-011, PAL-012, PAL-013
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from pxls.adapters.data_file import DataFile, data_folder
from pxls.core.palettes import (
    LoadedPalettes,
    Palettes,
    PalettesSaveError,
    dump_palettes,
    load_palettes,
)

FILE_NAME = "palettes.json"


def default_palettes_path() -> Path:
    """Devuelve la ruta de las paletas, en la misma carpeta que el historial."""
    return data_folder() / FILE_NAME


class PalettesFile:
    """Lee y escribe las paletas en ``path``; un fichero dañado se aparta con fecha (PAL-012)."""

    def __init__(self, path: Path, now: Callable[[], datetime] = datetime.now) -> None:
        """Usa ``path``; ``now`` da la fecha de la copia de un fichero dañado."""
        self.path = path
        self._file = DataFile(path, now)

    def load(self) -> LoadedPalettes:
        """Recupera las paletas; si están dañadas, aparta el fichero y arranca sin paletas."""
        read = self._file.read(load_palettes)
        if read.unreadable:
            warning = (
                f"No se han podido leer las paletas de {self.path}; no se guardarán en esta sesión."
            )
            return LoadedPalettes(Palettes(), warning)
        if read.copy is not None:
            warning = (
                "Las paletas estaban dañadas; se ha empezado sin paletas y las anteriores están "
                f"en {read.copy}"
            )
            return LoadedPalettes(Palettes(), warning)
        return LoadedPalettes(read.value if read.value is not None else Palettes())

    def save(self, palettes: Palettes) -> None:
        """Guarda las paletas; si no puede, las deja como estaban y lanza ``PalettesSaveError``."""
        try:
            self._file.write(dump_palettes(palettes))
        except OSError as error:
            raise PalettesSaveError(str(self.path)) from error
