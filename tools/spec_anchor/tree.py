"""Acceso de sólo lectura a los ficheros del repositorio.

Spec: ANCH-001, ANCH-021, ANCH-030
"""

from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from spec_anchor.git import git_output, git_paths, revision


class Tree(Protocol):
    """Árbol de ficheros con rutas POSIX relativas a la raíz del repositorio."""

    def files(self) -> Iterable[str]:
        """Devuelve las rutas de todos los ficheros del árbol."""
        ...

    def read(self, path: str) -> str:
        """Devuelve el contenido de ``path`` como texto."""
        ...


class DiskTree:
    """Copia de trabajo: ficheros en disco con seguimiento o no ignorados por git."""

    def __init__(self, root: Path) -> None:
        """Crea el árbol de la copia de trabajo del repositorio ``root``."""
        self.root = root

    def files(self) -> Iterable[str]:
        """Devuelve los ficheros con seguimiento o sin ignorar que existen en disco."""
        listed = git_paths(self.root, "ls-files", "--cached", "--others", "--exclude-standard")
        deleted = set(git_paths(self.root, "ls-files", "--deleted"))
        return [path for path in dict.fromkeys(listed) if path not in deleted]

    def read(self, path: str) -> str:
        """Devuelve el contenido en disco de ``path``."""
        return (self.root / path).read_text(encoding="utf-8")


class GitTree:
    """Árbol de una revisión de git o, con ``revision=None``, del índice (lo preparado)."""

    def __init__(self, root: Path, revision: str | None) -> None:
        """Crea el árbol de ``revision`` (o del índice) del repositorio ``root``."""
        self.root = root
        self.revision = revision

    def files(self) -> Iterable[str]:
        """Devuelve los ficheros de la revisión; ninguno si la revisión no existe."""
        if self.revision is None:
            return git_paths(self.root, "ls-files", "--cached")
        if revision(self.root, self.revision) is None:
            return []
        return git_paths(self.root, "ls-tree", "-r", "--name-only", self.revision)

    def read(self, path: str) -> str:
        """Devuelve el contenido de ``path`` en la revisión o en el índice."""
        return git_output(self.root, "show", f"{self.revision or ''}:{path}")
