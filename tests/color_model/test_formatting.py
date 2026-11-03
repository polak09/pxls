import pytest

from pxls.core.color import Color
from pxls.core.formatting import to_rgb_text

# COLOR-005 · Escribir RGB


@pytest.mark.spec("COLOR-005")
@pytest.mark.parametrize(
    ("color", "text"),
    [
        (Color(255, 136, 0, 255), "rgb(255, 136, 0)"),
        (Color(0, 0, 0, 128), "rgba(0, 0, 0, 0.5)"),
        (Color(10, 20, 30, 64), "rgba(10, 20, 30, 0.25)"),
        (Color(10, 20, 30, 0), "rgba(10, 20, 30, 0)"),
        (Color(10, 20, 30, 191), "rgba(10, 20, 30, 0.75)"),
    ],
)
def test_rgb_text_shows_alpha_only_when_not_opaque(color: Color, text: str) -> None:
    assert to_rgb_text(color) == text
