import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.color import Color, ColorError
from pxls.core.conversions import Hsl, from_hsl, to_hsl
from pxls.core.formatting import to_hsl_text

channels = st.integers(min_value=0, max_value=255)
colors = st.builds(Color, channels, channels, channels, channels)


def values(hsl: Hsl) -> tuple[float, float, float]:
    return hsl.hue, hsl.saturation, hsl.lightness


# COLOR-006 · Calcular HSL


@pytest.mark.spec("COLOR-006")
@pytest.mark.parametrize(
    ("color", "expected"),
    [(Color(255, 0, 0), (0, 100, 50)), (Color(255, 136, 0), (32, 100, 50))],
)
def test_hsl_of_a_color(color: Color, expected: tuple[float, float, float]) -> None:
    assert values(to_hsl(color)) == pytest.approx(expected)


@pytest.mark.spec("COLOR-006")
def test_grey_has_hue_and_saturation_0() -> None:
    hue, saturation, lightness = values(to_hsl(Color(128, 128, 128)))
    assert (hue, saturation) == (0, 0)
    assert 50.1 <= lightness <= 50.2


# COLOR-007 · Escribir HSL


@pytest.mark.spec("COLOR-007")
@pytest.mark.parametrize(
    ("color", "text"),
    [
        (Color(255, 136, 0, 255), "hsl(32, 100%, 50%)"),
        (Color(128, 128, 128, 255), "hsl(0, 0%, 50%)"),
        (Color(255, 0, 1, 255), "hsl(0, 100%, 50%)"),
        (Color(255, 136, 0, 128), "hsla(32, 100%, 50%, 0.5)"),
    ],
)
def test_hsl_text_uses_whole_numbers(color: Color, text: str) -> None:
    assert to_hsl_text(color) == text


# COLOR-010 · Color desde HSL


@pytest.mark.spec("COLOR-010")
@pytest.mark.parametrize(
    ("hsl", "expected"),
    [
        ((32, 100, 50), Color(255, 136, 0)),
        ((0, 0, 100), Color(255, 255, 255)),
        ((0, 0, 0), Color(0, 0, 0)),
    ],
)
def test_color_from_hsl(hsl: tuple[float, float, float], expected: Color) -> None:
    assert from_hsl(*hsl) == expected


@pytest.mark.spec("COLOR-010")
def test_color_from_hsl_keeps_the_alpha() -> None:
    assert from_hsl(32, 100, 50, 128) == Color(255, 136, 0, 128)


@pytest.mark.spec("COLOR-010")
def test_ties_are_rounded_up() -> None:
    # L 50 % da exactamente 127,5 en cada canal: el empate sube a 128.
    assert from_hsl(0, 0, 50) == Color(128, 128, 128)


# COLOR-012 · Valores HSL fuera de rango


@pytest.mark.spec("COLOR-012")
@pytest.mark.parametrize("hue", [420, 60, -300])
def test_hue_goes_around_the_circle(hue: float) -> None:
    assert from_hsl(hue, 100, 50) == Color(255, 255, 0)


@pytest.mark.spec("COLOR-012")
@pytest.mark.parametrize(
    ("hsl", "reason"),
    [((0, 101, 50), "saturación.*101"), ((0, 50, -1), "luminosidad.*-1")],
)
def test_saturation_or_lightness_out_of_range_is_rejected(
    hsl: tuple[float, float, float], reason: str
) -> None:
    with pytest.raises(ColorError, match=reason):
        from_hsl(*hsl)


# COLOR-013 · Ida y vuelta sin pérdidas (HSL)


@pytest.mark.spec("COLOR-013")
@given(colors)
def test_hsl_round_trip_returns_the_same_color(color: Color) -> None:
    hsl = to_hsl(color)
    assert from_hsl(hsl.hue, hsl.saturation, hsl.lightness, color.alpha) == color
