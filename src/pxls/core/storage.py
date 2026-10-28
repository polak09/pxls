"""Errores comunes de los datos que pxls guarda en el perfil del usuario.

Spec: PAL-013
"""


class SaveError(Exception):
    """No se han podido guardar los datos en ``location``."""

    def __init__(self, location: str) -> None:
        """Guarda dónde se intentaban guardar los datos."""
        super().__init__(location)
        self.location = location
