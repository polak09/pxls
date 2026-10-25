import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROBE = Path(__file__).with_name("real_clipboard_probe.py")


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


@pytest.mark.spec("CLIP-001")
def test_text_reaches_the_windows_clipboard(probe: dict[str, Any]) -> None:
    assert probe["written"] == "pxls #FF8800FF"


@pytest.mark.spec("CLIP-005")
def test_a_locked_clipboard_is_reported(probe: dict[str, Any]) -> None:
    assert probe["locked"] != "sin error"
    assert "portapapeles" in probe["locked"]


@pytest.mark.spec("CLIP-001")
def test_the_previous_clipboard_text_is_restored(probe: dict[str, Any]) -> None:
    assert probe["restored"]
