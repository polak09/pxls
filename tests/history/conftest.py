"""Configuración de los tests del historial: Qt sin pantalla."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
