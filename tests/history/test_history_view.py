from collections.abc import Callable

import pytest
from PySide6.QtCore import QPoint, QTimer
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.history import LIMIT, History
from pxls.ui.app import create_app
from pxls.ui.history_view import COLUMNS, SWATCH_SIZE, HistoryView, ask_to_clear

RED = Color(255, 0, 0)
BLUE = Color(0, 0, 255)


def view_of(qtbot: QtBot, history: History) -> HistoryView:
    create_app([])
    view = HistoryView(history)
    qtbot.addWidget(view)
    view.show()
    return view


def answer(reply: bool) -> Callable[[QWidget], bool]:
    def confirm(parent: QWidget) -> bool:
        return reply

    return confirm


# HIST-002 · Orden


@pytest.mark.spec("HIST-002")
def test_the_swatches_follow_the_order_of_the_history(qtbot: QtBot) -> None:
    history = History()
    view = view_of(qtbot, history)
    history.add(RED)
    history.add(BLUE)
    assert [swatch.color for swatch in view.swatches[:3]] == [BLUE, RED, None]


# HIST-005 · Recuperar un color


@pytest.mark.spec("HIST-005")
def test_clicking_a_swatch_chooses_its_colour(qtbot: QtBot) -> None:
    view = view_of(qtbot, History([BLUE, RED]))
    with qtbot.waitSignal(view.color_chosen) as chosen:
        view.swatches[1].click()
    assert chosen.args == [RED]


@pytest.mark.spec("HIST-005")
def test_the_tooltip_of_a_swatch_is_its_hex(qtbot: QtBot) -> None:
    view = view_of(qtbot, History([BLUE, RED]))
    assert [swatch.toolTip() for swatch in view.swatches[:3]] == ["#0000FFFF", "#FF0000FF", ""]


@pytest.mark.spec("HIST-005")
def test_an_empty_swatch_cannot_be_clicked(qtbot: QtBot) -> None:
    view = view_of(qtbot, History([BLUE]))
    assert view.swatches[0].isEnabled()
    assert not view.swatches[1].isEnabled()


# HIST-006 · Quitar y vaciar


@pytest.mark.spec("HIST-006")
def test_right_clicking_a_swatch_offers_to_remove_it(qtbot: QtBot) -> None:
    history = History([BLUE, RED])
    view = view_of(qtbot, history)
    offered: list[list[str]] = []

    def choose() -> None:
        menu = QApplication.activePopupWidget()
        assert isinstance(menu, QMenu)
        offered.append([action.text() for action in menu.actions()])
        menu.actions()[0].trigger()
        menu.close()

    swatch = view.swatches[0]
    QTimer.singleShot(0, choose)
    point = QPoint(SWATCH_SIZE // 2, SWATCH_SIZE // 2)
    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, point, swatch.mapToGlobal(point))
    QApplication.sendEvent(swatch, event)
    assert offered == [["Quitar del historial"]]
    assert history.entries == (RED,)


@pytest.mark.spec("HIST-006")
def test_clearing_and_confirming_empties_the_history(qtbot: QtBot) -> None:
    history = History([BLUE, RED])
    view = view_of(qtbot, history)
    view.confirm = answer(True)
    view.clear_button.click()
    assert history.entries == ()
    assert [swatch.color for swatch in view.swatches] == [None] * LIMIT


@pytest.mark.spec("HIST-006")
def test_clearing_and_cancelling_keeps_the_history(qtbot: QtBot) -> None:
    history = History([BLUE, RED])
    view = view_of(qtbot, history)
    view.confirm = answer(False)
    view.clear_button.click()
    assert history.entries == (BLUE, RED)


@pytest.mark.spec("HIST-006")
def test_the_clear_button_is_disabled_when_there_is_nothing_to_clear(qtbot: QtBot) -> None:
    history = History([BLUE])
    view = view_of(qtbot, history)
    assert view.clear_button.isEnabled()
    history.clear()
    assert not view.clear_button.isEnabled()


@pytest.mark.spec("HIST-006", "APP-006")
def test_the_confirmation_asks_in_spanish_and_cancels_with_no(qtbot: QtBot) -> None:
    create_app([])
    parent = QWidget()
    qtbot.addWidget(parent)
    seen: list[set[str]] = []

    def reply_no() -> None:
        box = QApplication.activeModalWidget()
        assert isinstance(box, QMessageBox)
        seen.append({box.windowTitle(), box.text()})
        seen.append({button.text() for button in box.buttons()})
        no = box.button(QMessageBox.StandardButton.No)
        assert box.defaultButton() is no
        no.click()

    QTimer.singleShot(0, reply_no)
    assert ask_to_clear(parent) is False
    assert seen == [
        {"Vaciar historial", "¿Vaciar el historial? No se puede deshacer."},
        {"&Sí", "&No"},
    ]


# HIST-009 · Ubicación en la ventana


@pytest.mark.spec("HIST-009")
def test_the_grid_has_two_rows_of_ten_swatches_of_24_px(qtbot: QtBot) -> None:
    view = view_of(qtbot, History())
    assert COLUMNS == 10
    assert len(view.swatches) == LIMIT
    assert {(swatch.width(), swatch.height()) for swatch in view.swatches} == {(24, 24)}
    tops = sorted({swatch.y() for swatch in view.swatches})
    assert len(tops) == 2
    assert [swatch.y() for swatch in view.swatches[:COLUMNS]] == [tops[0]] * COLUMNS
    lefts = [swatch.x() for swatch in view.swatches[:COLUMNS]]
    assert lefts == sorted(lefts)
