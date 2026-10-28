import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.color import Color
from pxls.core.palettes import (
    IMPORTED_NAME,
    MAX_COLORS,
    MAX_NAME_LENGTH,
    Imported,
    PaletteFormatError,
    PaletteNameError,
    Palettes,
    dump_palettes,
    load_palettes,
)

RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)
HALF_BLUE = Color(0, 0, 255, 128)


def numbered(count: int) -> list[Color]:
    return [Color(index, 0, 0) for index in range(count)]


def recorder(palettes: Palettes) -> list[int]:
    calls: list[int] = []
    palettes.on_change(lambda: calls.append(1))
    return calls


# PAL-001 · Crear una paleta


@pytest.mark.spec("PAL-001")
def test_a_new_collection_has_no_palettes() -> None:
    palettes = Palettes()
    assert palettes.names == ()
    assert palettes.active is None
    assert palettes.colors() == ()


@pytest.mark.spec("PAL-001")
def test_creating_a_palette_makes_it_active_and_empty() -> None:
    palettes = Palettes({"Marca": [RED]}, active="Marca")
    calls = recorder(palettes)
    assert palettes.create("Web") == "Web"
    assert palettes.names == ("Marca", "Web")
    assert palettes.active == "Web"
    assert palettes.colors() == ()
    assert calls == [1]


# PAL-002 · Nombre de una paleta


@pytest.mark.spec("PAL-002")
def test_the_name_loses_the_spaces_at_both_ends() -> None:
    palettes = Palettes()
    assert palettes.create("  Web  ") == "Web"
    assert palettes.names == ("Web",)


@pytest.mark.spec("PAL-002")
@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("", "El nombre no puede estar vacío."),
        ("   ", "El nombre no puede estar vacío."),
        ("web", "Ya hay una paleta con ese nombre."),
        (" WEB ", "Ya hay una paleta con ese nombre."),
        ("x" * 41, "El nombre no puede tener más de 40 caracteres."),
    ],
)
def test_an_invalid_name_is_rejected_with_its_reason(name: str, message: str) -> None:
    palettes = Palettes({"Web": []}, active="Web")
    calls = recorder(palettes)
    with pytest.raises(PaletteNameError) as raised:
        palettes.create(name)
    assert str(raised.value) == message
    assert palettes.names == ("Web",)
    assert calls == []


@pytest.mark.spec("PAL-002")
def test_a_name_of_40_characters_is_valid() -> None:
    assert MAX_NAME_LENGTH == 40
    assert Palettes().clean_name("x" * 40) == "x" * 40


@pytest.mark.spec("PAL-002")
def test_an_initial_collection_with_invalid_names_is_rejected() -> None:
    with pytest.raises(PaletteNameError):
        Palettes({"Web": [], "WEB": []})


# PAL-003 · Renombrar una paleta


@pytest.mark.spec("PAL-003")
def test_renaming_keeps_the_colours_and_the_active_palette() -> None:
    palettes = Palettes({"Web": [RED, BLUE], "Fotos": []}, active="Web")
    calls = recorder(palettes)
    assert palettes.rename("Marca") == "Marca"
    assert palettes.names == ("Fotos", "Marca")
    assert palettes.active == "Marca"
    assert palettes.colors() == (RED, BLUE)
    assert calls == [1]


@pytest.mark.spec("PAL-003")
def test_renaming_may_only_change_the_case() -> None:
    palettes = Palettes({"Web": [RED]}, active="Web")
    assert palettes.clean_name("WEB", renaming=True) == "WEB"
    palettes.rename("WEB")
    assert palettes.names == ("WEB",)


@pytest.mark.spec("PAL-003")
def test_renaming_to_another_palette_name_is_rejected() -> None:
    palettes = Palettes({"Web": [], "Marca": []}, active="Web")
    with pytest.raises(PaletteNameError):
        palettes.rename("marca")
    assert palettes.names == ("Marca", "Web")


# PAL-004 · Borrar una paleta


@pytest.mark.spec("PAL-004")
@pytest.mark.parametrize(
    ("names", "active", "left", "next_active"),
    [
        (["A", "B", "C"], "B", ("A", "C"), "C"),
        (["A", "B"], "B", ("A",), "A"),
        (["A"], "A", (), None),
    ],
)
def test_deleting_activates_the_next_or_the_previous_palette(
    names: list[str], active: str, left: tuple[str, ...], next_active: str | None
) -> None:
    palettes = Palettes({name: [] for name in names}, active=active)
    calls = recorder(palettes)
    palettes.delete()
    assert palettes.names == left
    assert palettes.active == next_active
    assert calls == [1]


@pytest.mark.spec("PAL-004")
def test_without_an_active_palette_there_is_nothing_to_delete() -> None:
    with pytest.raises(LookupError):
        Palettes().delete()


# PAL-005 · Elegir la paleta activa


@pytest.mark.spec("PAL-005")
def test_names_are_in_alphabetical_order_ignoring_case() -> None:
    palettes = Palettes({"web": [], "Fotos": [], "Marca": []})
    assert palettes.names == ("Fotos", "Marca", "web")


