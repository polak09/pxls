import ctypes
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pytest

from pxls.adapters.history_file import HistoryFile, default_history_path
from pxls.core.color import Color
from pxls.core.history import HistorySaveError

RED = Color(255, 0, 0)
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


def store(path: Path) -> HistoryFile:
    return HistoryFile(path, now=lambda: MOMENT)


# HIST-007 · Conservar entre sesiones


@pytest.mark.spec("HIST-007")
def test_a_new_store_on_the_same_file_loads_what_was_saved(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    store(path).save([BLUE, RED])
    loaded = store(path).load()
    assert loaded.colors == (BLUE, RED)
    assert loaded.warning is None


@pytest.mark.spec("HIST-007")
def test_without_a_saved_file_the_history_is_empty(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    loaded = store(path).load()
    assert loaded.colors == ()
    assert loaded.warning is None
    assert not path.exists()


@pytest.mark.spec("HIST-007")
def test_saving_creates_the_folder_and_leaves_only_the_history(tmp_path: Path) -> None:
    path = tmp_path / "pxls" / "history.json"
    store(path).save([RED])
    assert [child.name for child in path.parent.iterdir()] == ["history.json"]
    assert json.loads(path.read_text(encoding="utf-8"))["colors"] == ["#FF0000FF"]


@pytest.mark.spec("HIST-007")
def test_saving_again_replaces_the_previous_history(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    saver = store(path)
    saver.save([RED])
    saver.save([BLUE, RED])
    assert store(path).load().colors == (BLUE, RED)


@pytest.mark.spec("HIST-007")
def test_the_history_lives_in_the_pxls_folder_of_appdata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert default_history_path() == tmp_path / "pxls" / "history.json"


@pytest.mark.spec("HIST-007")
def test_without_appdata_the_history_lives_in_the_roaming_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert default_history_path() == tmp_path / "AppData" / "Roaming" / "pxls" / "history.json"


# HIST-008 · Fichero del historial dañado


@pytest.mark.spec("HIST-008")
@pytest.mark.parametrize(
    "content", [b"esto no es JSON", b'{"version": 1, "colors": ["#GG0000FF"]}', b"\xff\xfe\x00"]
)
def test_a_damaged_file_starts_empty_warns_and_keeps_a_copy(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "history.json"
    path.write_bytes(content)
    loaded = store(path).load()
    copy = tmp_path / "history-dañado-20261025-093005.json"
    assert loaded.colors == ()
    assert loaded.warning is not None
    assert str(copy) in loaded.warning
    assert copy.read_bytes() == content
    assert not path.exists()


@pytest.mark.spec("HIST-008")
def test_after_a_damaged_file_the_new_history_is_saved(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text("esto no es JSON", encoding="utf-8")
    saver = store(path)
    saver.load()
    saver.save([RED])
    assert store(path).load().colors == (RED,)


@pytest.mark.spec("HIST-008")
def test_a_second_damaged_file_in_the_same_second_keeps_both_copies(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    for content in ("primero", "segundo"):
        path.write_text(content, encoding="utf-8")
        store(path).load()
    copies = sorted(child.name for child in tmp_path.iterdir())
    assert copies == [
        "history-dañado-20261025-093005-2.json",
        "history-dañado-20261025-093005.json",
    ]
    assert (tmp_path / copies[0]).read_text(encoding="utf-8") == "segundo"


@pytest.mark.spec("HIST-008")
def test_a_file_that_cannot_be_read_is_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text('{"version": 1, "colors": ["#0000FFFF"]}', encoding="utf-8")
    saver = store(path)
    with locked(path):
        loaded = saver.load()
        saver.save([RED])
    assert loaded.colors == ()
    assert loaded.warning is not None
    assert "no se guardará" in loaded.warning
    saver.save([RED])
    assert store(path).load().colors == (BLUE,)


# HIST-010 · Fallo al guardar el historial


def blocked_path(tmp_path: Path) -> tuple[Path, Path]:
    """Ruta cuya carpeta es en realidad un fichero, así que no se puede escribir en ella."""
    blocker = tmp_path / "pxls"
    blocker.write_text("no es una carpeta", encoding="utf-8")
    return blocker, blocker / "history.json"


@pytest.mark.spec("HIST-010")
def test_a_file_that_cannot_be_written_raises_with_its_path(tmp_path: Path) -> None:
    _, path = blocked_path(tmp_path)
    with pytest.raises(HistorySaveError) as raised:
        store(path).save([RED])
    assert raised.value.location == str(path)


@pytest.mark.spec("HIST-010")
def test_saving_works_again_once_the_problem_is_gone(tmp_path: Path) -> None:
    blocker, path = blocked_path(tmp_path)
    saver = store(path)
    with pytest.raises(HistorySaveError):
        saver.save([RED])
    blocker.unlink()
    saver.save([BLUE, RED])
    assert store(path).load().colors == (BLUE, RED)


@pytest.mark.spec("HIST-010")
def test_a_failed_save_leaves_no_temporary_file(tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    saver = store(path)
    saver.save([BLUE])
    with locked(path), pytest.raises(HistorySaveError):
        saver.save([RED])
    assert [child.name for child in tmp_path.iterdir()] == ["history.json"]
    assert store(path).load().colors == (BLUE,)
