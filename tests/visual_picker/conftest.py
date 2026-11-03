"""Configuración de los tests del selector visual: Qt sin pantalla."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
