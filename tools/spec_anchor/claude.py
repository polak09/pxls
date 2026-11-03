"""Hooks de Claude Code: verificación al final de cada turno y guarda de acciones.

Spec: ANCH-042, ANCH-043, ANCH-044, ANCH-045, ANCH-046, ANCH-047
"""

import json
import re
from pathlib import Path

from spec_anchor.cli import verify_quick
from spec_anchor.git import git_output
from spec_anchor.model import Finding
from spec_anchor.report import format_report

MAX_STOP_BLOCKS = 2
BLOCK = 2

_GIT = r"\bgit(?:\.exe)?"
_GIT_OPTIONS = r"(?:\s+(?:-[Cc]\s+\S+|--?[\w-]+(?:=\S+)?))*"
_END = r"(?=\s|$|[;&|])"
_CREATES_COMMIT = re.compile(
    _GIT + _GIT_OPTIONS + r"\s+(?:commit|merge|cherry-pick|revert|rebase|am)" + _END
)
_NO_VERIFY = re.compile(_GIT + r"\b.*--no-verify")
_COMMIT_WITHOUT_HOOKS = re.compile(
    _GIT + _GIT_OPTIONS + r"\s+commit\b[^;&|]*?\s-[a-zA-Z]*n[a-zA-Z]*" + _END
)
_PROTECTED = re.compile(r"\.git[\\/]+hooks|\.claude[\\/]+settings|core\.hookspath", re.IGNORECASE)
_SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
_FILE_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})

_REASONS = {
    "ANCH-044": "omitir los hooks de git (`--no-verify`) está prohibido (constitución XI.5)",
    "ANCH-045": "los agentes de IA no hacen commits: los hace la persona propietaria del "
    "producto (constitución XII.4)",
    "ANCH-046": "la configuración de Claude Code y los hooks de git sólo los cambia la "
    "persona propietaria del producto",
}


def stop(root: Path, payload: dict[str, object]) -> tuple[int, str, str]:
    """Impide terminar el turno si la verificación rápida falla (hook ``Stop``, ANCH-043).

    Tras ``MAX_STOP_BLOCKS`` bloqueos seguidos deja terminar y muestra el informe a la
    persona (ANCH-047). Devuelve el código de salida y las salidas estándar y de error.
    """
    findings = verify_quick(root)
    counter = _counter(root)
    if not findings:
        counter.unlink(missing_ok=True)
        return 0, "", ""
    report = format_report(findings)
    blocks = int(counter.read_text()) if counter.is_file() else 0
    if blocks >= MAX_STOP_BLOCKS:
        counter.unlink(missing_ok=True)
        message = (
            f"spec-anchor: tras {blocks} intentos, el agente no ha conseguido que la "
            f"verificación rápida pase.\n{report}"
        )
        return 0, json.dumps({"systemMessage": message}, ensure_ascii=False), ""
    counter.parent.mkdir(parents=True, exist_ok=True)
    counter.write_text(str(blocks + 1))
    return BLOCK, "", f"spec-anchor: corrige estos errores antes de terminar el turno.\n{report}"


def guard(payload: dict[str, object]) -> Finding | None:
    """Devuelve el motivo para bloquear una acción, si lo hay (hook ``PreToolUse``)."""
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    if tool in _SHELL_TOOLS:
        return _check_command(str(tool_input.get("command", "")))
    if tool in _FILE_TOOLS:
        path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        return _finding("ANCH-046") if _PROTECTED.search(path) else None
    return None


def _check_command(command: str) -> Finding | None:
    if _PROTECTED.search(command):
        return _finding("ANCH-046")
    if _NO_VERIFY.search(command) or _COMMIT_WITHOUT_HOOKS.search(command):
        return _finding("ANCH-044")
    if _CREATES_COMMIT.search(command):
        return _finding("ANCH-045")
    return None


def _finding(rule: str) -> Finding:
    return Finding(rule, _REASONS[rule])


def _counter(root: Path) -> Path:
    return root / git_output(root, "rev-parse", "--git-path", "spec-anchor/stop-blocks").strip()
