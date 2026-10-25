"""Fakes y proyectos de ejemplo compartidos por los tests de spec-anchor."""

import os
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

import pytest

from spec_anchor.hooks import install
from spec_anchor.tree import Tree

# Comando con el que los hooks de los proyectos de ejemplo llaman a spec-anchor.
RUNNER = f'"{Path(sys.executable).as_posix()}" -m spec_anchor'


class MemoryTree:
    """Árbol de ficheros en memoria que implementa el puerto ``Tree``."""

    def __init__(self, files: dict[str, str]) -> None:
        self._files = dict(files)

    def files(self) -> Iterable[str]:
        return list(self._files)

    def read(self, path: str) -> str:
        return self._files[path]


@pytest.fixture
def make_tree() -> Callable[[dict[str, str]], Tree]:
    return MemoryTree


PYPROJECT = """\
[tool.mypy]
files = ["src"]
mypy_path = "src"
explicit_package_bases = true

[tool.pytest.ini_options]
markers = ["spec(*ids): requisitos que prueba el test"]

[tool.coverage.run]
branch = true
source = ["src/pxls"]

[tool.importlinter]
root_package = "pxls"

[[tool.importlinter.contracts]]
name = "Capas"
type = "layers"
layers = ["pxls.ui", "pxls.adapters", "pxls.core"]
"""

SPEC = """\
---
capability: demo
prefix: DEMO
owner: Bartosz Kucmierz
---

# Demo

## Requisitos

### DEMO-001 · Duplicar

- **Estado:** implemented
- **Enunciado (EARS):** El sistema deberá duplicar un número.
- **Criterios de aceptación:**
  1. Dado 2, cuando se duplica, entonces el resultado es 4.
"""

MODULE = '''\
"""Demo.

Spec: DEMO-001
"""


def double(x: int) -> int:
    """Duplica un número."""
    return 2 * x
'''

TESTS = """\
import pytest

from pxls.core.demo import double


@pytest.mark.spec("DEMO-001")
def test_double() -> None:
    assert double(2) == 4
"""

GITIGNORE = """\
ignored.txt
__pycache__/
.coverage
.mypy_cache/
.ruff_cache/
.pytest_cache/
.import_linter_cache/
"""

FILES = {
    "pyproject.toml": PYPROJECT,
    ".gitignore": GITIGNORE,
    "specs/demo/spec.md": SPEC,
    "src/pxls/__init__.py": '"""pxls."""\n',
    "src/pxls/core/__init__.py": '"""Dominio."""\n',
    "src/pxls/adapters/__init__.py": '"""Adaptadores."""\n',
    "src/pxls/ui/__init__.py": '"""Interfaz."""\n',
    "src/pxls/core/demo.py": MODULE,
    "tests/test_demo.py": TESTS,
}


class Project:
    """Repositorio git temporal con un proyecto mínimo que pasa todas las verificaciones."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        # Sin las variables GIT_* que exporta un hook: apuntarían al repositorio real.
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            check=check,
        )

    def read(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8")

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def replace(self, path: str, old: str, new: str) -> None:
        text = self.read(path)
        assert old in text, f"{old!r} no está en {path}"
        self.write(path, text.replace(old, new))


def _make_project(root: Path) -> Project:
    project = Project(root)
    project.git("init", "-q", "-b", "dev")
    project.git("config", "user.email", "test@example.com")
    project.git("config", "user.name", "Test")
    project.git("config", "core.autocrlf", "false")
    for path, text in FILES.items():
        project.write(path, text)
    project.git("add", "-A")
    return project


@pytest.fixture
def bare_project(tmp_path: Path) -> Project:
    """Proyecto mínimo correcto, sin los hooks de git instalados."""
    return _make_project(tmp_path)


@pytest.fixture
def project(tmp_path: Path) -> Project:
    """Proyecto mínimo correcto, con los hooks de git instalados."""
    project = _make_project(tmp_path)
    assert install(project.root, RUNNER) == []
    return project
