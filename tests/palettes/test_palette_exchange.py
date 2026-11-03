import ctypes
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.palettes import Palettes
from pxls.ui import palettes_view
from pxls.ui.app import create_app
from pxls.ui.palettes_view import (
    GPL_FILTER,
    TXT_FILTER,
    PalettesView,
    ask_export_path,
    ask_import_path,
)

RED = Color(255, 0, 0)
BLUE = Color(0, 0, 255)
HALF_BLUE = Color(0, 0, 255, 128)
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


class Messages:
    def __init__(self, view: PalettesView) -> None:
        self.texts: list[str] = []
        view.message.connect(lambda text, ms: self.texts.append(text))


def view_of(qtbot: QtBot, palettes: Palettes) -> tuple[PalettesView, Messages]:
    create_app([])
    view = PalettesView(palettes, lambda: RED)
    qtbot.addWidget(view)
    view.show()
    QApplication.processEvents()
    return view, Messages(view)


def export_to(view: PalettesView, path: Path | None) -> None:
    view.ask_export_path = lambda parent, name: path
    view.export_action.trigger()


def import_from(view: PalettesView, path: Path | None) -> None:
    view.ask_import_path = lambda parent: path
    view.import_action.trigger()


def color_values(text: str) -> list[list[str]]:
    lines = text.splitlines()
    return [line.split("\t")[0].split() for line in lines[lines.index("#") + 1 :]]


# PAL-014 · Exportar una paleta


@pytest.mark.spec("PAL-014")
def test_exporting_to_txt_writes_one_hex_per_line(qtbot: QtBot, tmp_path: Path) -> None:
    view, messages = view_of(qtbot, Palettes({"Web": [RED, HALF_BLUE]}, active="Web"))
    path = tmp_path / "web.txt"
    export_to(view, path)
    assert path.read_text(encoding="utf-8").splitlines() == ["#FF0000FF", "#0000FF80"]
    assert messages.texts == [f"Paleta exportada a {path}"]


@pytest.mark.spec("PAL-014")
def test_exporting_to_gpl_writes_a_gimp_palette(qtbot: QtBot, tmp_path: Path) -> None:
    view, messages = view_of(qtbot, Palettes({"Web": [RED]}, active="Web"))
    path = tmp_path / "web.gpl"
    export_to(view, path)
    text = path.read_text(encoding="utf-8")
    assert text.startswith("GIMP Palette\n")
    assert "Name: Web" in text.splitlines()
    assert color_values(text) == [["255", "0", "0"]]
    assert messages.texts == [f"Paleta exportada a {path}"]


@pytest.mark.spec("PAL-014")
def test_exporting_transparency_to_gpl_says_it_is_lost(qtbot: QtBot, tmp_path: Path) -> None:
    view, messages = view_of(qtbot, Palettes({"Web": [HALF_BLUE]}, active="Web"))
    path = tmp_path / "web.gpl"
    export_to(view, path)
    assert color_values(path.read_text(encoding="utf-8")) == [["0", "0", "255"]]
    assert messages.texts == [
        f"Paleta exportada a {path} sin transparencia: el formato .gpl no la guarda"
    ]


@pytest.mark.spec("PAL-014")
def test_a_file_that_cannot_be_written_is_left_as_it_was(qtbot: QtBot, tmp_path: Path) -> None:
    view, messages = view_of(qtbot, Palettes({"Web": [RED]}, active="Web"))
    path = tmp_path / "web.txt"
    path.write_text("lo que había\n", encoding="utf-8")
    with locked(path):
        export_to(view, path)
    assert path.read_text(encoding="utf-8") == "lo que había\n"
    assert [child.name for child in tmp_path.iterdir()] == ["web.txt"]
    assert messages.texts == [f"No se ha podido exportar la paleta a {path}"]


@pytest.mark.spec("PAL-014")
def test_cancelling_the_export_writes_nothing(qtbot: QtBot, tmp_path: Path) -> None:
    view, messages = view_of(qtbot, Palettes({"Web": [RED]}, active="Web"))
    export_to(view, None)
    assert messages.texts == []


