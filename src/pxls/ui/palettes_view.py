"""Pestaña «Paletas»: lista, menú «Paleta», rejilla de colores con arrastre y «Añadir color actual».

Spec: PAL-001, PAL-002, PAL-003, PAL-004, PAL-005, PAL-006, PAL-007, PAL-008, PAL-009, PAL-010,
    PAL-014, PAL-015, PAL-016, APP-006
"""

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Protocol

from PySide6.QtCore import QPoint, QPointF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pxls.adapters.palette_files import export_palette, import_palette_file
from pxls.core.color import Color
from pxls.core.palette_formats import FORMATS, GPL, TXT, loses_alpha
from pxls.core.palettes import MAX_COLORS, MAX_NAME_LENGTH, PaletteNameError, Palettes
from pxls.ui.swatch import COLUMNS, GAP, Swatch

NOTICE_MS = 4000
GPL_FILTER = "Paleta de GIMP (*.gpl)"
TXT_FILTER = "Texto con un HEX por línea (*.txt)"
_ERROR_STYLE = "color: #C62828;"
_VISIBLE_NAME_LENGTH = 10


class AskName(Protocol):
    """Pregunta un nombre; devuelve el nombre limpio o ``None`` si se cancela."""

    def __call__(
        self, parent: QWidget, title: str, check: Callable[[str], str], text: str = ""
    ) -> str | None:
        """Muestra la pregunta con ``text`` escrito y ``check`` para validarlo."""
        ...


