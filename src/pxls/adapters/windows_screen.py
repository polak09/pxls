"""Captura del escritorio y control del cursor con la API de Windows, en píxeles físicos.

Spec: PICK-002, PICK-006, PICK-007, PICK-008
"""

import ctypes
from collections.abc import Iterator
from contextlib import contextmanager
from ctypes import wintypes

from pxls.core.screen import BgraScreenshot, Point, Rect

_PER_MONITOR_AWARE_V2 = -4
_VIRTUAL_SCREEN_METRICS = (76, 77, 78, 79)  # SM_X/YVIRTUALSCREEN, SM_CX/CYVIRTUALSCREEN
_SRCCOPY = 0x00CC0020
_CAPTUREBLT = 0x40000000
_BI_RGB = 0
_DIB_RGB_COLORS = 0


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = (
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    )


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
_HANDLE = ctypes.c_void_p
_INT = ctypes.c_int
_UINT = wintypes.UINT


def _declare(library: ctypes.WinDLL, name: str, restype: type, *argtypes: type) -> None:
    # Firmas explícitas: sin ellas ctypes trunca los handles de 64 bits a 32.
    function = getattr(library, name)
    function.restype, function.argtypes = restype, argtypes


_declare(_user32, "SetThreadDpiAwarenessContext", _HANDLE, _HANDLE)
_declare(_user32, "GetSystemMetrics", _INT, _INT)
_declare(_user32, "GetDC", _HANDLE, _HANDLE)
_declare(_user32, "ReleaseDC", _INT, _HANDLE, _HANDLE)
_declare(_user32, "GetCursorPos", wintypes.BOOL, ctypes.POINTER(wintypes.POINT))
_declare(_user32, "SetCursorPos", wintypes.BOOL, _INT, _INT)
_declare(_gdi32, "CreateCompatibleDC", _HANDLE, _HANDLE)
_declare(_gdi32, "CreateCompatibleBitmap", _HANDLE, _HANDLE, _INT, _INT)
_declare(_gdi32, "SelectObject", _HANDLE, _HANDLE, _HANDLE)
_declare(
    _gdi32,
    "BitBlt",
    wintypes.BOOL,
    _HANDLE,
    _INT,
    _INT,
    _INT,
    _INT,
    _HANDLE,
    _INT,
    _INT,
    wintypes.DWORD,
)
_declare(_gdi32, "GetDIBits", _INT, _HANDLE, _HANDLE, _UINT, _UINT, _HANDLE, _HANDLE, _UINT)
_declare(_gdi32, "DeleteObject", wintypes.BOOL, _HANDLE)
_declare(_gdi32, "DeleteDC", wintypes.BOOL, _HANDLE)


@contextmanager
def _physical_coordinates() -> Iterator[None]:
    """Marca el hilo como *per-monitor DPI aware v2* para trabajar en píxeles físicos."""
    previous = _user32.SetThreadDpiAwarenessContext(_PER_MONITOR_AWARE_V2)
    try:
        yield
    finally:
        _user32.SetThreadDpiAwarenessContext(previous)


class WindowsScreenGrabber:
    """Captura todo el escritorio virtual con GDI (PICK-002, PICK-007, PICK-008)."""

    def grab(self) -> BgraScreenshot:
        """Devuelve una copia en memoria de todas las pantallas, en píxeles físicos."""
        with _physical_coordinates():
            x, y, width, height = (_user32.GetSystemMetrics(i) for i in _VIRTUAL_SCREEN_METRICS)
            screen_dc = _user32.GetDC(None)
            memory_dc = _gdi32.CreateCompatibleDC(screen_dc)
            bitmap = _gdi32.CreateCompatibleBitmap(screen_dc, width, height)
            try:
                previous = _gdi32.SelectObject(memory_dc, bitmap)
                copied = _gdi32.BitBlt(
                    memory_dc, 0, 0, width, height, screen_dc, x, y, _SRCCOPY | _CAPTUREBLT
                )
                _gdi32.SelectObject(memory_dc, previous)
                if not copied:
                    raise ctypes.WinError(ctypes.get_last_error())
                header = _BitmapInfoHeader(
                    ctypes.sizeof(_BitmapInfoHeader), width, -height, 1, 32, _BI_RGB, 0, 0, 0, 0, 0
                )
                pixels = ctypes.create_string_buffer(width * height * 4)
                lines = _gdi32.GetDIBits(
                    memory_dc, bitmap, 0, height, pixels, ctypes.byref(header), _DIB_RGB_COLORS
                )
                if lines != height:
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                _gdi32.DeleteObject(bitmap)
                _gdi32.DeleteDC(memory_dc)
                _user32.ReleaseDC(None, screen_dc)
        return BgraScreenshot(Rect(x, y, width, height), pixels.raw)


class WindowsPointer:
    """Lee y mueve el cursor en píxeles físicos (PICK-006)."""

    def position(self) -> Point:
        """Devuelve la posición del cursor en el escritorio virtual."""
        point = wintypes.POINT()
        with _physical_coordinates():
            if not _user32.GetCursorPos(ctypes.byref(point)):
                raise ctypes.WinError(ctypes.get_last_error())
        return Point(point.x, point.y)

    def move_to(self, point: Point) -> None:
        """Lleva el cursor al píxel físico indicado."""
        with _physical_coordinates():
            if not _user32.SetCursorPos(point.x, point.y):
                raise ctypes.WinError(ctypes.get_last_error())