@pytest.mark.spec("PAL-005")
def test_selecting_a_palette_shows_its_colours() -> None:
    palettes = Palettes({"Web": [RED], "Marca": [GREEN]}, active="Web")
    calls = recorder(palettes)
    palettes.select("Marca")
    assert palettes.active == "Marca"
    assert palettes.colors() == (GREEN,)
    assert palettes.colors("Web") == (RED,)
    palettes.select("Marca")
    assert calls == [1]


@pytest.mark.spec("PAL-005")
def test_selecting_an_unknown_palette_is_an_error() -> None:
    with pytest.raises(KeyError):
        Palettes({"Web": []}).select("Marca")


@pytest.mark.spec("PAL-005")
def test_an_unknown_initial_active_palette_is_rejected() -> None:
    with pytest.raises(KeyError):
        Palettes({"Web": []}, active="Marca")


# PAL-006 · Añadir el color actual


@pytest.mark.spec("PAL-006")
def test_adding_puts_the_colour_at_the_end() -> None:
    palettes = Palettes({"Web": [RED]}, active="Web")
    calls = recorder(palettes)
    assert palettes.add(BLUE) is True
    assert palettes.colors() == (RED, BLUE)
    assert calls == [1]


@pytest.mark.spec("PAL-006")
def test_adding_a_colour_already_there_changes_nothing() -> None:
    palettes = Palettes({"Web": [RED]}, active="Web")
    calls = recorder(palettes)
    assert palettes.add(RED) is False
    assert palettes.colors() == (RED,)
    assert calls == []


@pytest.mark.spec("PAL-006")
def test_without_an_active_palette_nothing_can_be_added() -> None:
    with pytest.raises(LookupError):
        Palettes().add(RED)


# PAL-007 · Quitar un color


@pytest.mark.spec("PAL-007")
def test_removing_keeps_the_order_of_the_others() -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    calls = recorder(palettes)
    palettes.remove(GREEN)
    assert palettes.colors() == (RED, BLUE)
    palettes.remove(GREEN)
    assert calls == [1]


# PAL-008 · Reordenar los colores


@pytest.mark.spec("PAL-008")
@pytest.mark.parametrize(
    ("source", "target", "result"),
    [
        (2, 0, (BLUE, RED, GREEN)),
        (0, 2, (GREEN, BLUE, RED)),
        (0, 1, (GREEN, RED, BLUE)),
        (2, 1, (RED, BLUE, GREEN)),
        (0, 7, (GREEN, BLUE, RED)),
    ],
)
def test_moving_a_colour_shifts_the_others(
    source: int, target: int, result: tuple[Color, ...]
) -> None:
    palettes = Palettes({"Web": [RED, GREEN, BLUE]}, active="Web")
    palettes.move(source, target)
    assert palettes.colors() == result


@pytest.mark.spec("PAL-008")
def test_moving_a_colour_onto_itself_changes_nothing() -> None:
    palettes = Palettes({"Web": [RED, GREEN]}, active="Web")
    calls = recorder(palettes)
    palettes.move(1, 1)
    assert calls == []


@pytest.mark.spec("PAL-008")
@given(st.integers(0, 9), st.integers(0, 30))
def test_moving_keeps_the_same_colours(source: int, target: int) -> None:
    colors = numbered(10)
    palettes = Palettes({"Web": colors}, active="Web")
    palettes.move(source, target)
    moved = palettes.colors()
    assert sorted(moved, key=Color.to_hex) == sorted(colors, key=Color.to_hex)
    assert moved[min(target, 9)] == colors[source]


# PAL-010 · Límite de colores


@pytest.mark.spec("PAL-010")
def test_a_palette_holds_up_to_20_colours() -> None:
    assert MAX_COLORS == 20
    palettes = Palettes({"Web": numbered(19)}, active="Web")
    assert not palettes.full
    palettes.add(BLUE)
    assert palettes.full
    with pytest.raises(ValueError):
        palettes.add(GREEN)


@pytest.mark.spec("PAL-010")
def test_an_initial_palette_with_more_than_20_colours_is_rejected() -> None:
    with pytest.raises(ValueError):
        Palettes({"Web": numbered(21)})


@pytest.mark.spec("PAL-010")
def test_without_an_active_palette_it_is_not_full() -> None:
    assert not Palettes().full


# PAL-011 · Conservar entre sesiones (formato)


@pytest.mark.spec("PAL-011")
def test_the_saved_text_has_every_palette_in_order_and_the_active_one() -> None:
    palettes = Palettes({"Web": [RED, BLUE], "Marca": [GREEN]}, active="Marca")
    assert json.loads(dump_palettes(palettes)) == {
        "version": 1,
        "active": "Marca",
        "palettes": [
            {"name": "Marca", "colors": ["#00FF00FF"]},
            {"name": "Web", "colors": ["#FF0000FF", "#0000FFFF"]},
        ],
    }


