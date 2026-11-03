import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui.app import create_app
from pxls.ui.main_window import MainWindow


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


def main_window(qtbot: QtBot) -> MainWindow:
    create_app([])
    window = MainWindow("0.1.0", PickerSession(OrangeDesktop(), StillPointer()))
    qtbot.addWidget(window)
    window.show()
    QApplication.processEvents()
    return window


def click(target: QWidget, point: QPoint) -> None:
    for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        position = QPointF(point)
        released = kind == QEvent.Type.MouseButtonRelease
        held = Qt.MouseButton.NoButton if released else Qt.MouseButton.LeftButton
        event = QMouseEvent(
            kind,
            position,
            target.mapToGlobal(position),
            Qt.MouseButton.LeftButton,
            held,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(target, event)


# SEL-008 · Sincronía con el color actual


@pytest.mark.spec("SEL-008")
def test_a_captured_colour_reaches_the_selector_and_its_fields(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    window.picker.start()
    for overlay in window.picker.overlays:
        qtbot.addWidget(overlay)
    window.picker.capture()
    rows = window.selector.rows
    assert [rows.field(name).value() for name in ("Rojo", "Verde", "Azul")] == [255, 136, 0]
    assert rows.field("Tono").value() == 32
    assert window.selector.hue_bar.marker() == 16


@pytest.mark.spec("SEL-008")
def test_a_change_in_the_square_reaches_the_panel(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    square = window.selector.square
    click(square, QPoint(square.width() - 1, square.height() - 1))
    assert window.panel.values()["HEX"] == "#000000FF"


# SEL-009 · Ubicación en la ventana


@pytest.mark.spec("SEL-009")
def test_everything_fits_without_scrolling_at_the_initial_size(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    assert not window.scroll_area.verticalScrollBar().isVisible()
    viewport = window.scroll_area.viewport()
    for widget in (window.selector.square, window.selector.rows, window.panel):
        bottom = widget.mapTo(viewport, QPoint(0, widget.height())).y()
        assert bottom <= viewport.height()


@pytest.mark.spec("SEL-009")
def test_the_selector_is_between_the_button_and_the_panel(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    viewport = window.scroll_area.viewport()
    button_top = window.pick_button.mapTo(viewport, QPoint(0, 0)).y()
    selector_top = window.selector.mapTo(viewport, QPoint(0, 0)).y()
    panel_top = window.panel.mapTo(viewport, QPoint(0, 0)).y()
    assert button_top < selector_top < panel_top


# APP-003 · Tamaño de la ventana (desplazamiento)


@pytest.mark.spec("APP-003")
def test_a_window_lower_than_its_content_scrolls(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    window.resize(360, 480)
    QApplication.processEvents()
    bar = window.scroll_area.verticalScrollBar()
    assert bar.isVisible()
    assert bar.maximum() > 0
