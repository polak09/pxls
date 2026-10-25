import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from pxls.adapters.history_file import HistoryFile
from pxls.core.clipboard import ClipboardError
from pxls.core.color import Color
from pxls.core.history import LIMIT, HistorySaveError, LoadedHistory
from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui import app
from pxls.ui.app import create_app, main
from pxls.ui.main_window import MainWindow

ORANGE = Color(255, 136, 0)
RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
INSIDE = Point(10, 10)


class OrangeDesktop:
    def grab(self) -> BgraScreenshot:
        geometry = QGuiApplication.primaryScreen().geometry()
        size = geometry.width() * geometry.height()
        bounds = Rect(0, 0, geometry.width(), geometry.height())
        return BgraScreenshot(bounds, bytes((0, 136, 255, 255)) * size)


class StillPointer:
    def __init__(self, point: Point = INSIDE) -> None:
        self.point = point

    def position(self) -> Point:
        return self.point

    def move_to(self, point: Point) -> None:
        self.point = point


class RecordingClipboard:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def set_text(self, text: str) -> None:
        self.texts.append(text)


class LockedClipboard:
    def set_text(self, text: str) -> None:
        raise ClipboardError("otra aplicación tiene el portapapeles bloqueado")


class MemoryStore:
    def __init__(self, colors: Sequence[Color] = (), warning: str | None = None) -> None:
        self.colors = tuple(colors)
        self.warning = warning
        self.saved: list[tuple[Color, ...]] = []

    def load(self) -> LoadedHistory:
        return LoadedHistory(self.colors, self.warning)

    def save(self, colors: Sequence[Color]) -> None:
        self.saved.append(tuple(colors))


class FlakyStore(MemoryStore):
    location = "C:/perfil/pxls/history.json"

    def __init__(self) -> None:
        super().__init__()
        self.failing = True

    def save(self, colors: Sequence[Color]) -> None:
        if self.failing:
            raise HistorySaveError(self.location)
        super().save(colors)


def save_warning(location: str) -> str:
    return (
        f"No se ha podido guardar el historial en {location}; "
        "se conserva mientras pxls siga abierto."
    )


def blocked_path(tmp_path: Path) -> tuple[Path, Path]:
    """Ruta cuya carpeta es en realidad un fichero, así que no se puede escribir en ella."""
    blocker = tmp_path / "pxls"
    blocker.write_text("no es una carpeta", encoding="utf-8")
    return blocker, blocker / "history.json"


def window_with(
    qtbot: QtBot,
    store: MemoryStore | HistoryFile | None = None,
    clipboard: RecordingClipboard | LockedClipboard | None = None,
    pointer: StillPointer | None = None,
) -> MainWindow:
    create_app([])
    session = PickerSession(OrangeDesktop(), pointer or StillPointer())
    window = MainWindow("0.1.0", session, clipboard or RecordingClipboard(), store)
    qtbot.addWidget(window)
    window.show()
    QApplication.processEvents()
    return window


def capture(qtbot: QtBot, window: MainWindow) -> None:
    window.picker.start()
    for overlay in window.picker.overlays:
        qtbot.addWidget(overlay)
    window.picker.capture()


def enter_hex(window: MainWindow, text: str) -> None:
    window.panel.hex_field.setText(text)
    QTest.keyClick(window.panel.hex_field, Qt.Key.Key_Return)


