import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.color import Color, ColorError
from pxls.core.conversions import Hsv, from_hsv, to_hsv
from pxls.core.formatting import to_hsv_text

channels = st.integers(min_value=0, max_value=255)
colors = st.builds(Color, channels, channels, channels, channels)


def values(hsv: Hsv) -> tuple[float, float, float]:
    return hsv.hue, hsv.saturation, hsv.value


# COLOR-008 · Calcular HSV


@pytest.mark.spec("COLOR-008")
@pytest.mark.parametrize(
    ("color", "expected"),
    [(Color(255, 136, 0), (32, 100, 100)), (Color(102, 153, 204), (210, 50, 80))],
)
def test_hsv_of_a_color(color: Color, expected: tuple[float, float, float]) -> None:
    assert values(to_hsv(color)) == pytest.approx(expected)


@pytest.mark.spec("COLOR-008")
def test_grey_has_hue_and_saturation_0_in_hsv() -> None:
    hue, saturation, _ = values(to_hsv(Color(128, 128, 128)))
    assert (hue, saturation) == (0, 0)


# COLOR-009 · Escribir HSV


@pytest.mark.spec("COLOR-009")
@pytest.mark.parametrize(
    ("color", "text"),
    [
        (Color(102, 153, 204, 255), "hsv(210, 50%, 80%)"),
        (Color(255, 136, 0, 128), "hsva(32, 100%, 100%, 0.5)"),
        (Color(255, 0, 1, 255), "hsv(0, 100%, 100%)"),
    ],
)
def test_hsv_text_uses_whole_numbers(color: Color, text: str) -> None:
    assert to_hsv_text(color) == text


# COLOR-011 · Color desde HSV


@pytest.mark.spec("COLOR-011")
def test_color_from_hsv() -> None:
    assert from_hsv(210, 50, 80) == Color(102, 153, 204)


@pytest.mark.spec("COLOR-011")
def test_color_from_hsv_keeps_the_alpha() -> None:
    assert from_hsv(210, 50, 80, 7) == Color(102, 153, 204, 7)


# COLOR-012 · Valores HSV fuera de rango


@pytest.mark.spec("COLOR-012")
@pytest.mark.parametrize("hue", [-60, 300, 660])
def test_hsv_hue_goes_around_the_circle(hue: float) -> None:
    assert from_hsv(hue, 100, 100) == Color(255, 0, 255)


@pytest.mark.spec("COLOR-012")
@pytest.mark.parametrize(
    ("hsv", "reason"), [((0, -0.5, 50), "saturación"), ((0, 50, 101), "valor.*101")]
)
def test_hsv_saturation_or_value_out_of_range_is_rejected(
    hsv: tuple[float, float, float], reason: str
) -> None:
    with pytest.raises(ColorError, match=reason):
        from_hsv(*hsv)


# COLOR-013 · Ida y vuelta sin pérdidas (HSV)


@pytest.mark.spec("COLOR-013")
@given(colors)
def test_hsv_round_trip_returns_the_same_color(color: Color) -> None:
    hsv = to_hsv(color)
    assert from_hsv(hsv.hue, hsv.saturation, hsv.value, color.alpha) == color
