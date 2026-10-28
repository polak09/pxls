import re
from importlib.metadata import version

import pytest
from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QAbstractButton, QDialogButtonBox, QLabel, QTabWidget, QWidget
from pytestqt.qtbot import QtBot

from pxls.core.picker import PickerSession
from pxls.ui import app
from pxls.ui.app import create_app, main, run, smoke_test
from pxls.ui.main_window import MainWindow, icon_path

# Textos en español aprobados para la interfaz (APP-006).
SPANISH_TEXTS = {
    "Capturar color",
    "Copiar",
    "Rojo",
    "Verde",
    "Azul",
    "Tono",
    "Saturación",
    "Valor",
    "Alfa",
    "Historial",
    "Vaciar historial",
    "Paletas",
    "Paleta",
    "Añadir color actual",
    "Nueva paleta…",
    "Renombrar…",
    "Borrar…",
    "Importar…",
    "Exportar…",
}
FORMAT_NAMES = {"HEX", "RGB", "HSL", "HSV"}
COLOR_TEXT = re.compile(r"^(#[0-9A-F]{8}|(rgb|hsl|hsv)a?\(.*\))$")


def window(qtbot: QtBot, app_version: str | None = None) -> MainWindow:
    create_app([])
    shown = MainWindow(app_version)
    qtbot.addWidget(shown)
    return shown


def visible_texts(widget: QWidget) -> set[str]:
    texts = {widget.windowTitle()}
    texts |= {label.text() for label in widget.findChildren(QLabel) if label.text()}
    texts |= {action.text() for action in widget.findChildren(QAction) if action.text()}
    texts |= {button.text() for button in widget.findChildren(QAbstractButton) if button.text()}
    for tabs in widget.findChildren(QTabWidget):
        texts |= {tabs.tabText(index) for index in range(tabs.count())}
    return texts


# APP-002 · Título de la ventana


@pytest.mark.spec("APP-002")
def test_window_title_is_pxls(qtbot: QtBot) -> None:
    assert window(qtbot).windowTitle() == "pxls"


# APP-003 · Tamaño de la ventana


@pytest.mark.spec("APP-003")
def test_window_opens_at_420_by_780(qtbot: QtBot) -> None:
    shown = window(qtbot)
    shown.show()
    assert shown.size() == QSize(420, 780)


@pytest.mark.spec("APP-003")
@pytest.mark.parametrize(
    ("requested", "expected"), [((300, 300), (360, 480)), ((600, 700), (600, 700))]
)
def test_window_is_resizable_down_to_360_by_480(
    qtbot: QtBot, requested: tuple[int, int], expected: tuple[int, int]
) -> None:
    shown = window(qtbot)
    shown.show()
    shown.resize(*requested)
    assert shown.size() == QSize(*expected)


# APP-004 · Icono


@pytest.mark.spec("APP-004")
def test_window_uses_the_pxls_icon(qtbot: QtBot) -> None:
    icon = window(qtbot).windowIcon()
    assert not icon.isNull()
    assert icon.pixmap(32).toImage() == QIcon(str(icon_path())).pixmap(32).toImage()


@pytest.mark.spec("APP-004")
def test_icon_file_has_several_resolutions() -> None:
    sizes = {size.width() for size in QIcon(str(icon_path())).availableSizes()}
    assert {16, 32, 48, 256} <= sizes


# APP-005 · Versión visible


@pytest.mark.spec("APP-005")
def test_status_bar_shows_the_version(qtbot: QtBot) -> None:
    shown = window(qtbot, "0.1.0")
    assert "v0.1.0" in {label.text() for label in shown.statusBar().findChildren(QLabel)}


@pytest.mark.spec("APP-005")
def test_version_comes_from_the_project(qtbot: QtBot) -> None:
    assert f"v{version('pxls')}" in visible_texts(window(qtbot))


# APP-006 · Idioma de la interfaz


@pytest.mark.spec("APP-006")
def test_every_visible_text_is_spanish_or_an_allowed_exception(qtbot: QtBot) -> None:
    allowed = {"pxls", "v0.1.0"} | SPANISH_TEXTS | FORMAT_NAMES
    for text in visible_texts(window(qtbot, "0.1.0")):
        assert text in allowed or COLOR_TEXT.match(text), text


@pytest.mark.spec("APP-006")
def test_standard_dialog_buttons_are_in_spanish(qtbot: QtBot) -> None:
    create_app([])
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
    qtbot.addWidget(buttons)
    assert buttons.button(QDialogButtonBox.StandardButton.Cancel).text() == "Cancelar"


# APP-007 · Cierre


@pytest.mark.spec("APP-007")
def test_closing_the_main_window_ends_the_application_with_0(qtbot: QtBot) -> None:
    application = create_app([])
    shown = MainWindow()
    QTimer.singleShot(0, shown.close)
    assert run(application, shown) == 0


# APP-009 · Prueba de humo (en el propio proceso)


@pytest.mark.spec("APP-009")
def test_smoke_test_creates_the_window_without_showing_it(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    created: list[MainWindow] = []
    original = MainWindow

    def recording(
        app_version: str | None = None, session: PickerSession | None = None
    ) -> MainWindow:
        created.append(original(app_version, session))
        return created[-1]

    monkeypatch.setattr(app, "MainWindow", recording)
    assert main(["pxls", "--smoke-test"]) == 0
    assert len(created) == 1
    assert not created[0].isVisible()


@pytest.mark.spec("APP-009")
def test_smoke_test_fails_when_the_application_cannot_start(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(app_version: str | None = None, session: PickerSession | None = None) -> MainWindow:
        raise ImportError("falta una dependencia")

    monkeypatch.setattr(app, "MainWindow", broken)
    assert smoke_test(["pxls", "--smoke-test"]) != 0
