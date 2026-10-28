"""Ficheros de datos de pxls en el perfil: lectura, copia del fichero dañado y escritura atómica.

Spec: PAL-011, PAL-012, PAL-013
"""

import os
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def data_folder() -> Path:
    """Devuelve la carpeta ``pxls`` de ``APPDATA`` o, sin ella, la del perfil del usuario."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / "pxls"


@dataclass(frozen=True, slots=True)
class ReadResult[T]:
    """Lo leído de un fichero, o ``None`` si no existe, está dañado o no se ha podido leer."""

    value: T | None = None
    copy: Path | None = None
    unreadable: bool = False


class DataFile:
    """Fichero de datos que no se pierde: el dañado se aparta con fecha y el ilegible no se pisa."""

    def __init__(self, path: Path, now: Callable[[], datetime] = datetime.now) -> None:
        """Usa ``path``; ``now`` da la fecha de la copia de un fichero dañado."""
        self.path = path
        self.writable = True
        self._now = now

    def read[T](self, parse: Callable[[str], T]) -> ReadResult[T]:
        """Lee el fichero con ``parse``; si falla, lo aparta (PAL-012)."""
        try:
            return ReadResult(parse(self.path.read_bytes().decode("utf-8")))
        except FileNotFoundError:
            return ReadResult()
        except (OSError, ValueError):
            pass
        try:
            return ReadResult(copy=self._set_aside())
        except OSError:
            # Sin poder leerlo ni apartarlo, escribir encima lo perdería.
            self.writable = False
            return ReadResult(unreadable=True)

    def write(self, text: str) -> None:
        """Escribe ``text`` en un temporal y lo pone en lugar del fichero; lanza ``OSError``.

        Si falla, el fichero anterior queda como estaba (PAL-013).
        """
        if not self.writable:
            return
        temporary = self.path.with_name(f"{self.path.name}.tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(text, encoding="utf-8")
            os.replace(temporary, self.path)
        except OSError:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise

    def _set_aside(self) -> Path:
        stamp = self._now().strftime("%Y%m%d-%H%M%S")
        copy = self.path.with_name(f"{self.path.stem}-dañado-{stamp}.json")
        number = 2
        while copy.exists():
            copy = self.path.with_name(f"{self.path.stem}-dañado-{stamp}-{number}.json")
            number += 1
        self.path.rename(copy)
        return copy
