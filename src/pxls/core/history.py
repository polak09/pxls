"""Historial de colores usados y su formato de guardado, sin depender de la interfaz ni del disco.

Spec: HIST-002, HIST-003, HIST-004, HIST-006, HIST-007, HIST-008, HIST-010
"""

import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from pxls.core.color import Color, ColorError

LIMIT = 20
FORMAT_VERSION = 1


class HistoryFormatError(ValueError):
    """El texto guardado no es un historial válido."""


class HistorySaveError(Exception):
    """No se ha podido guardar el historial en ``location`` (HIST-010)."""

    def __init__(self, location: str) -> None:
        """Guarda dónde se intentaba guardar el historial."""
        super().__init__(location)
        self.location = location


class History:
    """Colores usados, el más reciente primero, sin repetidos y como mucho ``LIMIT``."""

    def __init__(self, colors: Iterable[Color] = ()) -> None:
        """Crea el historial con ``colors``, ya ordenados del más reciente al más antiguo."""
        self._entries: list[Color] = []
        for color in colors:
            if color not in self._entries and len(self._entries) < LIMIT:
                self._entries.append(color)
        self._listeners: list[Callable[[tuple[Color, ...]], None]] = []

    @property
    def entries(self) -> tuple[Color, ...]:
        """Devuelve las entradas, la más reciente primero (HIST-002)."""
        return tuple(self._entries)

    def on_change(self, listener: Callable[[tuple[Color, ...]], None]) -> None:
        """Registra una función que recibe las entradas cada vez que cambian."""
        self._listeners.append(listener)

    def add(self, color: Color) -> None:
        """Pone ``color`` el primero, sin repetirlo (HIST-004) y sin pasar del límite (HIST-003)."""
        if self._entries[:1] == [color]:
            return
        if color in self._entries:
            self._entries.remove(color)
        self._entries.insert(0, color)
        del self._entries[LIMIT:]
        self._notify()

    def remove(self, color: Color) -> None:
        """Quita ``color`` del historial si está en él (HIST-006)."""
        if color in self._entries:
            self._entries.remove(color)
            self._notify()

    def clear(self) -> None:
        """Vacía el historial (HIST-006)."""
        if self._entries:
            self._entries.clear()
            self._notify()

    def _notify(self) -> None:
        entries = self.entries
        for listener in self._listeners:
            listener(entries)


@dataclass(frozen=True, slots=True)
class LoadedHistory:
    """Historial recuperado al arrancar y, si algo ha ido mal, el aviso para el usuario."""

    colors: tuple[Color, ...]
    warning: str | None = None


class HistoryStore(Protocol):
    """Dónde se conserva el historial entre sesiones (HIST-007)."""

    def load(self) -> LoadedHistory:
        """Recupera el historial guardado; un historial dañado se trata según HIST-008."""
        ...

    def save(self, colors: Sequence[Color]) -> None:
        """Guarda las entradas, la más reciente primero; si no puede, lanza ``HistorySaveError``."""
        ...


def dump_history(colors: Sequence[Color]) -> str:
    """Escribe las entradas en JSON, en HEX y la más reciente primero."""
    document = {"version": FORMAT_VERSION, "colors": [color.to_hex() for color in colors]}
    return json.dumps(document, indent=2) + "\n"


def load_history(text: str) -> tuple[Color, ...]:
    """Lee las entradas escritas por ``dump_history``; lanza ``HistoryFormatError`` si no lo son."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise HistoryFormatError(f"no es JSON válido: {error}") from error
    if not isinstance(document, dict) or document.get("version") != FORMAT_VERSION:
        raise HistoryFormatError(f"no es un historial de la versión {FORMAT_VERSION}")
    hexes = document.get("colors")
    if not isinstance(hexes, list) or not all(isinstance(value, str) for value in hexes):
        raise HistoryFormatError("los colores no son una lista de textos")
    try:
        return tuple(Color.from_hex(value) for value in hexes)
    except ColorError as error:
        raise HistoryFormatError(f"tiene un color no válido: {error}") from error