class NameDialog(QDialog):
    """Diálogo del nombre de una paleta: no deja aceptar un nombre no válido y dice por qué."""

    def __init__(
        self,
        title: str,
        check: Callable[[str], str],
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """Crea el diálogo; ``check`` limpia el nombre o lanza ``PaletteNameError`` (PAL-002)."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self._check = check
        self.label = QLabel("Nombre:", self)
        self.field = QLineEdit(text, self)
        self.field.setMaxLength(MAX_NAME_LENGTH)
        self.error = QLabel(self)
        self.error.setStyleSheet(_ERROR_STYLE)
        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttons = QDialogButtonBox(buttons, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.field)
        layout.addWidget(self.error)
        layout.addWidget(self.buttons)
        self.field.textChanged.connect(self._validate)
        self._validate(text)

    def name(self) -> str:
        """Devuelve el nombre escrito, ya limpio."""
        return self._check(self.field.text())

    def _validate(self, text: str) -> None:
        ok = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        try:
            self._check(text)
        except PaletteNameError as error:
            self.error.setText(str(error))
            self.error.show()
            ok.setEnabled(False)
            return
        self.error.hide()
        ok.setEnabled(True)


def ask_name(
    parent: QWidget, title: str, check: Callable[[str], str], text: str = ""
) -> str | None:
    """Pregunta el nombre de una paleta con ``NameDialog`` (PAL-001, PAL-003)."""
    dialog = NameDialog(title, check, text, parent)
    try:
        return dialog.name() if dialog.exec() == QDialog.DialogCode.Accepted else None
    finally:
        dialog.deleteLater()


def ask_to_delete(parent: QWidget, name: str) -> bool:
    """Pregunta si se borra la paleta ``name``; «No» es la respuesta por defecto (PAL-004)."""
    buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    box = QMessageBox(
        QMessageBox.Icon.Question,
        "Borrar paleta",
        f"¿Borrar la paleta «{name}»? No se puede deshacer.",
        buttons,
        parent,
    )
    box.setDefaultButton(QMessageBox.StandardButton.No)
    return box.exec() == QMessageBox.StandardButton.Yes


def ask_export_path(parent: QWidget, name: str) -> Path | None:
    """Pregunta dónde exportar la paleta ``name``; sin extensión, añade la del filtro (PAL-014)."""
    chosen, selected = QFileDialog.getSaveFileName(
        parent, "Exportar paleta", f"{name}{GPL}", f"{GPL_FILTER};;{TXT_FILTER}"
    )
    if not chosen:
        return None
    path = Path(chosen)
    if path.suffix.lower() not in FORMATS:
        path = path.with_name(path.name + (TXT if selected == TXT_FILTER else GPL))
    return path


def ask_import_path(parent: QWidget) -> Path | None:
    """Pregunta qué fichero ``.gpl`` o ``.txt`` importar (PAL-015)."""
    filters = f"Paletas (*{GPL} *{TXT});;{GPL_FILTER};;{TXT_FILTER}"
    chosen, _ = QFileDialog.getOpenFileName(parent, "Importar paleta", "", filters)
    return Path(chosen) if chosen else None


class PaletteSwatch(Swatch):
    """Muestra de una paleta que se puede arrastrar a otra posición (PAL-008)."""

    dropped = Signal(QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Crea la muestra vacía."""
        super().__init__(parent)
        self._pressed_at: QPointF | None = None
        self._dragging = False

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Recuerda dónde se pulsa, por si empieza un arrastre."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed_at = event.position()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Pasa a arrastrar cuando el ratón se aleja la distancia de arrastre del sistema."""
        held = bool(event.buttons() & Qt.MouseButton.LeftButton)
        if self._pressed_at is not None and held and not self._dragging:
            distance = (event.position() - self._pressed_at).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self._dragging = True
                self.setDown(False)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if not self._dragging:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Al soltar un arrastre avisa de dónde; sin arrastre, es un clic normal."""
        self._pressed_at = None
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.dropped.emit(self.mapToGlobal(event.position().toPoint()))
        # Tras un arrastre la muestra ya no está pulsada: soltar no es un clic.
        super().mouseReleaseEvent(event)


class PalettesView(QWidget):
    """Lista de paletas, menú «Paleta», rejilla de colores y «Añadir color actual» (PAL-016)."""

    color_chosen = Signal(Color)
    message = Signal(str, int)

    def __init__(
        self, palettes: Palettes, current: Callable[[], Color], parent: QWidget | None = None
    ) -> None:
        """Muestra ``palettes`` y las sigue; ``current`` da el color actual para añadirlo."""
        super().__init__(parent)
        self.palettes = palettes
        self._current = current
        self.ask_name: AskName = ask_name
        self.ask_to_delete: Callable[[QWidget, str], bool] = ask_to_delete
        self.ask_export_path: Callable[[QWidget, str], Path | None] = ask_export_path
        self.ask_import_path: Callable[[QWidget], Path | None] = ask_import_path
        self.combo = QComboBox(self)
        policy = QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        self.combo.setSizeAdjustPolicy(policy)
        self.combo.setMinimumContentsLength(_VISIBLE_NAME_LENGTH)
        self.combo.currentIndexChanged.connect(self._select)
        self.menu = QMenu(self)
        self.new_action = self.menu.addAction("Nueva paleta…", self._create)
        self.rename_action = self.menu.addAction("Renombrar…", self._rename)
        self.delete_action = self.menu.addAction("Borrar…", self._delete)
        self.import_action = self.menu.addAction("Importar…", self._import)
        self.export_action = self.menu.addAction("Exportar…", self._export)
        self.menu_button = QPushButton("Paleta", self)
        self.menu_button.setMenu(self.menu)
        top = QHBoxLayout()
        top.addWidget(self.combo, 1)
        top.addWidget(self.menu_button)
        grid = QGridLayout()
        grid.setSpacing(GAP)
        self.swatches: list[PaletteSwatch] = []
        for index in range(MAX_COLORS):
            swatch = PaletteSwatch(self)
            swatch.clicked.connect(partial(self._choose, swatch))
            swatch.customContextMenuRequested.connect(partial(self._open_menu, swatch))
            swatch.dropped.connect(partial(self._drop, swatch))
            grid.addWidget(swatch, index // COLUMNS, index % COLUMNS)
            self.swatches.append(swatch)
        self.add_button = QPushButton("Añadir color actual", self)
        self.add_button.clicked.connect(self._add)
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self.add_button)
        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(grid)
        layout.addLayout(bottom)
        palettes.on_change(self._refresh)
        self._refresh()

    def menu_for(self, swatch: PaletteSwatch) -> QMenu:
        """Crea el menú del clic derecho de un color: quitar y mover (PAL-007, PAL-008)."""
        menu = QMenu(self)
        if swatch.color is not None:
            index = self.swatches.index(swatch)
            count = len(self.palettes.colors())
            menu.addAction("Quitar de la paleta", partial(self.palettes.remove, swatch.color))
            left = menu.addAction(
                "Mover a la izquierda", partial(self.palettes.move, index, index - 1)
            )
            left.setEnabled(index > 0)
            right = menu.addAction(
                "Mover a la derecha", partial(self.palettes.move, index, index + 1)
            )
            right.setEnabled(index < count - 1)
        return menu

    def _refresh(self) -> None:
        names, active = self.palettes.names, self.palettes.active
        with QSignalBlocker(self.combo):
            self.combo.clear()
            self.combo.addItems(list(names))
            self.combo.setCurrentIndex(names.index(active) if active is not None else -1)
        self.combo.setEnabled(bool(names))
        colors = self.palettes.colors()
        for index, swatch in enumerate(self.swatches):
            swatch.show_color(colors[index] if index < len(colors) else None)
        for action in (self.rename_action, self.delete_action, self.export_action):
            action.setEnabled(active is not None)
        self.add_button.setEnabled(active is not None and not self.palettes.full)

    def _select(self, index: int) -> None:
        if index >= 0:
            self.palettes.select(self.combo.itemText(index))

    def _create(self) -> None:
        name = self.ask_name(self, "Nueva paleta", self.palettes.clean_name)
        if name is not None:
            self.palettes.create(name)

    def _rename(self) -> None:
        active = self.palettes.active
        if active is None:
            return
        check = partial(self.palettes.clean_name, renaming=True)
        name = self.ask_name(self, "Renombrar paleta", check, active)
        if name is not None:
            self.palettes.rename(name)

    def _delete(self) -> None:
        active = self.palettes.active
        if active is not None and self.ask_to_delete(self, active):
            self.palettes.delete()

    def _add(self) -> None:
        color, active = self._current(), self.palettes.active
        if active is not None and not self.palettes.add(color):
            self.message.emit(f"{color.to_hex()} ya está en la paleta {active}", NOTICE_MS)

    def _export(self) -> None:
        active = self.palettes.active
        path = self.ask_export_path(self, active) if active is not None else None
        if active is None or path is None:
            return
        colors = self.palettes.colors()
        try:
            export_palette(path, active, colors)
        except (OSError, ValueError):
            self.message.emit(f"No se ha podido exportar la paleta a {path}", NOTICE_MS)
            return
        text = f"Paleta exportada a {path}"
        if loses_alpha(path.suffix.lower(), colors):
            text += " sin transparencia: el formato .gpl no la guarda"
        self.message.emit(text, NOTICE_MS)

    def _import(self) -> None:
        path = self.ask_import_path(self)
        if path is None:
            return
        try:
            name, colors = import_palette_file(path)
        except (OSError, ValueError):
            text = f"No se ha podido importar {path}: no es una paleta .gpl o .txt válida"
            self.message.emit(text, NOTICE_MS)
            return
        imported = self.palettes.import_palette(name, colors)
        text = f"Paleta importada: {imported.name}"
        if imported.kept < imported.total:
            text += f", con {imported.kept} de sus {imported.total} colores"
        self.message.emit(text, NOTICE_MS)

    def _choose(self, swatch: PaletteSwatch) -> None:
        # Recuperar un color no lo usa: ni la paleta ni el historial cambian (PAL-009).
        if swatch.color is not None:
            self.color_chosen.emit(swatch.color)

    def _open_menu(self, swatch: PaletteSwatch, position: QPoint) -> None:
        menu = self.menu_for(swatch)
        menu.exec(swatch.mapToGlobal(position))
        menu.deleteLater()

    def _drop(self, swatch: PaletteSwatch, point: QPoint) -> None:
        # Soltar sobre una muestra vacía lleva el color al final; fuera de la rejilla, nada.
        local = self.mapFromGlobal(point)
        for target, other in enumerate(self.swatches):
            if other.geometry().contains(local):
                self.palettes.move(self.swatches.index(swatch), target)
                return
