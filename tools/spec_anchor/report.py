"""Informe de errores y código de salida de las verificaciones.

Spec: ANCH-035, ANCH-036
"""

from collections.abc import Sequence

from spec_anchor.model import Finding


def format_report(findings: Sequence[Finding]) -> str:
    """Devuelve una línea por error y un resumen con el número de errores (ANCH-035)."""
    lines = [_line(finding) for finding in findings]
    count = len(findings)
    lines.append("1 error" if count == 1 else f"{count} errores")
    return "\n".join(lines) + "\n"


def exit_code(findings: Sequence[Finding]) -> int:
    """Devuelve 0 si no hay errores y 1 si los hay (ANCH-036)."""
    return 1 if findings else 0


def _line(finding: Finding) -> str:
    location = finding.path
    if location is not None and finding.line is not None:
        location = f"{location}:{finding.line}"
    if location is None:
        return f"ERROR [{finding.rule}] {finding.message}"
    return f"ERROR [{finding.rule}] {location} · {finding.message}"