@pytest.mark.spec("PAL-014")
def test_the_export_dialog_adds_the_extension_of_the_chosen_format(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    create_app([])
    parent = QWidget()
    qtbot.addWidget(parent)
    answers = iter(
        [
            (str(tmp_path / "web"), TXT_FILTER),
            (str(tmp_path / "web"), GPL_FILTER),
            (str(tmp_path / "web.TXT"), GPL_FILTER),
            ("", ""),
        ]
    )
    asked: list[tuple[str, str, str]] = []

    def save_file_name(parent: QWidget, title: str, start: str, filters: str) -> tuple[str, str]:
        asked.append((title, start, filters))
        return next(answers)

    monkeypatch.setattr(QFileDialog, "getSaveFileName", save_file_name)
    assert ask_export_path(parent, "Web") == tmp_path / "web.txt"
    assert ask_export_path(parent, "Web") == tmp_path / "web.gpl"
    assert ask_export_path(parent, "Web") == tmp_path / "web.TXT"
    assert ask_export_path(parent, "Web") is None
    assert asked[0] == ("Exportar paleta", "Web.gpl", f"{GPL_FILTER};;{TXT_FILTER}")


# PAL-015 · Importar una paleta


@pytest.mark.spec("PAL-015")
def test_importing_a_txt_creates_an_active_palette_named_after_the_file(
    qtbot: QtBot, tmp_path: Path
) -> None:
    palettes = Palettes({"Web": []}, active="Web")
    view, messages = view_of(qtbot, palettes)
    path = tmp_path / "marca.txt"
    path.write_text("#FF0000FF\n#0000FF80\n", encoding="utf-8")
    import_from(view, path)
    assert palettes.active == "marca"
    assert palettes.colors() == (RED, HALF_BLUE)
    assert view.combo.currentText() == "marca"
    assert messages.texts == ["Paleta importada: marca"]


@pytest.mark.spec("PAL-015")
def test_an_imported_gpl_takes_its_name_and_a_number_if_it_exists(
    qtbot: QtBot, tmp_path: Path
) -> None:
    palettes = Palettes({"Web": []}, active="Web")
    view, messages = view_of(qtbot, palettes)
    path = tmp_path / "otra.gpl"
    path.write_text("GIMP Palette\nName: Web\n255 0 0\tRojo\n", encoding="utf-8-sig")
    import_from(view, path)
    assert palettes.names == ("Web", "Web (2)")
    assert palettes.colors("Web (2)") == (RED,)
    assert messages.texts == ["Paleta importada: Web (2)"]


@pytest.mark.spec("PAL-015")
def test_a_gpl_without_a_name_is_named_after_the_file(qtbot: QtBot, tmp_path: Path) -> None:
    palettes = Palettes()
    view, _ = view_of(qtbot, palettes)
    path = tmp_path / "colores.gpl"
    path.write_text("GIMP Palette\n0 0 255\n", encoding="utf-8")
    import_from(view, path)
    assert palettes.names == ("colores",)
    assert palettes.colors() == (BLUE,)


@pytest.mark.spec("PAL-015")
@pytest.mark.parametrize(
    ("name", "content"),
    [("rojo.txt", "rojo\n"), ("roto.gpl", "no es GIMP\n"), ("imagen.png", "#FF0000FF\n")],
)
def test_a_file_that_is_not_a_palette_creates_nothing(
    qtbot: QtBot, tmp_path: Path, name: str, content: str
) -> None:
    palettes = Palettes()
    view, messages = view_of(qtbot, palettes)
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    import_from(view, path)
    assert palettes.names == ()
    assert messages.texts == [
        f"No se ha podido importar {path}: no es una paleta .gpl o .txt válida"
    ]


@pytest.mark.spec("PAL-015")
def test_a_file_that_cannot_be_read_creates_nothing(qtbot: QtBot, tmp_path: Path) -> None:
    palettes = Palettes()
    view, messages = view_of(qtbot, palettes)
    path = tmp_path / "no-existe.txt"
    import_from(view, path)
    assert palettes.names == ()
    assert messages.texts == [
        f"No se ha podido importar {path}: no es una paleta .gpl o .txt válida"
    ]


@pytest.mark.spec("PAL-015")
def test_a_palette_exported_to_txt_comes_back_the_same(qtbot: QtBot, tmp_path: Path) -> None:
    colors = [RED, HALF_BLUE, BLUE]
    palettes = Palettes({"Web": colors}, active="Web")
    view, _ = view_of(qtbot, palettes)
    path = tmp_path / "web.txt"
    export_to(view, path)
    import_from(view, path)
    assert palettes.active == "web (2)"
    assert palettes.colors() == tuple(colors)


@pytest.mark.spec("PAL-015")
def test_an_import_keeps_the_first_20_colours_and_says_so(qtbot: QtBot, tmp_path: Path) -> None:
    palettes = Palettes()
    view, messages = view_of(qtbot, palettes)
    colors = [Color(index, 0, 0) for index in range(25)]
    path = tmp_path / "muchos.txt"
    path.write_text("".join(f"{color.to_hex()}\n" for color in colors), encoding="utf-8")
    import_from(view, path)
    assert palettes.colors() == tuple(colors[:20])
    assert messages.texts == ["Paleta importada: muchos, con 20 de sus 25 colores"]


@pytest.mark.spec("PAL-015")
def test_an_import_drops_repeated_colours(qtbot: QtBot, tmp_path: Path) -> None:
    palettes = Palettes()
    view, _ = view_of(qtbot, palettes)
    path = tmp_path / "repes.txt"
    path.write_text("#FF0000FF\n#0000FFFF\n#FF0000FF\n", encoding="utf-8")
    import_from(view, path)
    assert palettes.colors() == (RED, BLUE)


@pytest.mark.spec("PAL-015")
def test_cancelling_the_import_creates_nothing(qtbot: QtBot) -> None:
    palettes = Palettes()
    view, messages = view_of(qtbot, palettes)
    import_from(view, None)
    assert palettes.names == ()
    assert messages.texts == []


@pytest.mark.spec("PAL-015")
def test_the_import_dialog_offers_both_formats(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    create_app([])
    parent = QWidget()
    qtbot.addWidget(parent)
    answers = iter([(str(tmp_path / "web.gpl"), GPL_FILTER), ("", "")])
    asked: list[tuple[str, str]] = []

    def open_file_name(parent: QWidget, title: str, start: str, filters: str) -> tuple[str, str]:
        asked.append((title, filters))
        return next(answers)

    monkeypatch.setattr(QFileDialog, "getOpenFileName", open_file_name)
    assert ask_import_path(parent) == tmp_path / "web.gpl"
    assert ask_import_path(parent) is None
    assert asked[0] == (
        "Importar paleta",
        f"Paletas (*.gpl *.txt);;{GPL_FILTER};;{TXT_FILTER}",
    )
    assert palettes_view.GPL_FILTER == "Paleta de GIMP (*.gpl)"
    assert palettes_view.TXT_FILTER == "Texto con un HEX por línea (*.txt)"
