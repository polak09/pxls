import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.color import Color
from pxls.core.palette_formats import from_gpl, from_txt, loses_alpha, to_gpl, to_txt
from pxls.core.palettes import PaletteFormatError

RED = Color(255, 0, 0)
BLUE = Color(0, 0, 255)
HALF_BLUE = Color(0, 0, 255, 128)

colors = st.builds(
    Color,
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
)


def color_lines(text: str) -> list[list[str]]:
    lines = text.splitlines()
    start = lines.index("#") + 1
    return [line.split("\t")[0].split() for line in lines[start:]]


# PAL-014 · Exportar una paleta


@pytest.mark.spec("PAL-014")
def test_txt_has_one_hex_per_line() -> None:
    assert to_txt([RED, HALF_BLUE]).splitlines() == ["#FF0000FF", "#0000FF80"]


@pytest.mark.spec("PAL-014")
def test_gpl_has_the_header_the_name_and_each_colour() -> None:
    text = to_gpl("Web", [RED])
    lines = text.splitlines()
    assert lines[:4] == ["GIMP Palette", "Name: Web", "Columns: 10", "#"]
    assert color_lines(text) == [["255", "0", "0"]]
    assert lines[4] == "255   0   0\t#FF0000"


@pytest.mark.spec("PAL-014")
def test_gpl_writes_colours_without_their_transparency() -> None:
    assert color_lines(to_gpl("Web", [HALF_BLUE])) == [["0", "0", "255"]]


@pytest.mark.spec("PAL-014")
def test_only_gpl_loses_the_transparency_of_colours_that_are_not_opaque() -> None:
    assert loses_alpha(".gpl", [RED, HALF_BLUE])
    assert not loses_alpha(".gpl", [RED, BLUE])
    assert not loses_alpha(".txt", [HALF_BLUE])


# PAL-015 · Importar una paleta


@pytest.mark.spec("PAL-015")
def test_txt_is_read_line_by_line_ignoring_empty_lines() -> None:
    assert from_txt("#FF0000FF\n\n  #0000ff80  \r\n") == (RED, HALF_BLUE)


@pytest.mark.spec("PAL-015")
def test_an_empty_txt_is_an_empty_palette() -> None:
    assert from_txt("") == ()


@pytest.mark.spec("PAL-015")
def test_a_txt_line_that_is_not_a_colour_is_rejected() -> None:
    with pytest.raises(PaletteFormatError):
        from_txt("#FF0000FF\nrojo\n")


@pytest.mark.spec("PAL-015")
def test_gpl_gives_its_name_and_opaque_colours() -> None:
    text = "GIMP Palette\nName: Web \nColumns: 4\n# comentario\n\n255   0   0\tRojo\n0 0 255\n"
    assert from_gpl(text) == ("Web", (RED, BLUE))


@pytest.mark.spec("PAL-015")
def test_gpl_without_a_name_gives_none() -> None:
    assert from_gpl("GIMP Palette\n255 0 0\n") == (None, (RED,))


@pytest.mark.spec("PAL-015")
@pytest.mark.parametrize(
    "text",
    [
        "",
        "255 0 0\n",
        "GIMP Palette\n256 0 0\n",
        "GIMP Palette\n255 0\n",
        "GIMP Palette\nrojo verde azul\n",
        "GIMP Palette\n-1 0 0\n",
    ],
)
def test_text_that_is_not_a_gpl_palette_is_rejected(text: str) -> None:
    with pytest.raises(PaletteFormatError):
        from_gpl(text)


@pytest.mark.spec("PAL-014", "PAL-015")
@given(st.lists(colors, max_size=20))
def test_txt_keeps_every_colour_and_its_order(saved: list[Color]) -> None:
    assert from_txt(to_txt(saved)) == tuple(saved)


@pytest.mark.spec("PAL-014", "PAL-015")
@given(st.lists(colors, max_size=20))
def test_gpl_keeps_the_name_and_the_opaque_colours(saved: list[Color]) -> None:
    name, read = from_gpl(to_gpl("Paleta de prueba", saved))
    assert name == "Paleta de prueba"
    assert read == tuple(Color(color.red, color.green, color.blue) for color in saved)
