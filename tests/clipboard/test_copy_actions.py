import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from pxls.core.clipboard import ClipboardError
from pxls.core.color import Color
from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui.app import create_app
from pxls.ui.main_window import MainWindow

ORANGE = Color(255, 136, 0)


class RecordingClipboard:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def set_text(self, text: str) -> None:
        self.texts.append(text)


class LockedClipboard:
    def set_text(self, text: str) -> None:
        raise ClipboardError("otra aplicación tiene el portapapeles bloqueado")


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


def window_with(
    qtbot: QtBot, color: Color, clipboard: RecordingClipboard | LockedClipboard
) -> MainWindow:
    create_app([])
    session = PickerSession(OrangeDesktop(), StillPointer())
    session.set_current(color)
    window = MainWindow("0.1.0", session, clipboard)
    qtbot.addWidget(window)
    with qtbot.waitActive(window):
        window.show()
        window.activateWindow()
    return window


def copy_button(window: MainWindow, format_name: str) -> QPushButton:
    return window.panel.copy_buttons[format_name]


def ctrl_c(target: object) -> None:
    QTest.keyClick(target, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)  # type: ignore[call-overload]


# CLIP-001 · Copiar en un formato


@pytest.mark.spec("CLIP-001")
def test_every_format_has_a_copy_button_in_spanish(qtbot: QtBot) -> None:
    window = window_with(qtbot, ORANGE, RecordingClipboard())
    buttons = window.panel.copy_buttons
    assert list(buttons) == ["HEX", "RGB", "HSL", "HSV"]
    assert {button.text() for button in buttons.values()} == {"Copiar"}


@pytest.mark.spec("CLIP-001")
def test_copy_button_copies_exactly_the_text_of_its_format(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, ORANGE, clipboard)
    QTest.mouseClick(copy_button(window, "RGB"), Qt.MouseButton.LeftButton)
    assert clipboard.texts == ["rgb(255, 136, 0)"]


@pytest.mark.spec("CLIP-001")
def test_each_copy_button_copies_what_the_panel_shows(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, Color(255, 136, 0, 128), clipboard)
    for name in ("HEX", "RGB", "HSL", "HSV"):
        QTest.mouseClick(copy_button(window, name), Qt.MouseButton.LeftButton)
    assert clipboard.texts == [window.panel.values()[name] for name in ("HEX", "RGB", "HSL", "HSV")]


# CLIP-002 · Atajo de teclado


@pytest.mark.spec("CLIP-002")
def test_ctrl_c_outside_text_fields_copies_the_hex(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, Color(58, 134, 255), clipboard)
    square = window.selector.square
    square.setFocus()
    ctrl_c(square)
    assert clipboard.texts == ["#3A86FFFF"]


@pytest.mark.spec("CLIP-002")
def test_ctrl_c_in_a_text_field_copies_the_selected_text(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, Color(58, 134, 255), clipboard)
    field = window.panel.hex_field
    field.setFocus()
    field.setSelection(3, 4)
    assert field.selectedText() == "86FF"
    ctrl_c(field)
    assert QGuiApplication.clipboard().text() == "86FF"
    assert clipboard.texts == []


# CLIP-003 · Confirmación


@pytest.mark.spec("CLIP-003")
def test_copying_shows_a_confirmation_for_2_seconds(qtbot: QtBot) -> None:
    window = window_with(qtbot, ORANGE, RecordingClipboard())
    QTest.mouseClick(copy_button(window, "HEX"), Qt.MouseButton.LeftButton)
    bar = window.statusBar()
    assert bar.currentMessage() == "Copiado: #FF8800FF"
    QTest.qWait(1500)
    assert bar.currentMessage() == "Copiado: #FF8800FF"
    qtbot.waitUntil(lambda: bar.currentMessage() == "", timeout=1500)


# CLIP-004 · Copiar al capturar


@pytest.mark.spec("CLIP-004")
def test_capturing_with_the_eyedropper_leaves_the_clipboard_alone(qtbot: QtBot) -> None:
    clipboard = RecordingClipboard()
    window = window_with(qtbot, Color(1, 2, 3), clipboard)
    window.picker.start()
    for overlay in window.picker.overlays:
        qtbot.addWidget(overlay)
    window.picker.capture()
    assert window.picker.session.current == ORANGE
    assert clipboard.texts == []


# CLIP-005 · Portapapeles no disponible


@pytest.mark.spec("CLIP-005")
def test_a_locked_clipboard_is_reported_and_the_colour_kept(qtbot: QtBot) -> None:
    window = window_with(qtbot, ORANGE, LockedClipboard())
    QTest.mouseClick(copy_button(window, "HEX"), Qt.MouseButton.LeftButton)
    assert window.statusBar().currentMessage().startswith("No se ha podido copiar")
    assert window.picker.session.current == ORANGE
