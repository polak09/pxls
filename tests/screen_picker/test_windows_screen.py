import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROBE = Path(__file__).with_name("real_screen_probe.py")
WHITE, BLACK, ORANGE = [255, 255, 255, 255], [0, 0, 0, 255], [255, 136, 0, 255]


@pytest.fixture(scope="module")
def probe() -> dict[str, Any]:
    env = {key: value for key, value in os.environ.items() if key != "QT_QPA_PLATFORM"}
    result = subprocess.run(
        [sys.executable, str(PROBE)],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    data: dict[str, Any] = json.loads(result.stdout.strip().splitlines()[-1])
    return data


@pytest.mark.spec("PICK-002")
def test_screenshot_keeps_the_colour_the_pixel_had_when_taken(probe: dict[str, Any]) -> None:
    # La sonda pinta de azul las ventanas después de capturar: la captura sigue en naranja.
    assert all(screen["centre"] == ORANGE for screen in probe["screens"])


@pytest.mark.spec("PICK-007")
def test_every_connected_screen_can_be_captured(probe: dict[str, Any]) -> None:
    assert len(probe["screens"]) >= 1
    assert [screen["centre"] for screen in probe["screens"]] == [ORANGE] * len(probe["screens"])


@pytest.mark.spec("PICK-008")
def test_alternating_physical_pixels_are_captured_exactly(probe: dict[str, Any]) -> None:
    for screen in probe["screens"]:
        expected = [[WHITE if (x + y) % 2 == 0 else BLACK for x in range(4)] for y in range(4)]
        assert screen["checker"] == expected


@pytest.mark.spec("PICK-006")
def test_pointer_moves_to_an_exact_physical_pixel(probe: dict[str, Any]) -> None:
    actual_x, actual_y, target_x, target_y = probe["pointer"]
    assert (actual_x, actual_y) == (target_x, target_y)
