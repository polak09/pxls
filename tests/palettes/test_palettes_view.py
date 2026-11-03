from collections.abc import Callable
from functools import partial

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PySide6.QtGui import QContextMenuEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QMenu, QMessageBox, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.color import Color
from pxls.core.palettes import MAX_COLORS, Palettes
from pxls.ui.app import create_app
from pxls.ui.palettes_view import (
    NOTICE_MS,
    NameDialog,
    PalettesView,
    PaletteSwatch,
    ask_name,
    ask_to_delete,
)
from pxls.ui.swatch import COLUMNS, SWATCH_SIZE

RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
CENTER = QPoint(SWATCH_SIZE // 2, SWATCH_SIZE // 2)


def numbered(count: int) -> list[Color]:
    return [Color(index, 0, 0) for index in range(count)]


def view_of(qtbot: QtBot, palettes: Palettes, current: Color = BLUE) -> PalettesView:
    create_app([])
    view = PalettesView(palettes, lambda: current)
    qtbot.addWidget(view)
    view.show()
    QApplication.processEvents()
    return view


def replying(
    answer: str | None, asked: list[tuple[str, str]] | None = None
) -> Callable[..., str | None]:
    def ask(parent: QWidget, title: str, check: Callable[[str], str], text: str = "") -> str | None:
        if asked is not None:
            asked.append((title, text))
        return None if answer is None else check(answer)

    return ask


def confirming(reply: bool) -> Callable[[QWidget, str], bool]:
    def confirm(parent: QWidget, name: str) -> bool:
        return reply

    return confirm


def shown(view: PalettesView) -> list[Color | None]:
    return [swatch.color for swatch in view.swatches]


def send_mouse(target: QWidget, kind: QEvent.Type, point: QPoint, held: Qt.MouseButton) -> None:
    position = QPointF(point)
    event = QMouseEvent(
        kind,
        position,
        target.mapToGlobal(position),
        Qt.MouseButton.LeftButton if kind != QEvent.Type.MouseMove else Qt.MouseButton.NoButton,
        held,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(target, event)


def drag(source: PaletteSwatch, target: QWidget) -> None:
    end = source.mapFromGlobal(target.mapToGlobal(CENTER))
    left = Qt.MouseButton.LeftButton
    send_mouse(source, QEvent.Type.MouseButtonPress, CENTER, left)
    send_mouse(source, QEvent.Type.MouseMove, end, left)
    send_mouse(source, QEvent.Type.MouseButtonRelease, end, Qt.MouseButton.NoButton)


def menu_texts(menu: QMenu) -> dict[str, bool]:
    return {action.text(): action.isEnabled() for action in menu.actions()}


def trigger(menu: QMenu, text: str) -> None:
    next(action for action in menu.actions() if action.text() == text).trigger()


# PAL-001 · Crear una paleta


@pytest.mark.spec("PAL-001")
def test_a_new_palette_is_created_empty_and_active(qtbot: QtBot) -> None:
    palettes = Palettes()
    view = view_of(qtbot, palettes)
    asked: list[tuple[str, str]] = []
    view.ask_name = replying("Web", asked)
    view.new_action.trigger()
    assert asked == [("Nueva paleta", "")]
    assert palettes.names == ("Web",)
    assert palettes.active == "Web"
    assert view.combo.currentText() == "Web"
    assert shown(view) == [None] * MAX_COLORS


@pytest.mark.spec("PAL-001")
def test_cancelling_the_new_palette_creates_nothing(qtbot: QtBot) -> None:
    palettes = Palettes()
    view = view_of(qtbot, palettes)
    view.ask_name = replying(None)
    view.new_action.trigger()
    assert palettes.names == ()


@pytest.mark.spec("PAL-001")
def test_without_palettes_only_new_and_import_are_available(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes())
    assert not view.add_button.isEnabled()
    assert menu_texts(view.menu) == {
        "Nueva paleta…": True,
        "Renombrar…": False,
        "Borrar…": False,
        "Importar…": True,
        "Exportar…": False,
    }


@pytest.mark.spec("PAL-001")
def test_with_an_active_palette_every_action_is_available(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": []}, active="Web"))
    assert view.add_button.isEnabled()
    assert all(menu_texts(view.menu).values())


# PAL-002 · Nombre de una paleta


def dialog_for(qtbot: QtBot, palettes: Palettes, renaming: bool = False) -> NameDialog:
    create_app([])
    check = partial(palettes.clean_name, renaming=renaming)
    text = (palettes.active or "") if renaming else ""
    dialog = NameDialog("Nueva paleta", check, text)
    qtbot.addWidget(dialog)
    return dialog


def ok_button(dialog: NameDialog) -> QWidget:
    button = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert button is not None
    return button


@pytest.mark.spec("PAL-002")
def test_the_dialog_cleans_the_spaces_at_both_ends(qtbot: QtBot) -> None:
    dialog = dialog_for(qtbot, Palettes())
    dialog.field.setText("  Web  ")
    assert ok_button(dialog).isEnabled()
    assert not dialog.error.isVisibleTo(dialog)
    assert dialog.name() == "Web"


@pytest.mark.spec("PAL-002")
def test_a_repeated_name_cannot_be_confirmed_and_says_why(qtbot: QtBot) -> None:
    dialog = dialog_for(qtbot, Palettes({"Web": []}))
    dialog.field.setText("web")
    assert not ok_button(dialog).isEnabled()
    assert dialog.error.isVisibleTo(dialog)
    assert dialog.error.text() == "Ya hay una paleta con ese nombre."


@pytest.mark.spec("PAL-002")
@pytest.mark.parametrize("text", ["", "   "])
def test_an_empty_name_cannot_be_confirmed_and_says_why(qtbot: QtBot, text: str) -> None:
    dialog = dialog_for(qtbot, Palettes())
    dialog.field.setText("x")
    dialog.field.setText(text)
    assert not ok_button(dialog).isEnabled()
    assert dialog.error.text() == "El nombre no puede estar vacío."


@pytest.mark.spec("PAL-002")
def test_the_name_field_stops_at_40_characters(qtbot: QtBot) -> None:
    dialog = dialog_for(qtbot, Palettes())
    QTest.keyClicks(dialog.field, "x" * 41)
    assert dialog.field.text() == "x" * 40


@pytest.mark.spec("PAL-002", "APP-006")
def test_asking_a_name_returns_it_when_accepted(qtbot: QtBot) -> None:
    create_app([])
    parent = QWidget()
    qtbot.addWidget(parent)
    seen: list[set[str]] = []

    def accept() -> None:
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, NameDialog)
        seen.append({dialog.windowTitle(), dialog.label.text()})
        seen.append({button.text() for button in dialog.buttons.buttons()})
        dialog.field.setText(" Web ")
        dialog.accept()

    QTimer.singleShot(0, accept)
    assert ask_name(parent, "Nueva paleta", Palettes().clean_name) == "Web"
    assert seen == [{"Nueva paleta", "Nombre:"}, {"Aceptar", "Cancelar"}]


@pytest.mark.spec("PAL-002")
def test_asking_a_name_returns_none_when_cancelled(qtbot: QtBot) -> None:
    create_app([])
    parent = QWidget()
    qtbot.addWidget(parent)

    def cancel() -> None:
        dialog = QApplication.activeModalWidget()
        assert isinstance(dialog, QDialog)
        dialog.reject()

    QTimer.singleShot(0, cancel)
    assert ask_name(parent, "Nueva paleta", Palettes().clean_name) is None


# PAL-003 · Renombrar una paleta


@pytest.mark.spec("PAL-003")
def test_renaming_keeps_the_colours(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    asked: list[tuple[str, str]] = []
    view.ask_name = replying("Marca", asked)
    view.rename_action.trigger()
    assert asked == [("Renombrar paleta", "Web")]
    assert palettes.names == ("Marca",)
    assert palettes.colors() == (RED, BLUE)
    assert view.combo.currentText() == "Marca"


@pytest.mark.spec("PAL-003")
def test_renaming_may_change_only_the_case(qtbot: QtBot) -> None:
    dialog = dialog_for(qtbot, Palettes({"Web": []}, active="Web"), renaming=True)
    assert dialog.field.text() == "Web"
    dialog.field.setText("WEB")
    assert ok_button(dialog).isEnabled()


@pytest.mark.spec("PAL-003")
def test_cancelling_the_rename_keeps_the_name(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": []}, active="Web")
    view = view_of(qtbot, palettes)
    view.ask_name = replying(None)
    view.rename_action.trigger()
    assert palettes.names == ("Web",)


# PAL-004 · Borrar una paleta


@pytest.mark.spec("PAL-004")
def test_deleting_and_confirming_activates_the_next_palette(qtbot: QtBot) -> None:
    palettes = Palettes({"A": [RED], "B": [], "C": [GREEN]}, active="B")
    view = view_of(qtbot, palettes)
    view.ask_to_delete = confirming(True)
    view.delete_action.trigger()
    assert palettes.names == ("A", "C")
    assert view.combo.currentText() == "C"
    assert shown(view)[0] == GREEN


@pytest.mark.spec("PAL-004")
def test_deleting_and_cancelling_keeps_the_palette(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": []}, active="Web")
    view = view_of(qtbot, palettes)
    view.ask_to_delete = confirming(False)
    view.delete_action.trigger()
    assert palettes.names == ("Web",)


@pytest.mark.spec("PAL-004", "APP-006")
def test_the_delete_question_names_the_palette_and_defaults_to_no(qtbot: QtBot) -> None:
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
    assert ask_to_delete(parent, "Web") is False
    assert seen == [
        {"Borrar paleta", "¿Borrar la paleta «Web»? No se puede deshacer."},
        {"&Sí", "&No"},
    ]


# PAL-005 · Elegir la paleta activa


@pytest.mark.spec("PAL-005")
def test_the_list_is_in_alphabetical_order(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"web": [], "Fotos": [], "Marca": []}, active="web"))
    items = [view.combo.itemText(index) for index in range(view.combo.count())]
    assert items == ["Fotos", "Marca", "web"]
    assert view.combo.currentText() == "web"


@pytest.mark.spec("PAL-005")
def test_choosing_a_palette_in_the_list_shows_its_colours(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED], "Marca": [GREEN]}, active="Web")
    view = view_of(qtbot, palettes)
    view.combo.setCurrentIndex(view.combo.findText("Marca"))
    assert palettes.active == "Marca"
    assert shown(view)[:2] == [GREEN, None]


# PAL-006 · Añadir el color actual


@pytest.mark.spec("PAL-006")
def test_adding_puts_the_current_colour_at_the_end(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED]}, active="Web")
    view = view_of(qtbot, palettes, current=BLUE)
    view.add_button.click()
    assert palettes.colors() == (RED, BLUE)
    assert shown(view)[:3] == [RED, BLUE, None]


