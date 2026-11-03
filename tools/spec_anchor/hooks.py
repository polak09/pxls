"""Instalación y comprobación de los hooks de git.

Spec: ANCH-038, ANCH-039, ANCH-041
"""

from pathlib import Path

from spec_anchor.git import git_output
from spec_anchor.model import Finding

HOOK_NAMES = ("pre-commit", "pre-merge-commit", "commit-msg")
MARKER = "# managed-by: spec-anchor"
DEFAULT_RUNNER = "uv run --frozen spec-anchor"
INSTALL_COMMAND = "uv run spec-anchor install"


def hooks_dir(root: Path) -> Path:
    """Devuelve la carpeta de hooks del clon, respetando ``core.hooksPath``."""
    return root / git_output(root, "rev-parse", "--git-path", "hooks").strip()


def install(root: Path, runner: str = DEFAULT_RUNNER) -> list[Finding]:
    """Instala los hooks del sistema sin sobrescribir hooks ajenos (ANCH-038, ANCH-039)."""
    directory = hooks_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    findings: list[Finding] = []
    for name in HOOK_NAMES:
        hook = directory / name
        if hook.exists() and not _is_ours(hook):
            text = f"ya hay un hook `{name}` ajeno a spec-anchor: quítalo a mano e instala de nuevo"
            findings.append(Finding("ANCH-039", text))
            continue
        hook.write_text(_script(name, runner), encoding="utf-8", newline="\n")
        hook.chmod(0o755)
    return findings


def check_hooks_installed(root: Path) -> list[Finding]:
    """Comprueba que los tres hooks del sistema están instalados (ANCH-041)."""
    directory = hooks_dir(root)
    missing = [name for name in HOOK_NAMES if not _is_ours(directory / name)]
    if not missing:
        return []
    text = f"faltan los hooks de git {', '.join(missing)}: instálalos con `{INSTALL_COMMAND}`"
    return [Finding("ANCH-041", text)]


def _is_ours(hook: Path) -> bool:
    return hook.is_file() and MARKER in hook.read_text(encoding="utf-8", errors="replace")


def _script(name: str, runner: str) -> str:
    return f'#!/bin/sh\n{MARKER}\nexec {runner} hook {name} "$@"\n'
