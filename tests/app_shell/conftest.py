"""Configuración de los tests de la interfaz: Qt sin pantalla."""

import os

# Antes de que pytest-qt cree la aplicación: los tests no abren ventanas reales.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