@pytest.mark.spec("PAL-006")
def test_adding_a_colour_already_there_warns(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED]}, active="Web")
    view = view_of(qtbot, palettes, current=RED)
    with qtbot.waitSignal(view.message) as message:
        view.add_button.click()
    assert message.args == ["#FF0000FF ya está en la paleta Web", 4000]
    assert NOTICE_MS == 4000
    assert palettes.colors() == (RED,)


# PAL-007 · Quitar un color


@pytest.mark.spec("PAL-007")
def test_right_clicking_a_colour_offers_to_remove_it(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    offered: list[list[str]] = []

    def choose() -> None:
        menu = QApplication.activePopupWidget()
        assert isinstance(menu, QMenu)
        offered.append([action.text() for action in menu.actions()])
        trigger(menu, "Quitar de la paleta")
        menu.close()

    swatch = view.swatches[1]
    QTimer.singleShot(0, choose)
    event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, CENTER, swatch.mapToGlobal(CENTER))
    QApplication.sendEvent(swatch, event)
    assert offered == [["Quitar de la paleta", "Mover a la izquierda", "Mover a la derecha"]]
    assert palettes.colors() == (RED, BLUE)


# PAL-008 · Reordenar los colores


@pytest.mark.spec("PAL-008")
def test_dragging_a_colour_onto_another_moves_it_there(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    chosen: list[Color] = []
    view.color_chosen.connect(chosen.append)
    drag(view.swatches[2], view.swatches[0])
    assert palettes.colors() == (BLUE, RED, GREEN)
    assert chosen == []


@pytest.mark.spec("PAL-008")
def test_dropping_a_colour_on_an_empty_place_moves_it_to_the_end(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    drag(view.swatches[0], view.swatches[COLUMNS + 4])
    assert palettes.colors() == (GREEN, BLUE, RED)


@pytest.mark.spec("PAL-008")
def test_dropping_a_colour_outside_the_grid_changes_nothing(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    drag(view.swatches[0], view.add_button)
    assert palettes.colors() == (RED, GREEN, BLUE)


@pytest.mark.spec("PAL-008")
@pytest.mark.parametrize(
    ("index", "text", "result"),
    [
        (0, "Mover a la derecha", (GREEN, RED, BLUE)),
        (2, "Mover a la izquierda", (RED, BLUE, GREEN)),
    ],
)
def test_the_menu_moves_a_colour_one_place(
    qtbot: QtBot, index: int, text: str, result: tuple[Color, ...]
) -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    trigger(view.menu_for(view.swatches[index]), text)
    assert palettes.colors() == result


@pytest.mark.spec("PAL-008")
def test_the_menu_cannot_move_past_the_ends(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": [RED, GREEN, BLUE]}, active="Web"))
    first = menu_texts(view.menu_for(view.swatches[0]))
    last = menu_texts(view.menu_for(view.swatches[2]))
    assert first == {
        "Quitar de la paleta": True,
        "Mover a la izquierda": False,
        "Mover a la derecha": True,
    }
    assert last == {
        "Quitar de la paleta": True,
        "Mover a la izquierda": True,
        "Mover a la derecha": False,
    }


# PAL-009 · Recuperar un color de una paleta


@pytest.mark.spec("PAL-009")
def test_clicking_a_colour_chooses_it_without_changing_the_palette(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": [RED, BLUE]}, active="Web")
    view = view_of(qtbot, palettes)
    with qtbot.waitSignal(view.color_chosen) as chosen:
        view.swatches[1].click()
    assert chosen.args == [BLUE]
    assert palettes.colors() == (RED, BLUE)


@pytest.mark.spec("PAL-009")
def test_a_short_movement_is_still_a_click(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": [RED, BLUE]}, active="Web"))
    chosen: list[Color] = []
    view.color_chosen.connect(chosen.append)
    swatch = view.swatches[0]
    left = Qt.MouseButton.LeftButton
    send_mouse(swatch, QEvent.Type.MouseButtonPress, CENTER, left)
    send_mouse(swatch, QEvent.Type.MouseMove, CENTER + QPoint(2, 1), left)
    send_mouse(
        swatch, QEvent.Type.MouseButtonRelease, CENTER + QPoint(2, 1), Qt.MouseButton.NoButton
    )
    assert chosen == [RED]


@pytest.mark.spec("PAL-009")
def test_the_tooltip_of_a_colour_is_its_hex(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": [RED]}, active="Web"))
    assert [swatch.toolTip() for swatch in view.swatches[:2]] == ["#FF0000FF", ""]


# PAL-010 · Límite de colores


@pytest.mark.spec("PAL-010")
def test_a_full_palette_cannot_get_more_colours(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": numbered(MAX_COLORS)}, active="Web"))
    assert not view.add_button.isEnabled()


@pytest.mark.spec("PAL-010")
def test_the_twentieth_colour_disables_adding(qtbot: QtBot) -> None:
    palettes = Palettes({"Web": numbered(MAX_COLORS - 1)}, active="Web")
    view = view_of(qtbot, palettes, current=BLUE)
    view.add_button.click()
    assert len(palettes.colors()) == MAX_COLORS
    assert not view.add_button.isEnabled()


# PAL-016 · Ubicación en la ventana


@pytest.mark.spec("PAL-016")
def test_the_list_and_the_menu_button_share_the_first_row(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": []}, active="Web"))
    assert view.menu_button.text() == "Paleta"
    assert view.menu_button.menu() is view.menu
    assert view.menu_button.x() > view.combo.x() + view.combo.width() - 1
    assert abs(view.menu_button.geometry().center().y() - view.combo.geometry().center().y()) <= 2
    grid_top = min(swatch.y() for swatch in view.swatches)
    grid_bottom = max(swatch.y() + swatch.height() for swatch in view.swatches)
    assert view.combo.y() + view.combo.height() <= grid_top
    assert grid_bottom <= view.add_button.y()
    assert view.add_button.text() == "Añadir color actual"


@pytest.mark.spec("PAL-016")
def test_the_grid_has_two_rows_of_ten_swatches_of_24_px(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes({"Web": []}, active="Web"))
    assert len(view.swatches) == MAX_COLORS
    assert {(swatch.width(), swatch.height()) for swatch in view.swatches} == {(24, 24)}
    assert len({swatch.y() for swatch in view.swatches}) == 2
    assert all(isinstance(swatch, PaletteSwatch) for swatch in view.swatches)


@pytest.mark.spec("PAL-016")
def test_the_menu_lists_the_palette_actions_in_order(qtbot: QtBot) -> None:
    view = view_of(qtbot, Palettes())
    assert list(menu_texts(view.menu)) == [
        "Nueva paleta…",
        "Renombrar…",
        "Borrar…",
        "Importar…",
        "Exportar…",
    ]
