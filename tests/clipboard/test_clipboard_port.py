import pytest
from hypothesis import given
from hypothesis import strategies as st

from pxls.core.clipboard import ClipboardError, copy_color
from pxls.core.color import Color
from pxls.core.formatting import FORMATS

channels = st.integers(min_value=0, max_value=255)
colors = st.builds(Color, channels, channels, channels, channels)


class RecordingClipboard:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def set_text(self, text: str) -> None:
        self.texts.append(text)


class LockedClipboard:
    def set_text(self, text: str) -> None:
        raise ClipboardError("otra aplicación tiene el portapapeles bloqueado")


# CLIP-001 · Copiar en un formato


@pytest.mark.spec("CLIP-001")
@pytest.mark.parametrize(
    ("hex_text", "name", "expected"),
    [
        ("#FF8800FF", "RGB", "rgb(255, 136, 0)"),
        ("#FF880080", "HSL", "hsla(32, 100%, 50%, 0.5)"),
        ("#FF8800FF", "HEX", "#FF8800FF"),
        ("#FF8800FF", "HSV", "hsv(32, 100%, 100%)"),
    ],
)
def test_copying_puts_exactly_the_format_text_in_the_clipboard(
    hex_text: str, name: str, expected: str
) -> None:
    clipboard = RecordingClipboard()
    assert copy_color(clipboard, Color.from_hex(hex_text), name) == expected
    assert clipboard.texts == [expected]


@pytest.mark.spec("CLIP-001")
@given(colors, st.sampled_from(sorted(FORMATS)))
def test_copied_text_is_the_text_the_panel_shows(color: Color, name: str) -> None:
    clipboard = RecordingClipboard()
    copy_color(clipboard, color, name)
    assert clipboard.texts == [FORMATS[name](color)]
    assert clipboard.texts[0] == clipboard.texts[0].strip()


@pytest.mark.spec("CLIP-001")
def test_the_four_formats_are_registered_in_order() -> None:
    assert list(FORMATS) == ["HEX", "RGB", "HSL", "HSV"]


# CLIP-005 · Portapapeles no disponible


@pytest.mark.spec("CLIP-005")
def test_a_clipboard_that_rejects_the_text_raises_clipboard_error() -> None:
    with pytest.raises(ClipboardError, match="bloqueado"):
        copy_color(LockedClipboard(), Color(1, 2, 3), "HEX")
