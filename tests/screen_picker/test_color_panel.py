import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui.app import create_app
from pxls.ui.color_panel import ColorPanel
from pxls.ui.main_window import MainWindow


class OrangeDesktop:
    def grab(self) -> BgraScreenshot:
        geometry = QGuiApplication.primaryScreen().geometry()
        size = geometry.width() * geometry.height()
        return BgraScreenshot(
            Rect(0, 0, geometry.width(), geometry.height()), bytes((0, 136, 255, 255)) * size
        )


class StillPointer:
    def position(self) -> Point:
        return Point(10, 10)

    def move_to(self, point: Point) -> None:
        pass


def main_window(qtbot: QtBot) -> MainWindow:
    create_app([])
    window = MainWindow("0.1.0", PickerSession(OrangeDesktop(), StillPointer()))
    qtbot.addWidget(window)
    return window


# PICK-009 · Panel del color actual


@pytest.mark.spec("PICK-009")
def test_panel_shows_the_colour_and_its_four_formats(qtbot: QtBot) -> None:
    create_app([])
    panel = ColorPanel()
    qtbot.addWidget(panel)
    panel.show_color(Color(255, 136, 0))
    assert panel.values() == {
        "HEX": "#FF8800FF",
        "RGB": "rgb(255, 136, 0)",
        "HSL": "hsl(32, 100%, 50%)",
        "HSV": "hsv(32, 100%, 100%)",
    }
    swatch = panel.swatch.grab().toImage()
    assert swatch.pixelColor(swatch.width() // 2, swatch.height() // 2) == QColor(255, 136, 0)


@pytest.mark.spec("PICK-009")
def test_panel_shows_the_captured_colour(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    window.picker.start()
    window.picker.capture()
    assert window.panel.values()["HEX"] == "#FF8800FF"


def content_rect(window: MainWindow, widget: QWidget) -> tuple[int, int, int, int]:
    """Devuelve izquierda, arriba, derecha y abajo de ``widget`` en el contenido de la ventana."""
    content = window.scroll_area.widget()
    assert content is not None
    top_left = widget.mapTo(content, QPoint(0, 0))
    return top_left.x(), top_left.y(), top_left.x() + widget.width(), top_left.y() + widget.height()


@pytest.mark.spec("PICK-009")
def test_the_swatch_fills_the_space_right_of_the_hue_bar(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    window.show()
    QApplication.processEvents()
    swatch = content_rect(window, window.panel.swatch)
    hue_bar = content_rect(window, window.selector.hue_bar)
    button = content_rect(window, window.pick_button)
    assert swatch[0] > hue_bar[2]
    assert (swatch[1], swatch[3]) == (hue_bar[1], hue_bar[3])
    assert swatch[2] == button[2]


@pytest.mark.spec("PICK-009")
def test_the_swatch_follows_the_current_colour_in_the_window(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    window.show()
    window.picker.session.set_current(Color(255, 136, 0))
    image = window.panel.swatch.grab().toImage()
    assert image.pixelColor(image.width() // 2, image.height() // 2) == QColor(255, 136, 0)


# PICK-010 · Color actual al arrancar


@pytest.mark.spec("PICK-010")
def test_panel_starts_with_opaque_white(qtbot: QtBot) -> None:
    window = main_window(qtbot)
    assert window.panel.values()["HEX"] == "#FFFFFFFF"
