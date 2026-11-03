import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.picker import PickerSession
from pxls.core.selector import SelectorState
from pxls.ui.app import create_app
from pxls.ui.selector import COMPONENT_LABELS, SelectorWidget

ORANGE = Color(255, 136, 0)


def selector(qtbot: QtBot, color: Color) -> SelectorWidget:
    create_app([])
    session = PickerSession(None, None)  # type: ignore[arg-type]
    session.set_current(color)
    widget = SelectorWidget(session)
    qtbot.addWidget(widget)
    widget.show()
    return widget


def type_into(widget: SelectorWidget, label: str, text: str) -> None:
    field = widget.rows.field(label)
    field.selectAll()
    QTest.keyClicks(field, text)
    QTest.keyClick(field, Qt.Key.Key_Return)


def click(target: QWidget, point: QPoint) -> None:
    for kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        position = QPointF(point)
        held = (
            Qt.MouseButton.NoButton
            if kind == QEvent.Type.MouseButtonRelease
            else Qt.MouseButton.LeftButton
        )
        event = QMouseEvent(
            kind,
            position,
            target.mapToGlobal(position),
            Qt.MouseButton.LeftButton,
            held,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(target, event)


# SEL-005 · Alfa (núcleo)


@pytest.mark.spec("SEL-005")
def test_alpha_percent_sets_the_alpha_and_nothing_else() -> None:
    state = SelectorState(ORANGE)
    assert state.set_alpha_percent(50) == Color(255, 136, 0, 128)
    assert state.alpha_percent() == 50
    assert state.set_alpha_percent(120).alpha == 255


# SEL-005 · Alfa (interfaz)


@pytest.mark.spec("SEL-005")
def test_writing_50_in_alpha_gives_half_transparency(qtbot: QtBot) -> None:
    widget = selector(qtbot, ORANGE)
    type_into(widget, "Alfa", "50")
    assert widget.session.current.to_hex() == "#FF880080"


@pytest.mark.spec("SEL-005")
@pytest.mark.parametrize(("right", "alpha"), [(False, 0), (True, 255)])
def test_alpha_bar_goes_from_transparent_to_opaque_keeping_rgb(
    qtbot: QtBot, right: bool, alpha: int
) -> None:
    widget = selector(qtbot, Color(10, 20, 30, 100))
    bar = widget.rows.alpha_bar
    click(bar, QPoint(bar.width() - 1 if right else 0, bar.height() // 2))
    assert widget.session.current == Color(10, 20, 30, alpha)


@pytest.mark.spec("SEL-005")
def test_alpha_bar_is_painted_over_a_checkerboard(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(10, 20, 30, 255))
    image = widget.rows.alpha_bar.grab().toImage()
    row = image.height() // 2
    left_tiles = {image.pixelColor(x, row).name() for x in range(2, 14)}
    assert len(left_tiles) >= 2


# SEL-006 · Barra y campo por componente


@pytest.mark.spec("SEL-006")
def test_every_component_has_a_spanish_label_a_bar_and_a_field(qtbot: QtBot) -> None:
    widget = selector(qtbot, ORANGE)
    assert COMPONENT_LABELS == ("Rojo", "Verde", "Azul", "Tono", "Saturación", "Valor", "Alfa")
    labels = {label.text() for label in widget.rows.findChildren(QLabel)}
    assert set(COMPONENT_LABELS) <= labels
    for name in COMPONENT_LABELS:
        assert widget.rows.bar(name) is not None
        assert widget.rows.field(name) is not None


@pytest.mark.spec("SEL-006")
@pytest.mark.parametrize(
    ("start", "label", "text", "expected"),
    [(ORANGE, "Rojo", "0", "#008800FF"), (Color(255, 0, 0), "Tono", "240", "#0000FFFF")],
)
def test_writing_a_component_changes_only_that_component(
    qtbot: QtBot, start: Color, label: str, text: str, expected: str
) -> None:
    widget = selector(qtbot, start)
    type_into(widget, label, text)
    assert widget.session.current.to_hex() == expected


@pytest.mark.spec("SEL-006")
def test_values_out_of_range_are_limited_to_the_maximum(qtbot: QtBot) -> None:
    widget = selector(qtbot, Color(0, 136, 0))
    type_into(widget, "Rojo", "300")
    assert widget.rows.field("Rojo").value() == 255
    assert widget.session.current == Color(255, 136, 0)


@pytest.mark.spec("SEL-006")
def test_moving_a_bar_changes_the_colour_and_its_field(qtbot: QtBot) -> None:
    widget = selector(qtbot, ORANGE)
    bar = widget.rows.bar("Rojo")
    bar.setValue(0)
    assert widget.session.current.to_hex() == "#008800FF"
    assert widget.rows.field("Rojo").value() == 0


@pytest.mark.spec("SEL-006")
@pytest.mark.parametrize(
    ("label", "text"), [("Verde", "40"), ("Saturación", "30"), ("Valor", "70")]
)
def test_writing_a_field_moves_its_bar(qtbot: QtBot, label: str, text: str) -> None:
    widget = selector(qtbot, ORANGE)
    type_into(widget, label, text)
    assert widget.rows.bar(label).value() == int(text)
