import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.color import Color
from pxls.core.history import LIMIT, History, HistoryFormatError, dump_history, load_history

RED = Color(255, 0, 0)
GREEN = Color(0, 255, 0)
BLUE = Color(0, 0, 255)

colors = st.builds(
    Color,
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
)


def numbered(count: int) -> list[Color]:
    return [Color(index, 0, 0) for index in range(count)]


# HIST-002 · Orden


@pytest.mark.spec("HIST-002")
def test_the_most_recent_colour_goes_first() -> None:
    history = History()
    for color in (RED, GREEN, BLUE):
        history.add(color)
    assert history.entries == (BLUE, GREEN, RED)


@pytest.mark.spec("HIST-002")
def test_a_new_history_is_empty() -> None:
    assert History().entries == ()


# HIST-003 · Límite


@pytest.mark.spec("HIST-003")
def test_the_limit_is_20_entries() -> None:
    assert LIMIT == 20


@pytest.mark.spec("HIST-003")
def test_a_full_history_drops_the_oldest_entry() -> None:
    oldest, *rest = numbered(LIMIT)
    history = History(reversed([oldest, *rest]))
    assert len(history.entries) == LIMIT
    history.add(BLUE)
    assert len(history.entries) == LIMIT
    assert history.entries[0] == BLUE
    assert oldest not in history.entries


@pytest.mark.spec("HIST-003")
def test_a_longer_initial_list_keeps_only_the_first_20() -> None:
    initial = numbered(LIMIT + 5)
    assert History(initial).entries == tuple(initial[:LIMIT])


@pytest.mark.spec("HIST-003", "HIST-004")
@given(st.lists(colors, max_size=60))
def test_any_sequence_of_uses_keeps_the_rules(used: list[Color]) -> None:
    history = History()
    for color in used:
        history.add(color)
    entries = history.entries
    assert len(entries) <= LIMIT
    assert len(set(entries)) == len(entries)
    if used:
        assert entries[0] == used[-1]


# HIST-004 · Duplicados


@pytest.mark.spec("HIST-004")
def test_a_repeated_colour_moves_to_the_front_instead_of_repeating() -> None:
    history = History([BLUE, RED])
    history.add(RED)
    assert history.entries == (RED, BLUE)


@pytest.mark.spec("HIST-004")
def test_using_the_first_colour_again_changes_nothing() -> None:
    history = History([BLUE, RED])
    seen: list[tuple[Color, ...]] = []
    history.on_change(seen.append)
    history.add(BLUE)
    assert history.entries == (BLUE, RED)
    assert seen == []


@pytest.mark.spec("HIST-004")
def test_an_initial_list_with_duplicates_keeps_the_first_occurrence() -> None:
    assert History([BLUE, RED, BLUE]).entries == (BLUE, RED)


# HIST-006 · Quitar y vaciar


@pytest.mark.spec("HIST-006")
def test_removing_an_entry_keeps_the_others_in_order() -> None:
    history = History([BLUE, RED])
    history.remove(BLUE)
    assert history.entries == (RED,)


@pytest.mark.spec("HIST-006")
def test_removing_a_colour_that_is_not_there_changes_nothing() -> None:
    history = History([BLUE])
    seen: list[tuple[Color, ...]] = []
    history.on_change(seen.append)
    history.remove(RED)
    assert history.entries == (BLUE,)
    assert seen == []


@pytest.mark.spec("HIST-006")
def test_clearing_empties_the_history() -> None:
    history = History([BLUE, RED])
    history.clear()
    assert history.entries == ()


# Avisos de cambio, que la vista y el almacén necesitan (HIST-006, HIST-007)


@pytest.mark.spec("HIST-006", "HIST-007")
def test_listeners_receive_every_change() -> None:
    history = History()
    seen: list[tuple[Color, ...]] = []
    history.on_change(seen.append)
    history.add(RED)
    history.add(BLUE)
    history.remove(RED)
    history.clear()
    assert seen == [(RED,), (BLUE, RED), (BLUE,), ()]


@pytest.mark.spec("HIST-006")
def test_clearing_an_empty_history_does_not_notify() -> None:
    history = History()
    seen: list[tuple[Color, ...]] = []
    history.on_change(seen.append)
    history.clear()
    assert seen == []


# HIST-007 · Conservar entre sesiones (formato)


@pytest.mark.spec("HIST-007")
def test_the_saved_text_lists_the_colours_in_hex_most_recent_first() -> None:
    assert json.loads(dump_history([BLUE, RED])) == {
        "version": 1,
        "colors": ["#0000FFFF", "#FF0000FF"],
    }


@pytest.mark.spec("HIST-007")
@given(st.lists(colors, max_size=LIMIT, unique=True))
def test_saving_and_loading_gives_the_same_colours_in_the_same_order(saved: list[Color]) -> None:
    assert load_history(dump_history(saved)) == tuple(saved)


# HIST-008 · Fichero del historial dañado (formato)


@pytest.mark.spec("HIST-008")
@pytest.mark.parametrize(
    "text",
    [
        "",
        "esto no es JSON",
        "[]",
        '{"colors": ["#FF0000FF"]}',
        '{"version": 2, "colors": ["#FF0000FF"]}',
        '{"version": 1}',
        '{"version": 1, "colors": "#FF0000FF"}',
        '{"version": 1, "colors": [16711935]}',
        '{"version": 1, "colors": ["#GG0000FF"]}',
    ],
)
def test_text_that_is_not_a_valid_history_is_rejected(text: str) -> None:
    with pytest.raises(HistoryFormatError):
        load_history(text)
