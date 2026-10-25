import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.picker import INITIAL_COLOR, PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui.app import create_app
from pxls.ui.main_window import MainWindow
from pxls.ui.picker_overlay import PickerController

ORANGE, BLUE = Color(255, 136, 0), Color(0, 0, 255)


class FakeGrabber:
    def grab(self) -> BgraScreenshot:
        """Escritorio del tamaño de la pantalla de Qt: naranja, salvo el píxel (5, 5) azul."""
        geometry = QGuiApplication.primaryScreen().geometry()
        width, height = geometry.width(), geometry.height()
        pixels = bytearray(bytes((0, 136, 255, 255)) * width * height)
        offset = (5 * width + 5) * 4
        pixels[offset : offset + 4] = bytes((255, 0, 0, 255))
        return BgraScreenshot(Rect(0, 0, width, height), bytes(pixels))


class FakePointer:
    def __init__(self) -> None:
        self.point = Point(10, 10)

    def position(self) -> Point:
        return self.point

    def move_to(self, point: Point) -> None:
        self.point = point


def fake_session() -> PickerSession:
    return PickerSession(FakeGrabber(), FakePointer())


@pytest.fixture
def controller(qtbot: QtBot) -> PickerController:
    create_app([])
    picker = PickerController(fake_session())
    picker.start()
    for overlay in picker.overlays:
        qtbot.addWidget(overlay)
    return picker


def main_window(qtbot: QtBot) -> MainWindow:
    create_app([])
    window = MainWindow("0.1.0", fake_session())
    qtbot.addWidget(window)
    return window


# PICK-001 · Activar el cuentagotas


@pytest.mark.spec("PICK-001")
def test_capture_button_starts_the_picker(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    [button] = [b for b in window.findChildren(QPushButton) if b.text() == "Capturar color"]
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert window.picker.active
    window.picker.cancel()


@pytest.mark.spec("PICK-001")
def test_shortcut_starts_the_picker(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    with qtbot.waitActive(window):
        window.show()
        window.activateWindow()
    modifiers = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
    QTest.keyClick(window, Qt.Key.Key_C, modifiers)
    assert window.picker.active
    window.picker.cancel()


# PICK-002 · Qué se captura


@pytest.mark.spec("PICK-002")
def test_overlays_show_the_frozen_screen(controller: PickerController) -> None:
    image = controller.overlays[0].grab().toImage()
    assert image.pixelColor(5, 5) == QColor(0, 0, 255)
    assert image.pixelColor(300, 300) == QColor(255, 136, 0)


# PICK-004 · Capturar con un clic


@pytest.mark.spec("PICK-004")
def test_left_click_captures_and_closes_the_overlays(
    qtbot: QtBot, controller: PickerController
) -> None:
    QTest.mouseClick(
        controller.overlays[0],
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(10, 10),
    )
    assert controller.session.current == ORANGE
    assert not controller.active
    assert not any(overlay.isVisible() for overlay in controller.overlays)


# PICK-005 · Cancelar


@pytest.mark.spec("PICK-005")
def test_escape_cancels(qtbot: QtBot, controller: PickerController) -> None:
    QTest.keyClick(controller.overlays[0], Qt.Key.Key_Escape)
    assert controller.session.current == INITIAL_COLOR
    assert not controller.active


@pytest.mark.spec("PICK-005")
def test_right_click_cancels(qtbot: QtBot, controller: PickerController) -> None:
    QTest.mouseClick(
        controller.overlays[0],
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(10, 10),
    )
    assert controller.session.current == INITIAL_COLOR
    assert not controller.active


# PICK-006 · Ajuste fino con el teclado


@pytest.mark.spec("PICK-006")
def test_arrows_move_the_pointer_and_enter_captures(
    qtbot: QtBot, controller: PickerController
) -> None:
    pointer = controller.session.pointer
    pointer.move_to(Point(6, 5))
    QTest.keyClick(controller.overlays[0], Qt.Key.Key_Left)
    assert pointer.position() == Point(5, 5)
    QTest.keyClick(controller.overlays[0], Qt.Key.Key_Return)
    assert controller.session.current == BLUE
    assert not controller.active
