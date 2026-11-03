# pxls

Color picker de escritorio para Windows. Antes de contribuir, lee [CONSTITUTION.md](CONSTITUTION.md); el plan está en [tareas.md](tareas.md).

## Ejecutar en local

Necesitas Windows, [uv](https://docs.astral.sh/uv/) y Python 3.13 instalado en el sistema (uv no lo descarga: `python-downloads = "never"`).

```bash
uv sync
uv run pxls
```

`uv sync` crea el entorno con las dependencias de desarrollo y `uv run pxls` abre la aplicación.

### Generar el ejecutable

```bash
uv run pyinstaller --noconfirm pxls.spec
```

Deja un único `dist/pxls.exe` que funciona sin Python.

### Comprobar el proyecto

| Para | Comando |
|---|---|
| Tests | `uv run pytest` |
| Verificación rápida | `uv run spec-anchor check --quick` |
| Verificación completa | `uv run spec-anchor check --full` |
| Instalar los hooks de git | `uv run spec-anchor install` |
