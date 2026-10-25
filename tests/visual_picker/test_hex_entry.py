import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.picker import PickerSession
from pxls.ui.app import create_app
from pxls.ui.main_window import MainWindow

ORANGE = Color(255, 136, 0)


def window_with(qtbot: QtBot, color: Color) -> MainWindow:
    create_app([])
    session = PickerSession(None, None)  # type: ignore[arg-type]
    session.set_current(color)
    window = MainWindow("0.1.0", session)
    qtbot.addWidget(window)
    window.show()
    return window


def enter_hex(window: MainWindow, text: str) -> None:
    field = window.panel.hex_field
    field.selectAll()
    QTest.keyClicks(field, text)
    QTest.keyClick(field, Qt.Key.Key_Return)


# SEL-007 · Escribir el color en HEX


@pytest.mark.spec("SEL-007")
def test_a_valid_hex_becomes_the_current_colour(qtbot: QtBot) -> None:
    window = window_with(qtbot, ORANGE)
    enter_hex(window, "#3a86ff")
    assert window.picker.session.current.to_hex() == "#3A86FFFF"
    assert window.panel.values()["HEX"] == "#3A86FFFF"
    assert window.selector.rows.field("Azul").value() == 255


@pytest.mark.spec("SEL-007")
def test_an_invalid_hex_keeps_the_colour_and_explains_why(qtbot: QtBot) -> None:
    window = window_with(qtbot, ORANGE)
    enter_hex(window, "#GG0000")
    assert window.picker.session.current == ORANGE
    assert window.panel.error.isVisible()
    assert "`G` no es un dígito hexadecimal" in window.panel.error.text()


@pytest.mark.spec("SEL-007")
def test_a_valid_hex_after_an_error_hides_the_error(qtbot: QtBot) -> None:
    window = window_with(qtbot, ORANGE)
    enter_hex(window, "#12345")
    assert window.panel.error.isVisible()
    enter_hex(window, "#00FF00")
    assert not window.panel.error.isVisible()
    assert window.picker.session.current == Color(0, 255, 0)