@pytest.mark.spec("PAL-011")
def test_saving_and_loading_gives_the_same_palettes() -> None:
    palettes = Palettes({"Web": [RED, HALF_BLUE], "Marca": [GREEN], "Vacía": []}, active="Web")
    loaded = load_palettes(dump_palettes(palettes))
    assert loaded.names == palettes.names
    assert loaded.active == "Web"
    for name in palettes.names:
        assert loaded.colors(name) == palettes.colors(name)


@pytest.mark.spec("PAL-011")
def test_no_palettes_are_saved_and_loaded_too() -> None:
    loaded = load_palettes(dump_palettes(Palettes()))
    assert loaded.names == ()
    assert loaded.active is None


# PAL-012 · Fichero de las paletas dañado (formato)


@pytest.mark.spec("PAL-012")
@pytest.mark.parametrize(
    "text",
    [
        "esto no es JSON",
        "[]",
        '{"version": 2, "active": null, "palettes": []}',
        '{"version": 1, "active": null}',
        '{"version": 1, "active": null, "palettes": {}}',
        '{"version": 1, "active": null, "palettes": [["Web", []]]}',
        '{"version": 1, "active": null, "palettes": [{"name": 3, "colors": []}]}',
        '{"version": 1, "active": null, "palettes": [{"name": "Web", "colors": "#FF0000FF"}]}',
        '{"version": 1, "active": null, "palettes": [{"name": "Web", "colors": [1]}]}',
        '{"version": 1, "active": null, "palettes": [{"name": "Web", "colors": ["#GG0000FF"]}]}',
        '{"version": 1, "active": null, "palettes": [{"name": "", "colors": []}]}',
        '{"version": 1, "active": null, "palettes": [{"name": "Web", "colors": []},'
        ' {"name": "web", "colors": []}]}',
        '{"version": 1, "active": null, "palettes": [{"name": "Web",'
        ' "colors": ["#FF0000FF", "#FF0000FF"]}]}',
        '{"version": 1, "active": "Marca", "palettes": [{"name": "Web", "colors": []}]}',
        '{"version": 1, "active": 3, "palettes": []}',
    ],
)
def test_text_that_is_not_valid_palettes_is_rejected(text: str) -> None:
    with pytest.raises(PaletteFormatError):
        load_palettes(text)


@pytest.mark.spec("PAL-012")
def test_a_saved_palette_with_more_than_20_colours_is_rejected() -> None:
    colors = [color.to_hex() for color in numbered(21)]
    text = json.dumps(
        {"version": 1, "active": None, "palettes": [{"name": "Web", "colors": colors}]}
    )
    with pytest.raises(PaletteFormatError):
        load_palettes(text)


# PAL-015 · Importar una paleta


@pytest.mark.spec("PAL-015")
def test_an_imported_palette_becomes_active() -> None:
    palettes = Palettes({"Web": []}, active="Web")
    calls = recorder(palettes)
    assert palettes.import_palette("marca", [RED, HALF_BLUE]) == Imported("marca", 2, 2)
    assert palettes.active == "marca"
    assert palettes.colors() == (RED, HALF_BLUE)
    assert calls == [1]


@pytest.mark.spec("PAL-015")
def test_an_imported_name_that_exists_gets_a_number() -> None:
    palettes = Palettes({"Web": [], "Web (2)": []})
    assert palettes.import_palette("web", []).name == "web (3)"
    assert palettes.import_palette("Marca", []).name == "Marca"
    assert palettes.import_palette("Marca", []).name == "Marca (2)"


@pytest.mark.spec("PAL-015")
def test_an_imported_name_is_cleaned_and_cut_to_40_characters() -> None:
    palettes = Palettes()
    assert palettes.import_palette("  Web  ", []).name == "Web"
    assert palettes.import_palette("a" * 50, []).name == "a" * 40
    assert palettes.import_palette("a" * 50, []).name == "a" * 36 + " (2)"
    assert palettes.import_palette("   ", []).name == IMPORTED_NAME
    assert IMPORTED_NAME == "Paleta importada"


@pytest.mark.spec("PAL-015")
def test_an_imported_name_cut_before_the_number_loses_its_trailing_spaces() -> None:
    palettes = Palettes({"a" * 35 + " bcd": []})
    assert palettes.import_palette("a" * 35 + " bcd", []).name == "a" * 35 + " (2)"


@pytest.mark.spec("PAL-015")
def test_an_import_drops_repeated_colours_and_keeps_the_first_20() -> None:
    palettes = Palettes()
    colors = [RED, BLUE, RED, *numbered(25)]
    imported = palettes.import_palette("Muchos", colors)
    assert imported == Imported("Muchos", 20, 27)
    assert palettes.colors() == (RED, BLUE, *numbered(18))


@pytest.mark.spec("PAL-015")
def test_an_import_without_repeats_keeps_their_order() -> None:
    palettes = Palettes()
    palettes.import_palette("Web", [RED, BLUE, RED])
    assert palettes.colors() == (RED, BLUE)