def drag(target: QWidget, start: QPoint, end: QPoint) -> None:
    steps = [
        (QEvent.Type.MouseButtonPress, start, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseMove, end, Qt.MouseButton.LeftButton),
        (QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.NoButton),
    ]
    for kind, point, held in steps:
        position = QPointF(point)
        button = (
            Qt.MouseButton.NoButton if kind == QEvent.Type.MouseMove else Qt.MouseButton.LeftButton
        )
        event = QMouseEvent(
            kind,
            position,
            target.mapToGlobal(position),
            button,
            held,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(target, event)


# HIST-001 · Qué entra en el historial


@pytest.mark.spec("HIST-001")
def test_a_captured_colour_enters_the_history(qtbot: QtBot) -> None:
    window = window_with(qtbot)
    capture(qtbot, window)
    assert window.history.entries == (ORANGE,)


@pytest.mark.spec("HIST-001")
def test_capturing_outside_every_screen_adds_nothing(qtbot: QtBot) -> None:
    window = window_with(qtbot, pointer=StillPointer(Point(-100_000, -100_000)))
    capture(qtbot, window)
    assert window.history.entries == ()


@pytest.mark.spec("HIST-001")
def test_dragging_in_the_selector_without_copying_adds_nothing(qtbot: QtBot) -> None:
    window = window_with(qtbot)
    square = window.selector.square
    drag(square, QPoint(10, 10), QPoint(square.width() - 10, square.height() - 10))
    assert window.picker.session.current != Color(255, 255, 255)
    assert window.history.entries == ()


@pytest.mark.spec("HIST-001")
def test_a_confirmed_hex_copied_afterwards_enters_only_once(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, clipboard=clipboard)
    enter_hex(window, "#3A86FF")
    window.copy("RGB")
    assert clipboard.texts == ["rgb(58, 134, 255)"]
    assert window.history.entries == (Color(0x3A, 0x86, 0xFF),)


@pytest.mark.spec("HIST-001")
def test_a_copied_colour_enters_the_history(qtbot: QtBot) -> None:
    window = window_with(qtbot)
    window.copy("HEX")
    assert window.history.entries == (Color(255, 255, 255),)


@pytest.mark.spec("HIST-001")
def test_a_copy_that_fails_adds_nothing(qtbot: QtBot) -> None:
    window = window_with(qtbot, clipboard=LockedClipboard())
    window.copy("HEX")
    assert window.history.entries == ()


@pytest.mark.spec("HIST-001")
def test_an_invalid_hex_adds_nothing(qtbot: QtBot) -> None:
    window = window_with(qtbot)
    enter_hex(window, "#GG0000")
    assert window.history.entries == ()


# HIST-005 · Recuperar un color


@pytest.mark.spec("HIST-005")
def test_choosing_an_entry_makes_it_current_without_reordering(qtbot: QtBot) -> None:
    window = window_with(qtbot, MemoryStore([BLUE, RED]))
    window.history_view.swatches[1].click()
    assert window.picker.session.current == RED
    assert window.panel.values()["HEX"] == "#FF0000FF"
    assert window.history.entries == (BLUE, RED)


# HIST-007 · Conservar entre sesiones


@pytest.mark.spec("HIST-007")
def test_every_change_is_saved(qtbot: QtBot) -> None:
    store = MemoryStore()
    window = window_with(qtbot, store)
    enter_hex(window, "#FF0000")
    enter_hex(window, "#0000FF")
    assert store.saved == [(RED,), (BLUE, RED)]


@pytest.mark.spec("HIST-007")
def test_the_history_comes_back_after_closing_and_opening(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    first = window_with(qtbot, HistoryFile(path))
    enter_hex(first, "#FF0000")
    enter_hex(first, "#0000FF")
    first.close()
    second = window_with(qtbot, HistoryFile(path))
    assert second.history.entries == (BLUE, RED)
    assert [swatch.color for swatch in second.history_view.swatches[:2]] == [BLUE, RED]


@pytest.mark.spec("HIST-007")
def test_a_first_start_has_an_empty_history(qtbot: QtBot, tmp_path: Path) -> None:
    window = window_with(qtbot, HistoryFile(tmp_path / "history.json"))
    assert window.history.entries == ()


@pytest.mark.spec("HIST-007")
def test_the_application_keeps_the_history_in_appdata(
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
    store = opened[0].history_store
    assert isinstance(store, HistoryFile)
    assert store.path == tmp_path / "pxls" / "history.json"


# HIST-008 · Fichero del historial dañado


@pytest.mark.spec("HIST-008")
def test_a_damaged_file_opens_empty_with_a_warning_and_a_copy(qtbot: QtBot, tmp_path: Path) -> None:
    path = tmp_path / "history.json"
    path.write_text("esto no es JSON", encoding="utf-8")
    window = window_with(qtbot, HistoryFile(path))
    copies = list(tmp_path.glob("history-dañado-*.json"))
    assert window.history.entries == ()
    assert len(copies) == 1
    assert copies[0].read_text(encoding="utf-8") == "esto no es JSON"
    assert str(copies[0]) in window.statusBar().currentMessage()


# HIST-009 · Ubicación en la ventana


@pytest.mark.spec("HIST-009")
def test_a_full_history_is_visible_without_scrolling(qtbot: QtBot) -> None:
    full = [Color(index * 10, 0, 0) for index in range(LIMIT)]
    window = window_with(qtbot, MemoryStore(full))
    assert window.size().height() == 780
    assert not window.scroll_area.verticalScrollBar().isVisible()
    viewport = window.scroll_area.viewport()
    for swatch in window.history_view.swatches:
        assert swatch.isVisible()
        bottom = swatch.mapTo(viewport, QPoint(0, swatch.height())).y()
        assert bottom <= viewport.height()


@pytest.mark.spec("HIST-009")
def test_the_history_tab_is_below_the_colour_panel(qtbot: QtBot) -> None:
    window = window_with(qtbot)
    viewport = window.scroll_area.viewport()
    panel_bottom = window.panel.mapTo(viewport, QPoint(0, window.panel.height())).y()
    tabs_top = window.tabs.mapTo(viewport, QPoint(0, 0)).y()
    assert panel_bottom <= tabs_top
    assert [window.tabs.tabText(index) for index in range(window.tabs.count())] == ["Historial"]
    assert window.tabs.currentWidget() is window.history_view


# HIST-010 · Fallo al guardar el historial


@pytest.mark.spec("HIST-010")
def test_a_failed_save_keeps_the_history_and_warns_with_the_path(
    qtbot: QtBot, tmp_path: Path
) -> None:
    _, path = blocked_path(tmp_path)
    window = window_with(qtbot, HistoryFile(path))
    enter_hex(window, "#FF0000")
    assert window.history.entries == (RED,)
    assert window.statusBar().currentMessage() == save_warning(str(path))


@pytest.mark.spec("HIST-010")
def test_the_warning_is_not_repeated_while_saving_keeps_failing(qtbot: QtBot) -> None:
    window = window_with(qtbot, FlakyStore())
    enter_hex(window, "#FF0000")
    window.statusBar().clearMessage()
    enter_hex(window, "#0000FF")
    assert window.history.entries == (BLUE, RED)
    assert window.statusBar().currentMessage() == ""


@pytest.mark.spec("HIST-010")
def test_the_warning_comes_back_after_a_good_save(qtbot: QtBot) -> None:
    store = FlakyStore()
    window = window_with(qtbot, store)
    enter_hex(window, "#FF0000")
    store.failing = False
    enter_hex(window, "#0000FF")
    window.statusBar().clearMessage()
    store.failing = True
    enter_hex(window, "#00FF00")
    assert window.history.entries[0] == GREEN
    assert window.statusBar().currentMessage() == save_warning(FlakyStore.location)


@pytest.mark.spec("HIST-010")
def test_the_warning_replaces_the_copy_confirmation(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, FlakyStore(), clipboard)
    window.copy("HEX")
    assert clipboard.texts == ["#FFFFFFFF"]
    assert window.statusBar().currentMessage() == save_warning(FlakyStore.location)


@pytest.mark.spec("HIST-010")
def test_once_saving_works_again_the_whole_history_is_saved(qtbot: QtBot, tmp_path: Path) -> None:
    blocker, path = blocked_path(tmp_path)
    window = window_with(qtbot, HistoryFile(path))
    enter_hex(window, "#FF0000")
    blocker.unlink()
    enter_hex(window, "#0000FF")
    assert json.loads(path.read_text(encoding="utf-8"))["colors"] == ["#0000FFFF", "#FF0000FF"]
