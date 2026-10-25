"""Configuración de los tests del portapapeles: Qt sin pantalla.

El test del adaptador real usa el portapapeles de Windows desde un subproceso.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
