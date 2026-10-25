import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.color import Color, ColorError

channels = st.integers(min_value=0, max_value=255)
colors = st.builds(Color, channels, channels, channels, channels)


# COLOR-001 · Color con alfa


@pytest.mark.spec("COLOR-001")
def test_color_keeps_its_four_components() -> None:
    color = Color(255, 136, 0, 255)
    assert (color.red, color.green, color.blue, color.alpha) == (255, 136, 0, 255)


@pytest.mark.spec("COLOR-001")
@pytest.mark.parametrize(
    ("components", "name"),
    [
        ((256, 0, 0, 255), "rojo"),
        ((0, -1, 0, 255), "verde"),
        ((0, 0, 300, 255), "azul"),
        ((0, 0, 0, 256), "alfa"),
    ],
)
def test_component_out_of_range_is_rejected_naming_it(
    components: tuple[int, int, int, int], name: str
) -> None:
    with pytest.raises(ColorError, match=name):
        Color(*components)


@pytest.mark.spec("COLOR-001")
def test_colors_with_the_same_components_are_equal() -> None:
    assert Color(1, 2, 3, 4) == Color(1, 2, 3, 4)
    assert Color(1, 2, 3, 4) != Color(1, 2, 3, 5)


@pytest.mark.spec("COLOR-001")
def test_alpha_defaults_to_opaque() -> None:
    assert Color(1, 2, 3).alpha == 255
    assert Color(1, 2, 3).opaque
    assert not Color(1, 2, 3, 254).opaque


# COLOR-002 · Leer HEX


@pytest.mark.spec("COLOR-002")
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("#FF8800FF", Color(255, 136, 0, 255)),
        ("#ff880080", Color(255, 136, 0, 128)),
        ("#FF8800", Color(255, 136, 0, 255)),
        ("#F808", Color(255, 136, 0, 136)),
        ("  f80 ", Color(255, 136, 0, 255)),
    ],
)
def test_hex_variants_are_read(text: str, expected: Color) -> None:
    assert Color.from_hex(text) == expected


# COLOR-003 · HEX no válido


@pytest.mark.spec("COLOR-003")
@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("#GG0000FF", "`G` no es un dígito hexadecimal"),
        ("#12345", "longitud"),
        ("", "vacío"),
        ("   ", "vacío"),
        ("##FF8800", "`#` no es un dígito hexadecimal"),
        ("0x12345678", "`x` no es un dígito hexadecimal"),
    ],
)
def test_invalid_hex_is_rejected_explaining_why(text: str, reason: str) -> None:
    with pytest.raises(ColorError, match=reason):
        Color.from_hex(text)


# COLOR-004 · Escribir HEX


@pytest.mark.spec("COLOR-004")
@pytest.mark.parametrize(
    ("color", "text"),
    [
        (Color(255, 136, 0, 255), "#FF8800FF"),
        (Color(0, 0, 0, 128), "#00000080"),
        (Color(10, 11, 12, 0), "#0A0B0C00"),
    ],
)
def test_hex_is_written_with_alpha_in_uppercase(color: Color, text: str) -> None:
    assert color.to_hex() == text


# COLOR-013 · Ida y vuelta sin pérdidas (HEX)


@pytest.mark.spec("COLOR-013")
@given(colors)
def test_writing_and_reading_hex_gives_the_same_color(color: Color) -> None:
    assert Color.from_hex(color.to_hex()) == color
