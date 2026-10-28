import json
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from pxls.adapters.history_file import HistoryFile
from pxls.adapters.palettes_file import PalettesFile
from pxls.core.color import Color
from pxls.core.palettes import MAX_COLORS, LoadedPalettes, Palettes, PalettesSaveError
from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui import app
from pxls.ui.app import create_app, main
from pxls.ui.main_window import MainWindow

RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)


class OrangeDesktop:
    def grab(self) -> BgraScreenshot:
        geometry = QGuiApplication.primaryScreen().geometry()
        size = geometry.width() * geometry.height()
        bounds = Rect(0, 0, geometry.width(), geometry.height())
        return BgraScreenshot(bounds, bytes((0, 136, 255, 255)) * size)


class StillPointer:
    def position(self) -> Point:
        return Point(10, 10)

    def move_to(self, point: Point) -> None:
        pass


class RecordingClipboard:
    def set_text(self, text: str) -> None:
        pass


class MemoryPalettes:
    location = "C:/perfil/pxls/palettes.json"

    def __init__(self, palettes: Palettes | None = None, warning: str | None = None) -> None:
        self.palettes = palettes or Palettes()
        self.warning = warning
        self.failing = False
        self.saved: list[str] = []

    def load(self) -> LoadedPalettes:
        return LoadedPalettes(self.palettes, self.warning)

    def save(self, palettes: Palettes) -> None:
        if self.failing:
            raise PalettesSaveError(self.location)
        self.saved.append(palettes.active or "")


def save_warning(location: str) -> str:
    return (
        f"No se han podido guardar las paletas en {location}; "
        "se conservan mientras pxls siga abierto."
    )


def window_with(
    qtbot: QtBot,
    palettes_store: MemoryPalettes | PalettesFile | None = None,
    history_store: HistoryFile | None = None,
) -> MainWindow:
    create_app([])
    session = PickerSession(OrangeDesktop(), StillPointer())
    window = MainWindow("0.1.0", session, RecordingClipboard(), history_store, palettes_store)
    qtbot.addWidget(window)
    window.show()
    QApplication.processEvents()
    return window


def blocked_path(tmp_path: Path) -> tuple[Path, Path]:
    """Ruta cuya carpeta es en realidad un fichero, así que no se puede escribir en ella."""
    blocker = tmp_path / "pxls"
    blocker.write_text("no es una carpeta", encoding="utf-8")
    return blocker, blocker / "palettes.json"


def create(window: MainWindow, name: str) -> None:
    window.palettes_view.ask_name = lambda parent, title, check, text="": check(name)
    window.palettes_view.new_action.trigger()


# PAL-006 · Añadir el color actual (en la ventana)


@pytest.mark.spec("PAL-006")
def test_adding_takes_the_current_colour_of_the_window(qtbot: QtBot) -> None:
    window = window_with(qtbot, MemoryPalettes(Palettes({"Web": []}, active="Web")))
    window.picker.session.set_current(GREEN)
    window.palettes_view.add_button.click()
    assert window.palettes.colors() == (GREEN,)


@pytest.mark.spec("PAL-006")
def test_the_repeated_colour_warning_reaches_the_status_bar(qtbot: QtBot) -> None:
    window = window_with(qtbot, MemoryPalettes(Palettes({"Web": [GREEN]}, active="Web")))
    window.picker.session.set_current(GREEN)
    window.palettes_view.add_button.click()
    assert window.statusBar().currentMessage() == "#00FF00FF ya está en la paleta Web"


# PAL-009 · Recuperar un color de una paleta


@pytest.mark.spec("PAL-009")
def test_choosing_a_palette_colour_makes_it_current_without_touching_the_history(
    qtbot: QtBot,
) -> None:
    window = window_with(qtbot, MemoryPalettes(Palettes({"Web": [RED, BLUE]}, active="Web")))
    window.palettes_view.swatches[1].click()
    assert window.picker.session.current == BLUE
    assert window.panel.values()["HEX"] == "#0000FFFF"
    assert window.palettes.colors() == (RED, BLUE)
    assert window.history.entries == ()


# PAL-011 · Conservar entre sesiones


