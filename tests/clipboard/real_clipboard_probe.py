"""Sonda para los tests del adaptador real del portapapeles.

Se ejecuta en un subproceso con la plataforma Qt de Windows. Guarda el texto que hubiera
en el portapapeles y lo restaura al terminar. Escribe el resultado en JSON.
"""

import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes
from typing import Any

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication

from pxls.adapters.qt_clipboard import QtClipboard
from pxls.core.clipboard import ClipboardError

CF_UNICODETEXT = 13
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32.OpenClipboard.argtypes = (wintypes.HWND,)
_user32.GetClipboardData.restype = ctypes.c_void_p
_user32.GetClipboardData.argtypes = (wintypes.UINT,)
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalLock.argtypes = (ctypes.c_void_p,)
_kernel32.GlobalUnlock.argtypes = (ctypes.c_void_p,)

LOCKER = (
    "import ctypes, sys, time\n"
    "ctypes.windll.user32.OpenClipboard(None)\n"
    "print('bloqueado', flush=True)\n"
    "time.sleep(float(sys.argv[1]))\n"
    "ctypes.windll.user32.CloseClipboard()\n"
)


def system_clipboard_text() -> str | None:
    """Lee el texto del portapapeles con la API de Windows, sin pasar por Qt."""
    if not _user32.OpenClipboard(None):
        return None
    try:
        handle = _user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        pointer = _kernel32.GlobalLock(handle)
        try:
            return ctypes.wstring_at(pointer)
        finally:
            _kernel32.GlobalUnlock(handle)
    finally:
        _user32.CloseClipboard()


def saved_clipboard(app: QApplication) -> QMimeData:
    """Copia todos los formatos del portapapeles (texto, imágenes…) para restaurarlos."""
    saved = QMimeData()
    source = app.clipboard().mimeData()
    for name in source.formats():
        saved.setData(name, source.data(name))
    return saved


def same_text(first: str, second: str) -> bool:
    """Compara textos sin tener en cuenta si los saltos de línea son \\r\\n o \\n."""
    return first.replace("\r\n", "\n") == second.replace("\r\n", "\n")


app = QApplication([])
original = app.clipboard().text()
saved = saved_clipboard(app)
result: dict[str, Any] = {}
try:
    QtClipboard().set_text("pxls #FF8800FF")
    result["written"] = system_clipboard_text()
    locker = subprocess.Popen(
        [sys.executable, "-c", LOCKER, "3"], stdout=subprocess.PIPE, text=True
    )
    assert locker.stdout is not None
    locker.stdout.readline()
    started = time.perf_counter()
    try:
        QtClipboard().set_text("pxls bloqueado")
        result["locked"] = "sin error"
    except ClipboardError as error:
        result["locked"] = str(error)
    result["locked_seconds"] = round(time.perf_counter() - started, 1)
    locker.wait(timeout=10)
finally:
    app.clipboard().setMimeData(saved)
    result["restored"] = same_text(system_clipboard_text() or "", original)
print(json.dumps(result))
