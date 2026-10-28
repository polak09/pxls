"""Configuración de los tests de las paletas: Qt sin pantalla."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
