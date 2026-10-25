"""Configuración de los tests del cuentagotas: Qt sin pantalla.

Los tests del adaptador real usan la pantalla de verdad desde un subproceso.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