@pytest.mark.spec("PAL-011")
def test_the_palettes_come_back_after_closing_and_opening(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "palettes.json"
    first = window_with(qtbot, PalettesFile(path))
    create(first, "Web")
    first.picker.session.set_current(RED)
    first.palettes_view.add_button.click()
    first.picker.session.set_current(BLUE)
    first.palettes_view.add_button.click()
    create(first, "Marca")
    first.picker.session.set_current(GREEN)
    first.palettes_view.add_button.click()
    first.close()
    second = window_with(qtbot, PalettesFile(path))
    assert second.palettes.names == ("Marca", "Web")
    assert second.palettes.active == "Marca"
    assert second.palettes.colors("Web") == (RED, BLUE)
    assert second.palettes_view.combo.currentText() == "Marca"
    assert second.palettes_view.swatches[0].color == GREEN


@pytest.mark.spec("PAL-011")
def test_the_application_keeps_the_palettes_in_appdata(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    opened: list[MainWindow] = []

    def record(application: QApplication, window: MainWindow) -> int:
        qtbot.addWidget(window)
        opened.append(window)
        return 0

    monkeypatch.setattr(app, "run", record)
    assert main(["pxls"]) == 0
    store = opened[0].palettes_store
    assert isinstance(store, PalettesFile)
    assert store.path == tmp_path / "pxls" / "palettes.json"


# PAL-012 · Fichero de las paletas dañado


@pytest.mark.spec("PAL-012")
def test_a_damaged_file_opens_without_palettes_with_a_warning_and_a_copy(
    qtbot: QtBot, tmp_path: Path
) -> None:
    path = tmp_path / "palettes.json"
    path.write_text("esto no es JSON", encoding="utf-8")
    window = window_with(qtbot, PalettesFile(path))
    copies = list(tmp_path.glob("palettes-dañado-*.json"))
    assert window.palettes.names == ()
    assert len(copies) == 1
    assert copies[0].read_text(encoding="utf-8") == "esto no es JSON"
    assert str(copies[0]) in window.statusBar().currentMessage()


@pytest.mark.spec("PAL-012", "HIST-008")
def test_both_startup_warnings_are_shown(qtbot: QtBot, tmp_path: Path) -> None:
    (tmp_path / "palettes.json").write_text("roto", encoding="utf-8")
    (tmp_path / "history.json").write_text("roto", encoding="utf-8")
    window = window_with(
        qtbot, PalettesFile(tmp_path / "palettes.json"), HistoryFile(tmp_path / "history.json")
    )
    message = window.statusBar().currentMessage()
    assert "El historial estaba dañado" in message
    assert "Las paletas estaban dañadas" in message


# PAL-013 · Fallo al guardar las paletas


@pytest.mark.spec("PAL-013")
def test_a_failed_save_keeps_the_palette_and_warns_with_the_path(
    qtbot: QtBot, tmp_path: Path
) -> None:
    _, path = blocked_path(tmp_path)
    window = window_with(qtbot, PalettesFile(path))
    create(window, "Web")
    assert window.palettes.names == ("Web",)
    assert window.statusBar().currentMessage() == save_warning(str(path))


@pytest.mark.spec("PAL-013")
def test_the_warning_is_not_repeated_while_saving_keeps_failing(qtbot: QtBot) -> None:
    store = MemoryPalettes(Palettes({"Web": []}, active="Web"))
    store.failing = True
    window = window_with(qtbot, store)
    window.palettes_view.add_button.click()
    assert window.statusBar().currentMessage() == save_warning(MemoryPalettes.location)
    window.statusBar().clearMessage()
    window.picker.session.set_current(RED)
    window.palettes_view.add_button.click()
    assert window.statusBar().currentMessage() == ""


@pytest.mark.spec("PAL-013")
def test_the_warning_comes_back_after_a_good_save(qtbot: QtBot) -> None:
    store = MemoryPalettes(Palettes({"Web": []}, active="Web"))
    store.failing = True
    window = window_with(qtbot, store)
    window.palettes_view.add_button.click()
    store.failing = False
    window.picker.session.set_current(RED)
    window.palettes_view.add_button.click()
    window.statusBar().clearMessage()
    store.failing = True
    window.picker.session.set_current(BLUE)
    window.palettes_view.add_button.click()
    assert window.statusBar().currentMessage() == save_warning(MemoryPalettes.location)


@pytest.mark.spec("PAL-013")
def test_once_saving_works_again_every_palette_is_saved(qtbot: QtBot, tmp_path: Path) -> None:
    blocker, path = blocked_path(tmp_path)
    window = window_with(qtbot, PalettesFile(path))
    create(window, "Web")
    blocker.unlink()
    window.palettes_view.add_button.click()
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["palettes"] == [{"name": "Web", "colors": ["#FFFFFFFF"]}]


# PAL-016 · Ubicación en la ventana


@pytest.mark.spec("PAL-016")
def test_the_tabs_are_history_and_palettes(qtbot: QtBot) -> None:
    window = window_with(qtbot)
    tabs = [window.tabs.tabText(index) for index in range(window.tabs.count())]
    assert tabs == ["Historial", "Paletas"]
    assert window.tabs.widget(1) is window.palettes_view


@pytest.mark.spec("PAL-016")
def test_a_full_palette_is_visible_without_scrolling(qtbot: QtBot) -> None:
    full = [Color(0, index * 10, 200) for index in range(MAX_COLORS)]
    window = window_with(qtbot, MemoryPalettes(Palettes({"Web": full}, active="Web")))
    window.tabs.setCurrentWidget(window.palettes_view)
    QApplication.processEvents()
    assert window.size().height() == 780
    assert not window.scroll_area.verticalScrollBar().isVisible()
    viewport = window.scroll_area.viewport()
    view = window.palettes_view
    widgets: list[QWidget] = [view.combo, view.menu_button, view.add_button, *view.swatches]
    for widget in widgets:
        assert widget.isVisible()
        bottom = widget.mapTo(viewport, QPoint(widget.width(), widget.height()))
        assert bottom.y() <= viewport.height()
        assert bottom.x() <= viewport.width()
