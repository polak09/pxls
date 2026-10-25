# Configuración de PyInstaller: genera pxls.exe, un único fichero sin consola.
# Uso: uv run pyinstaller --noconfirm pxls.spec  (ver specs/app-shell/design.md)
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

ROOT = Path(SPECPATH)
ASSETS = ROOT / "src" / "pxls" / "ui" / "assets"

analysis = Analysis(
    [str(ROOT / "src" / "pxls" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    datas=[(str(ASSETS), "pxls/ui/assets"), *copy_metadata("pxls")],
    excludes=["tkinter"],
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    name="pxls",
    icon=str(ASSETS / "pxls.ico"),
    console=False,
    upx=False,
)
