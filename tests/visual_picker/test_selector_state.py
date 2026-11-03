import pytest

from pxls.core.color import Color
from pxls.core.conversions import from_hsv
from pxls.core.selector import SelectorState

RED, WHITE, BLACK = Color(255, 0, 0), Color(255, 255, 255), Color(0, 0, 0)


def hsv(state: SelectorState) -> tuple[float, float, float]:
    return state.hue, state.saturation, state.value


def chosen(hue: float, saturation: float, value: float) -> SelectorState:
    """Estado con un tono, una saturación y un valor elegidos en el propio selector."""
    state = SelectorState(WHITE)
    state.set_hue(hue)
    state.set_sv(saturation, value)
    return state


# SEL-001 · Cuadrado de saturación y valor


@pytest.mark.spec("SEL-001")
@pytest.mark.parametrize(
    ("sv", "expected"),
    [((100, 100), RED), ((0, 100), WHITE), ((100, 0), BLACK), ((0, 0), BLACK)],
)
def test_saturation_and_value_set_the_colour_with_the_current_hue(
    sv: tuple[float, float], expected: Color
) -> None:
    state = SelectorState(WHITE)
    assert state.set_sv(*sv) == expected


@pytest.mark.spec("SEL-001")
def test_saturation_and_value_keep_the_hue_and_the_alpha() -> None:
    state = SelectorState(Color(255, 136, 0, 128))
    color = state.set_sv(50, 80)
    assert color.alpha == 128
    assert state.hue == pytest.approx(32)


@pytest.mark.spec("SEL-001")
def test_saturation_and_value_are_clamped_to_the_square() -> None:
    state = SelectorState(WHITE)
    state.set_sv(-20, 130)
    assert (state.saturation, state.value) == (0, 100)


# SEL-002 · Barra de tono


@pytest.mark.spec("SEL-002")
def test_hue_changes_only_the_hue() -> None:
    state = SelectorState(from_hsv(0, 50, 80))
    color = state.set_hue(120)
    assert color == from_hsv(120, 50, 80)
    assert (state.saturation, state.value) == pytest.approx((50, 80))


@pytest.mark.spec("SEL-002")
def test_red_with_hue_120_is_green() -> None:
    assert SelectorState(RED).set_hue(120) == Color(0, 255, 0)


# SEL-004 · Conservar tono y saturación


@pytest.mark.spec("SEL-004")
def test_hue_and_saturation_survive_black() -> None:
    state = chosen(200, 80, 90)
    assert state.set_sv(80, 0) == BLACK
    state.set_sv(80, 90)
    assert hsv(state) == pytest.approx((200, 80, 90))


@pytest.mark.spec("SEL-004")
def test_hue_survives_grey() -> None:
    state = chosen(200, 80, 90)
    state.set_sv(0, 90)
    state.set_sv(60, 90)
    assert state.hue == pytest.approx(200)


@pytest.mark.spec("SEL-004")
def test_black_from_outside_keeps_hue_and_saturation() -> None:
    state = chosen(200, 80, 90)
    state.sync(BLACK)
    assert hsv(state) == pytest.approx((200, 80, 0))
    assert state.color == BLACK


@pytest.mark.spec("SEL-004")
def test_grey_from_outside_keeps_the_hue() -> None:
    state = chosen(200, 80, 90)
    state.sync(Color(128, 128, 128))
    assert state.hue == pytest.approx(200)
    assert state.saturation == 0


@pytest.mark.spec("SEL-004")
def test_the_same_colour_from_outside_changes_nothing() -> None:
    state = chosen(200, 80, 90)
    state.set_sv(80, 0)
    state.sync(BLACK)
    assert hsv(state) == pytest.approx((200, 80, 0))


@pytest.mark.spec("SEL-004")
def test_a_coloured_colour_from_outside_replaces_hue_saturation_and_value() -> None:
    state = SelectorState(WHITE)
    state.sync(Color(255, 136, 0, 64))
    assert hsv(state) == pytest.approx((32, 100, 100))
    assert state.color == Color(255, 136, 0, 64)
