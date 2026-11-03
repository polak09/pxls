import ctypes
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PySide6.QtGui import QIcon, QImage
from pytestqt.qtbot import QtBot

from pxls.ui.main_window import icon_path

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def executable(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Genera el ejecutable una sola vez por sesión y lo arranca una vez para calentarlo."""
    work = tmp_path_factory.mktemp("pyinstaller")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--distpath",
        str(work / "dist"),
        "--workpath",
        str(work / "build"),
        str(REPO / "pxls.spec"),
    ]
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr[-2000:]
    exe = work / "dist" / "pxls.exe"
    subprocess.run([str(exe), "--smoke-test"], timeout=60, check=False)
    return exe


def smoke(exe: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([str(exe), "--smoke-test"], env=env, timeout=10, check=False)


def environment_without_python() -> dict[str, str]:
    system = os.environ["SYSTEMROOT"]
    removed = ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "QT_QPA_PLATFORM")
    env = {key: value for key, value in os.environ.items() if key not in removed}
    env["PATH"] = os.pathsep.join([str(Path(system) / "System32"), system])
    return env


# APP-008 · Ejecutable de Windows


@pytest.mark.spec("APP-008")
def test_packaging_generates_a_single_pxls_exe(executable: Path) -> None:
    assert [path.name for path in executable.parent.iterdir()] == ["pxls.exe"]


@pytest.mark.spec("APP-008")
def test_executable_runs_outside_the_project_without_python(
    executable: Path, tmp_path: Path
) -> None:
    copy = tmp_path / "otra carpeta" / "pxls.exe"
    copy.parent.mkdir()
    shutil.copy2(executable, copy)
    env = environment_without_python()
    assert shutil.which("python", path=env["PATH"]) is None
    assert smoke(copy, env).returncode == 0


# APP-009 · Prueba de humo


@pytest.mark.spec("APP-009")
def test_smoke_test_of_the_executable_ends_with_0_in_less_than_10_seconds(
    executable: Path,
) -> None:
    assert smoke(executable).returncode == 0


# APP-001 · Arranque


@pytest.mark.spec("APP-001")
def test_executable_starts_in_less_than_5_seconds(executable: Path) -> None:
    start = time.perf_counter()
    assert smoke(executable).returncode == 0
    assert time.perf_counter() - start < 5


# APP-004 · Icono


def executable_icon(exe: Path) -> QImage:
    shell32 = ctypes.windll.shell32
    handle = ctypes.c_void_p()
    assert shell32.ExtractIconExW(str(exe), 0, ctypes.byref(handle), None, 1) == 1
    try:
        assert handle.value is not None
        return QImage.fromHICON(handle.value).convertToFormat(QImage.Format.Format_ARGB32)
    finally:
        ctypes.windll.user32.DestroyIcon(handle)


def mean_difference(first: QImage, second: QImage) -> float:
    total = 0
    for y in range(first.height()):
        for x in range(first.width()):
            a, b = first.pixelColor(x, y), second.pixelColor(x, y)
            channels_a = (a.red(), a.green(), a.blue(), a.alpha())
            channels_b = (b.red(), b.green(), b.blue(), b.alpha())
            total += sum(abs(i - j) for i, j in zip(channels_a, channels_b, strict=True))
    return total / (first.width() * first.height() * 4)


@pytest.mark.spec("APP-004")
def test_executable_has_the_pxls_icon(executable: Path, qtbot: QtBot) -> None:
    icon = executable_icon(executable)
    expected = QIcon(str(icon_path())).pixmap(icon.width()).toImage()
    expected = expected.convertToFormat(QImage.Format.Format_ARGB32)
    assert mean_difference(icon, expected) < 2
