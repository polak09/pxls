"""Paletas de color con nombre y su formato de guardado, sin depender de la interfaz ni del disco.

Spec: PAL-001, PAL-002, PAL-003, PAL-004, PAL-005, PAL-006, PAL-007, PAL-008, PAL-010, PAL-011,
    PAL-012, PAL-013, PAL-015
"""

import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from pxls.core.color import Color, ColorError
from pxls.core.storage import SaveError

MAX_COLORS = 20
MAX_NAME_LENGTH = 40
IMPORTED_NAME = "Paleta importada"
FORMAT_VERSION = 1

EMPTY_NAME = "El nombre no puede estar vacío."
LONG_NAME = f"El nombre no puede tener más de {MAX_NAME_LENGTH} caracteres."
REPEATED_NAME = "Ya hay una paleta con ese nombre."


class PaletteNameError(ValueError):
    """El nombre de una paleta no es válido; el mensaje explica por qué (PAL-002)."""


class PaletteFormatError(ValueError):
    """El texto no es un fichero de paletas ni una paleta en un formato admitido."""


class PalettesSaveError(SaveError):
    """No se han podido guardar las paletas en ``location`` (PAL-013)."""


@dataclass(frozen=True, slots=True)
class Imported:
    """Resultado de importar: nombre final, colores importados y colores distintos del fichero."""

    name: str
    kept: int
    total: int


class Palettes:
    """Paletas por nombre, cada una con hasta ``MAX_COLORS`` colores sin repetir, y la activa."""

    def __init__(
        self, palettes: Mapping[str, Iterable[Color]] | None = None, active: str | None = None
    ) -> None:
        """Crea las paletas; lanza ``ValueError`` o ``KeyError`` si no cumplen las reglas."""
        self._palettes: dict[str, list[Color]] = {}
        self._listeners: list[Callable[[], None]] = []
        for name, colors in (palettes or {}).items():
            if self.clean_name(name) != name:
                raise PaletteNameError(f"el nombre {name!r} tiene espacios en los extremos")
            listed = list(colors)
            if len(set(listed)) != len(listed) or len(listed) > MAX_COLORS:
                raise ValueError(f"la paleta {name!r} repite colores o tiene más de {MAX_COLORS}")
            self._palettes[name] = listed
        if active is not None and active not in self._palettes:
            raise KeyError(active)
        self._active = active

    @property
    def names(self) -> tuple[str, ...]:
        """Devuelve los nombres por orden alfabético, sin distinguir mayúsculas (PAL-005)."""
        return tuple(sorted(self._palettes, key=lambda name: (name.casefold(), name)))

    @property
    def active(self) -> str | None:
        """Devuelve el nombre de la paleta activa, o ``None`` si no hay paletas."""
        return self._active

    @property
    def full(self) -> bool:
        """Indica si la paleta activa ya tiene ``MAX_COLORS`` colores (PAL-010)."""
        return self._active is not None and len(self._palettes[self._active]) >= MAX_COLORS

    def colors(self, name: str | None = None) -> tuple[Color, ...]:
        """Devuelve los colores de la paleta ``name`` o, sin ``name``, de la activa."""
        chosen = self._active if name is None else name
        return () if chosen is None else tuple(self._palettes[chosen])

    def on_change(self, listener: Callable[[], None]) -> None:
        """Registra una función que se llama cada vez que cambian las paletas o la activa."""
        self._listeners.append(listener)

    def clean_name(self, name: str, renaming: bool = False) -> str:
        """Devuelve ``name`` sin espacios en los extremos o lanza ``PaletteNameError`` (PAL-002).

        Al renombrar, el nombre de la propia paleta activa no cuenta como repetido (PAL-003).
        """
        cleaned = name.strip()
        if not cleaned:
            raise PaletteNameError(EMPTY_NAME)
        if len(cleaned) > MAX_NAME_LENGTH:
            raise PaletteNameError(LONG_NAME)
        own = self._active if renaming else None
        key = cleaned.casefold()
        if any(other.casefold() == key and other != own for other in self._palettes):
            raise PaletteNameError(REPEATED_NAME)
        return cleaned

    def create(self, name: str) -> str:
        """Crea una paleta vacía y la activa; devuelve su nombre (PAL-001)."""
        cleaned = self.clean_name(name)
        self._palettes[cleaned] = []
        self._active = cleaned
        self._notify()
        return cleaned

    def rename(self, name: str) -> str:
        """Cambia el nombre de la paleta activa sin tocar sus colores (PAL-003)."""
        current = self._require_active()
        cleaned = self.clean_name(name, renaming=True)
        if cleaned != current:
            self._palettes[cleaned] = self._palettes.pop(current)
            self._active = cleaned
            self._notify()
        return cleaned

    def delete(self) -> None:
        """Borra la paleta activa y activa la siguiente o, si no hay, la anterior (PAL-004)."""
        current = self._require_active()
        index = self.names.index(current)
        del self._palettes[current]
        remaining = self.names
        self._active = remaining[min(index, len(remaining) - 1)] if remaining else None
        self._notify()

    def select(self, name: str) -> None:
        """Convierte ``name`` en la paleta activa (PAL-005)."""
        if name not in self._palettes:
            raise KeyError(name)
        if name != self._active:
            self._active = name
            self._notify()

    def add(self, color: Color) -> bool:
        """Añade ``color`` al final de la paleta activa; ``False`` si ya estaba (PAL-006)."""
        colors = self._active_colors()
        if color in colors:
            return False
        if len(colors) >= MAX_COLORS:
            raise ValueError(f"la paleta ya tiene {MAX_COLORS} colores")
        colors.append(color)
        self._notify()
        return True

    def remove(self, color: Color) -> None:
        """Quita ``color`` de la paleta activa sin cambiar el orden de los demás (PAL-007)."""
        colors = self._active_colors()
        if color in colors:
            colors.remove(color)
            self._notify()

    def move(self, source: int, target: int) -> None:
        """Lleva el color de ``source`` a ``target``, o al final si no hay tantos (PAL-008)."""
        colors = self._active_colors()
        target = min(target, len(colors) - 1)
        if source != target:
            colors.insert(target, colors.pop(source))
            self._notify()

    def import_palette(self, name: str, colors: Iterable[Color]) -> Imported:
        """Crea y activa una paleta con ``colors`` sin repetir y como mucho 20 (PAL-015)."""
        unique = list(dict.fromkeys(colors))
        kept = unique[:MAX_COLORS]
        chosen = self._free_name(name)
        self._palettes[chosen] = kept
        self._active = chosen
        self._notify()
        return Imported(chosen, len(kept), len(unique))

    def _free_name(self, name: str) -> str:
        base = name.strip()[:MAX_NAME_LENGTH].rstrip() or IMPORTED_NAME
        taken = {other.casefold() for other in self._palettes}
        candidate, number = base, 2
        while candidate.casefold() in taken:
            suffix = f" ({number})"
            candidate = base[: MAX_NAME_LENGTH - len(suffix)].rstrip() + suffix
            number += 1
        return candidate

    def _require_active(self) -> str:
        if self._active is None:
            raise LookupError("no hay ninguna paleta activa")
        return self._active

    def _active_colors(self) -> list[Color]:
        return self._palettes[self._require_active()]

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()


@dataclass(frozen=True, slots=True)
class LoadedPalettes:
    """Paletas recuperadas al arrancar y, si algo ha ido mal, el aviso para el usuario."""

    palettes: Palettes
    warning: str | None = None


class PalettesStore(Protocol):
    """Dónde se conservan las paletas entre sesiones (PAL-011)."""

    def load(self) -> LoadedPalettes:
        """Recupera las paletas guardadas; un fichero dañado se trata según PAL-012."""
        ...

    def save(self, palettes: Palettes) -> None:
        """Guarda las paletas; si no puede, lanza ``PalettesSaveError`` (PAL-013)."""
        ...


def dump_palettes(palettes: Palettes) -> str:
    """Escribe las paletas en JSON, por orden alfabético y con la paleta activa."""
    document = {
        "version": FORMAT_VERSION,
        "active": palettes.active,
        "palettes": [
            {"name": name, "colors": [color.to_hex() for color in palettes.colors(name)]}
            for name in palettes.names
        ],
    }
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def load_palettes(text: str) -> Palettes:
    """Lee las paletas escritas por ``dump_palettes``; lanza ``PaletteFormatError`` si no lo son."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise PaletteFormatError(f"no es JSON válido: {error}") from error
    if not isinstance(document, dict) or document.get("version") != FORMAT_VERSION:
        raise PaletteFormatError(f"no son paletas de la versión {FORMAT_VERSION}")
    entries, active = document.get("palettes"), document.get("active")
    if not isinstance(entries, list) or not (active is None or isinstance(active, str)):
        raise PaletteFormatError("las paletas o la paleta activa no tienen el formato esperado")
    found: dict[str, list[Color]] = {}
    for entry in entries:
        name = entry.get("name") if isinstance(entry, dict) else None
        hexes = entry.get("colors") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not isinstance(hexes, list) or name in found:
            raise PaletteFormatError("hay una paleta sin nombre, repetida o sin lista de colores")
        if not all(isinstance(value, str) for value in hexes):
            raise PaletteFormatError(f"los colores de {name!r} no son textos")
        try:
            found[name] = [Color.from_hex(value) for value in hexes]
        except ColorError as error:
            raise PaletteFormatError(f"{name!r} tiene un color no válido: {error}") from error
    try:
        return Palettes(found, active)
    except (ValueError, KeyError) as error:
        raise PaletteFormatError(f"las paletas no cumplen las reglas: {error}") from error
