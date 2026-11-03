import pytest

from pxls.core.color import Color
from pxls.core.picker import INITIAL_COLOR, PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect

ORANGE, BLUE = Color(255, 136, 0), Color(0, 0, 255)
START = Point(1, 1)


def screenshot(color: Color, size: int = 4) -> BgraScreenshot:
    pixel = bytes((color.blue, color.green, color.red, 255))
    return BgraScreenshot(Rect(0, 0, size, size), pixel * size * size)


class FakeGrabber:
    def __init__(self, *shots: BgraScreenshot) -> None:
        self.shots = list(shots)
        self.grabs = 0

    def grab(self) -> BgraScreenshot:
        self.grabs += 1
        return self.shots.pop(0)


class FakePointer:
    def __init__(self, point: Point) -> None:
        self.point = point

    def position(self) -> Point:
        return self.point

    def move_to(self, point: Point) -> None:
        self.point = point


def session(*shots: BgraScreenshot, at: Point = START) -> tuple[PickerSession, FakePointer]:
    pointer = FakePointer(at)
    return PickerSession(FakeGrabber(*shots), pointer), pointer


# PICK-010 · Color actual al arrancar


@pytest.mark.spec("PICK-010")
def test_initial_colour_is_opaque_white() -> None:
    picker, _ = session()
    assert picker.current == INITIAL_COLOR == Color.from_hex("#FFFFFFFF")
    assert not picker.active


# PICK-004 · Capturar con un clic


@pytest.mark.spec("PICK-004")
def test_capture_takes_the_colour_under_the_pointer_and_ends_the_mode() -> None:
    picker, _ = session(screenshot(ORANGE))
    picker.start()
    assert picker.active
    assert picker.capture() == ORANGE
    assert picker.current == ORANGE
    assert not picker.active


@pytest.mark.spec("PICK-004")
def test_listeners_are_told_about_the_new_colour() -> None:
    picker, _ = session(screenshot(ORANGE))
    seen: list[Color] = []
    picker.on_change(seen.append)
    picker.start()
    picker.capture()
    assert seen == [ORANGE]


# PICK-005 · Cancelar


@pytest.mark.spec("PICK-005")
def test_cancel_keeps_the_current_colour_and_ends_the_mode() -> None:
    picker, _ = session(screenshot(ORANGE))
    seen: list[Color] = []
    picker.on_change(seen.append)
    picker.start()
    picker.cancel()
    assert picker.current == INITIAL_COLOR
    assert not picker.active
    assert seen == []


# PICK-002 · Qué se captura


@pytest.mark.spec("PICK-002")
def test_the_screen_is_captured_once_when_the_mode_starts() -> None:
    grabber = FakeGrabber(screenshot(ORANGE), screenshot(BLUE))
    picker = PickerSession(grabber, FakePointer(START))
    shot = picker.start()
    assert picker.screenshot is shot
    assert picker.capture() == ORANGE
    assert grabber.grabs == 1


# PICK-006 · Ajuste fino con el teclado


@pytest.mark.spec("PICK-006")
@pytest.mark.parametrize(
    ("step", "expected"),
    [
        ((1, 0), Point(101, 100)),
        ((-1, 0), Point(99, 100)),
        ((0, 1), Point(100, 101)),
        ((0, -1), Point(100, 99)),
    ],
)
def test_arrow_keys_move_the_pointer_one_physical_pixel(
    step: tuple[int, int], expected: Point
) -> None:
    picker, pointer = session(screenshot(ORANGE, 300), at=Point(100, 100))
    picker.start()
    picker.nudge(*step)
    assert pointer.position() == expected


@pytest.mark.spec("PICK-006")
def test_nudging_does_nothing_outside_the_mode() -> None:
    picker, pointer = session(at=Point(100, 100))
    picker.nudge(1, 0)
    assert pointer.position() == Point(100, 100)
