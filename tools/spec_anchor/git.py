"""Consultas al repositorio git.

Spec: ANCH-028, ANCH-029, ANCH-030, ANCH-034, ANCH-040
"""

import os
import subprocess
from pathlib import Path

from spec_anchor.model import Finding


def git_output(root: Path, *args: str) -> str:
    """Ejecuta ``git`` en ``root`` y devuelve su salida estándar."""
    return _git(root, *args, check=True).stdout


def git_paths(root: Path, *args: str) -> list[str]:
    """Ejecuta un comando de git con ``-z`` y devuelve las rutas que lista, sin repetir."""
    paths = git_output(root, *args, "-z").split("\0")
    return list(dict.fromkeys(path for path in paths if path))


def repo_root(start: Path) -> Path:
    """Devuelve la raíz del repositorio que contiene ``start``."""
    return Path(git_output(start, "rev-parse", "--show-toplevel").strip())


def current_branch(root: Path) -> str:
    """Devuelve la rama actual, o una cadena vacía si ``HEAD`` está separado."""
    result = _git(root, "symbolic-ref", "--short", "-q", "HEAD", check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def revision(root: Path, name: str) -> str | None:
    """Devuelve el commit al que apunta ``name``, o ``None`` si no existe."""
    result = _git(root, "rev-parse", "-q", "--verify", f"{name}^{{commit}}", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def merge_sources(root: Path) -> list[str]:
    """Devuelve los commits que integra el merge en curso; ninguno si no hay merge.

    Tras un conflicto, git deja ``MERGE_HEAD``; durante ``pre-merge-commit`` no lo
    escribe, pero exporta ``GIT_REFLOG_ACTION`` con las ramas que se integran.
    """
    merge_file = root / git_output(root, "rev-parse", "--git-path", "MERGE_HEAD").strip()
    if merge_file.is_file():
        return [line.strip() for line in merge_file.read_text().splitlines() if line.strip()]
    action = os.environ.get("GIT_REFLOG_ACTION", "")
    if not action.startswith("merge "):
        return []
    names = [token for token in action.split()[1:] if not token.startswith("-")]
    return [commit for name in names if (commit := revision(root, name)) is not None]


def staged_paths(root: Path) -> list[str]:
    """Devuelve las rutas que cambian en el commit en curso respecto a ``HEAD``."""
    if revision(root, "HEAD") is None:
        return git_paths(root, "ls-files", "--cached")
    return git_paths(root, "diff", "--cached", "--name-only")


def uncommitted_changes(root: Path) -> list[Finding]:
    """Lista los cambios sin preparar y los ficheros sin seguimiento no ignorados (ANCH-034)."""
    unstaged = git_paths(root, "diff", "--name-only")
    untracked = git_paths(root, "ls-files", "--others", "--exclude-standard")
    return [
        *(Finding("ANCH-034", "tiene cambios sin preparar", path) for path in unstaged),
        *(Finding("ANCH-034", "no tiene seguimiento ni está ignorado", path) for path in untracked),
    ]


def _git(root: Path, *args: str, check: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )
