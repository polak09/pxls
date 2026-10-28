import ctypes
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pytest

from pxls.adapters.palettes_file import PalettesFile, default_palettes_path
from pxls.core.color import Color
from pxls.core.palettes import Palettes, PalettesSaveError

RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
MOMENT = datetime(2026, 10, 25, 9, 30, 5)
GENERIC_READ = 0x80000000
OPEN_EXISTING = 3
INVALID_HANDLE = ctypes.c_void_p(-1).value

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.CreateFileW.restype = ctypes.c_void_p
_kernel32.CreateFileW.argtypes = (
    ctypes.c_wchar_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_void_p,
)
_kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)


@contextmanager
def locked(path: Path) -> Iterator[None]:
    """Abre ``path`` sin compartirlo, como otro programa que lo tuviera bloqueado."""
    handle = _kernel32.CreateFileW(str(path), GENERIC_READ, 0, None, OPEN_EXISTING, 0, None)
    assert handle not in (None, INVALID_HANDLE), ctypes.get_last_error()
    try:
        yield
    finally:
        _kernel32.CloseHandle(handle)


def store(path: Path) -> PalettesFile:
    return PalettesFile(path, now=lambda: MOMENT)


def sample() -> Palettes:
    return Palettes({"Web": [RED, BLUE], "Marca": [GREEN]}, active="Marca")


# PAL-011 · Conservar entre sesiones


@pytest.mark.spec("PAL-011")
def test_a_new_store_on_the_same_file_loads_what_was_saved(tmp_path: Path) -> None:
    path = tmp_path / "palettes.json"
    store(path).save(sample())
    loaded = store(path).load()
    assert loaded.warning is None
    assert loaded.palettes.names == ("Marca", "Web")
    assert loaded.palettes.active == "Marca"
    assert loaded.palettes.colors("Web") == (RED, BLUE)


@pytest.mark.spec("PAL-011")
def test_without_a_saved_file_there_are_no_palettes(tmp_path: Path) -> None:
    path = tmp_path / "palettes.json"
    loaded = store(path).load()
    assert loaded.palettes.names == ()
    assert loaded.warning is None
    assert not path.exists()


@pytest.mark.spec("PAL-011")
def test_saving_creates_the_folder_and_leaves_only_the_palettes(tmp_path: Path) -> None:
    path = tmp_path / "pxls" / "palettes.json"
    store(path).save(sample())
    assert [child.name for child in path.parent.iterdir()] == ["palettes.json"]
    assert json.loads(path.read_text(encoding="utf-8"))["active"] == "Marca"


@pytest.mark.spec("PAL-011")
def test_the_palettes_live_next_to_the_history_in_appdata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert default_palettes_path() == tmp_path / "pxls" / "palettes.json"


# PAL-012 · Fichero de las paletas dañado


@pytest.mark.spec("PAL-012")
@pytest.mark.parametrize(
    "content", [b"esto no es JSON", b'{"version": 1, "active": "X", "palettes": []}', b"\xff\xfe"]
)
def test_a_damaged_file_starts_without_palettes_warns_and_keeps_a_copy(
    tmp_path: Path, content: bytes
) -> None:
    path = tmp_path / "palettes.json"
    path.write_bytes(content)
    loaded = store(path).load()
    copy = tmp_path / "palettes-dañado-20261025-093005.json"
    assert loaded.palettes.names == ()
    assert loaded.warning is not None
    assert str(copy) in loaded.warning
    assert copy.read_bytes() == content
    assert not path.exists()


@pytest.mark.spec("PAL-012")
def test_a_file_that_cannot_be_read_is_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "palettes.json"
    store(path).save(sample())
    before = path.read_bytes()
    saver = store(path)
    with locked(path):
        loaded = saver.load()
    assert loaded.palettes.names == ()
    assert loaded.warning is not None
    assert "no se guardarán" in loaded.warning
    saver.save(Palettes())
    assert path.read_bytes() == before


# PAL-013 · Fallo al guardar las paletas


def blocked_path(tmp_path: Path) -> tuple[Path, Path]:
    """Ruta cuya carpeta es en realidad un fichero, así que no se puede escribir en ella."""
    blocker = tmp_path / "pxls"
    blocker.write_text("no es una carpeta", encoding="utf-8")
    return blocker, blocker / "palettes.json"


@pytest.mark.spec("PAL-013")
def test_a_file_that_cannot_be_written_raises_with_its_path(tmp_path: Path) -> None:
    _, path = blocked_path(tmp_path)
    with pytest.raises(PalettesSaveError) as raised:
        store(path).save(sample())
    assert raised.value.location == str(path)


@pytest.mark.spec("PAL-013")
def test_saving_works_again_once_the_problem_is_gone(tmp_path: Path) -> None:
    blocker, path = blocked_path(tmp_path)
    saver = store(path)
    with pytest.raises(PalettesSaveError):
        saver.save(sample())
    blocker.unlink()
    saver.save(sample())
    assert store(path).load().palettes.names == ("Marca", "Web")


@pytest.mark.spec("PAL-013")
def test_a_failed_save_leaves_the_previous_file_and_no_temporary(tmp_path: Path) -> None:
    path = tmp_path / "palettes.json"
    saver = store(path)
    saver.save(sample())
    with locked(path), pytest.raises(PalettesSaveError):
        saver.save(Palettes())
    assert [child.name for child in tmp_path.iterdir()] == ["palettes.json"]
    assert store(path).load().palettes.names == ("Marca", "Web")
