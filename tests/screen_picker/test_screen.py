import pytest

from pxls.core.color import Color
from pxls.core.screen import BgraScreenshot, Point, Rect

BLACK, WHITE = Color(0, 0, 0), Color(255, 255, 255)


def bgra(*colors: Color) -> bytes:
    return b"".join(bytes((c.blue, c.green, c.red, 255)) for c in colors)


# PICK-007 · Varias pantallas


@pytest.mark.spec("PICK-007")
def test_screenshot_with_a_screen_to_the_left_uses_negative_coordinates() -> None:
    # Escritorio de 4 por 1 píxeles: dos a la izquierda de la pantalla principal (x < 0).
    pixels = bgra(Color(1, 0, 0), Color(2, 0, 0), Color(3, 0, 0), Color(4, 0, 0))
    shot = BgraScreenshot(Rect(-2, 0, 4, 1), pixels)
    assert shot.color_at(Point(-2, 0)) == Color(1, 0, 0)
    assert shot.color_at(Point(-1, 0)) == Color(2, 0, 0)
    assert shot.color_at(Point(1, 0)) == Color(4, 0, 0)


@pytest.mark.spec("PICK-007")
@pytest.mark.parametrize("point", [Point(-3, 0), Point(2, 0), Point(0, 1), Point(0, -1)])
def test_points_outside_the_desktop_have_no_color(point: Point) -> None:
    shot = BgraScreenshot(Rect(-2, 0, 4, 1), bgra(BLACK, BLACK, BLACK, BLACK))
    assert shot.color_at(point) is None


@pytest.mark.spec("PICK-007")
def test_rect_knows_which_points_it_contains() -> None:
    rect = Rect(-1920, -200, 1920, 1080)
    assert rect.contains(Point(-1920, -200))
    assert rect.contains(Point(-1, 879))
    assert not rect.contains(Point(0, 0))
    assert (rect.right, rect.bottom) == (0, 880)


# PICK-008 · Escalado de pantalla


@pytest.mark.spec("PICK-008")
def test_alternating_pixels_are_read_exactly_without_blending() -> None:
    width, height = 6, 4
    pattern = [BLACK if (x + y) % 2 else WHITE for y in range(height) for x in range(width)]
    shot = BgraScreenshot(Rect(0, 0, width, height), bgra(*pattern))
    read = [shot.color_at(Point(x, y)) for y in range(height) for x in range(width)]
    assert read == pattern


@pytest.mark.spec("PICK-008")
def test_screenshot_rejects_a_buffer_of_the_wrong_size() -> None:
    with pytest.raises(ValueError, match="bytes"):
        BgraScreenshot(Rect(0, 0, 2, 2), bgra(BLACK))


# PICK-002 · Qué se captura


@pytest.mark.spec("PICK-002")
def test_screenshot_keeps_its_own_copy_of_the_pixels() -> None:
    source = bytearray(bgra(WHITE))
    shot = BgraScreenshot(Rect(0, 0, 1, 1), bytes(source))
    source[:3] = b"\x00\x00\x00"
    assert shot.color_at(Point(0, 0)) == WHITE


@pytest.mark.spec("PICK-002")
def test_captured_pixels_are_opaque() -> None:
    shot = BgraScreenshot(Rect(0, 0, 1, 1), bytes((10, 20, 30, 0)))
    assert shot.color_at(Point(0, 0)) == Color(30, 20, 10, 255)
