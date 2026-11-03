import pytest
from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QGuiApplication
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.magnifier import LENS_PIXELS, ZOOM, lens_origin, neighbourhood
from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui.app import create_app
from pxls.ui.picker_overlay import PickerController

ORANGE, BLUE = Color(255, 136, 0), Color(0, 0, 255)


def desktop(width: int, height: int, blue_at: Point) -> BgraScreenshot:
    """Escritorio naranja con un único píxel azul."""
    pixels = bytearray(bytes((0, 136, 255, 255)) * width * height)
    offset = (blue_at.y * width + blue_at.x) * 4
    pixels[offset : offset + 4] = bytes((255, 0, 0, 255))
    return BgraScreenshot(Rect(0, 0, width, height), bytes(pixels))


# PICK-003 · Lupa (núcleo)


@pytest.mark.spec("PICK-003")
def test_lens_shows_11_by_11_pixels_around_the_cursor() -> None:
    cells = neighbourhood(desktop(40, 40, Point(20, 20)), Point(20, 20))
    assert (LENS_PIXELS, ZOOM) == (11, 10)
    assert len(cells) == 11
    assert all(len(row) == 11 for row in cells)
    assert cells[5][5] == BLUE
    assert {color for row in cells for color in row} == {ORANGE, BLUE}


@pytest.mark.spec("PICK-003")
def test_cells_outside_the_desktop_are_empty() -> None:
    cells = neighbourhood(desktop(40, 40, Point(0, 0)), Point(0, 0))
    assert cells[5][5] == BLUE
    assert cells[0][0] is None
    assert cells[5][4] is None
    assert cells[5][6] == ORANGE


@pytest.mark.spec("PICK-003")
def test_lens_goes_below_and_to_the_right_when_it_fits() -> None:
    screen = Rect(0, 0, 1000, 800)
    origin = lens_origin(Point(100, 100), 110, 132, screen)
    assert origin.x > 100
    assert origin.y > 100


@pytest.mark.spec("PICK-003")
@pytest.mark.parametrize("cursor", [Point(995, 400), Point(400, 795), Point(995, 795)])
def test_lens_moves_to_the_other_side_when_it_does_not_fit(cursor: Point) -> None:
    screen = Rect(0, 0, 1000, 800)
    origin = lens_origin(cursor, 110, 132, screen)
    assert screen.contains(origin)
    assert screen.contains(Point(origin.x + 109, origin.y + 131))


# PICK-003 · Lupa (interfaz)


class FixedPointer:
    def __init__(self, point: Point) -> None:
        self.point = point

    def position(self) -> Point:
        return self.point

    def move_to(self, point: Point) -> None:
        self.point = point


class OneShot:
    def __init__(self, shot: BgraScreenshot) -> None:
        self.shot = shot

    def grab(self) -> BgraScreenshot:
        return self.shot


def overlay_with_cursor_at(qtbot: QtBot, cursor: Point) -> PickerController:
    create_app([])
    geometry = QGuiApplication.primaryScreen().geometry()
    shot = desktop(geometry.width(), geometry.height(), cursor)
    controller = PickerController(PickerSession(OneShot(shot), FixedPointer(cursor)))
    controller.start()
    for overlay in controller.overlays:
        qtbot.addWidget(overlay)
    return controller


@pytest.mark.spec("PICK-003")
def test_lens_centre_has_the_pixel_colour_highlighted_and_its_hex(qtbot: QtBot) -> None:
    controller = overlay_with_cursor_at(qtbot, Point(200, 150))
    overlay = controller.overlays[0]
    lens = overlay.lens_rect()
    assert lens is not None
    image = overlay.grab().toImage()
    centre_x = lens.x() + 5 * ZOOM + ZOOM // 2
    centre_y = lens.y() + 5 * ZOOM + ZOOM // 2
    assert image.pixelColor(centre_x, centre_y) == QColor(0, 0, 255)
    assert image.pixelColor(lens.x() + ZOOM // 2, lens.y() + ZOOM // 2) == QColor(255, 136, 0)
    border = image.pixelColor(lens.x() + 5 * ZOOM, centre_y)
    assert border not in (QColor(0, 0, 255), QColor(255, 136, 0))
    assert overlay.lens_hex() == "#0000FFFF"
    controller.cancel()


@pytest.mark.spec("PICK-003")
def test_lens_next_to_the_right_edge_stays_inside_the_screen(qtbot: QtBot) -> None:
    geometry = QGuiApplication.primaryScreen().geometry()
    controller = overlay_with_cursor_at(qtbot, Point(geometry.width() - 3, 100))
    overlay = controller.overlays[0]
    lens = overlay.lens_rect()
    assert lens is not None
    assert QRect(0, 0, geometry.width(), geometry.height()).contains(lens)
    controller.cancel()
