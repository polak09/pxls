import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QApplication, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.conversions import from_hsv
from pxls.core.picker import PickerSession
from pxls.core.screen import BgraScreenshot, Point, Rect
from pxls.ui.app import create_app
from pxls.ui.picker_overlay import PickerController
from pxls.ui.selector import HUE_BAR_HEIGHT, SelectorWidget


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


def selector(qtbot: QtBot, color: Color | None = None) -> SelectorWidget:
    create_app([])
    session = PickerSession(OrangeDesktop(), StillPointer())
    if color is not None:
        session.set_current(color)
    widget = SelectorWidget(session)
    qtbot.addWidget(widget)
    widget.show()
    return widget


def mouse(target: QWidget, kind: QEvent.Type, point: QPoint) -> None:
    # QTest trata QPoint(0, 0) como «sin posición» y pulsa en el centro: se envía el evento.
    position = QPointF(point)
    event = QMouseEvent(
        kind,
        position,
        target.mapToGlobal(position),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton
        if kind != QEvent.Type.MouseButtonRelease
        else Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(target, event)


def click(widget: SelectorWidget, target: str, point: QPoint) -> None:
    area = getattr(widget, target)
    mouse(area, QEvent.Type.MouseButtonPress, point)
    mouse(area, QEvent.Type.MouseButtonRelease, point)


def square_corner(widget: SelectorWidget, right: bool, bottom: bool) -> QPoint:
    square = widget.square
    return QPoint(square.width() - 1 if right else 0, square.height() - 1 if bottom else 0)


# SEL-001 · Cuadrado de saturación y valor


@pytest.mark.spec("SEL-001")
@pytest.mark.parametrize(
    ("right", "bottom", "expected"),
    [
        (True, False, "#FF0000FF"),
        (False, False, "#FFFFFFFF"),
        (True, True, "#000000FF"),
        (False, True, "#000000FF"),
    ],
)
def test_clicking_the_square_sets_saturation_and_value(
    qtbot: QtBot, right: bool, bottom: bool, expected: str
) -> None:
    widget = selector(qtbot)
    click(widget, "square", square_corner(widget, right, bottom))
    assert widget.session.current.to_hex() == expected


@pytest.mark.spec("SEL-001")
def test_clicking_the_square_keeps_the_alpha(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(255, 136, 0, 128))
    click(widget, "square", QPoint(40, 40))
    assert widget.session.current.alpha == 128


@pytest.mark.spec("SEL-001")
def test_dragging_out_of_the_square_stops_at_the_nearest_edge(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(255, 0, 0))
    square = widget.square
    mouse(square, QEvent.Type.MouseButtonPress, QPoint(50, 50))
    mouse(square, QEvent.Type.MouseMove, QPoint(-80, -80))
    mouse(square, QEvent.Type.MouseButtonRelease, QPoint(-80, -80))
    assert widget.session.current.to_hex() == "#FFFFFFFF"


# SEL-002 · Barra de tono


@pytest.mark.spec("SEL-002")
def test_hue_bar_is_vertical_with_0_on_top(qtbot: QtBot) -> None:
    widget = selector(qtbot)
    bar = widget.hue_bar
    assert bar.height() == HUE_BAR_HEIGHT > bar.width()
    assert bar.x() > widget.square.x() + widget.square.width() - 1


@pytest.mark.spec("SEL-002")
def test_clicking_hue_120_on_red_gives_green(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(255, 0, 0))
    click(widget, "hue_bar", QPoint(5, round(120 / 360 * (HUE_BAR_HEIGHT - 1))))
    assert widget.session.current.to_hex() == "#00FF00FF"


@pytest.mark.spec("SEL-002")
def test_hue_bar_keeps_saturation_and_value(qtbot: QtBot) -> None:
    widget = selector(qtbot, from_hsv(0, 50, 80))
    click(widget, "hue_bar", QPoint(5, 90))
    assert (widget.state.saturation, widget.state.value) == pytest.approx((50, 80))


# SEL-003 · Indicadores de posición


@pytest.mark.spec("SEL-003")
def test_markers_of_red_are_top_right_and_hue_0(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(255, 0, 0))
    assert widget.square.marker() == square_corner(widget, right=True, bottom=False)
    assert widget.hue_bar.marker() == 0


@pytest.mark.spec("SEL-003")
def test_markers_follow_a_captured_colour(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(255, 0, 0))
    picker = PickerController(widget.session)
    picker.start()
    for overlay in picker.overlays:
        qtbot.addWidget(overlay)
    picker.capture()
    assert widget.session.current == Color(255, 136, 0)
    assert widget.hue_bar.marker() == round(32 / 360 * (HUE_BAR_HEIGHT - 1))
    assert widget.square.marker() == square_corner(widget, right=True, bottom=False)
