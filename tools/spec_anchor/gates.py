"""Puertas de calidad que se ejecutan con herramientas externas.

Spec: ANCH-018, ANCH-030, ANCH-031, ANCH-032, ANCH-033, ANCH-040
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Sequence
from pathlib import Path

from spec_anchor.model import Finding

TOTAL_COVERAGE_MIN = 85.0
CORE_COVERAGE_MIN = 95.0
CORE_FILES = "src/pxls/core/*"
COVERAGE_ARGS = ("--cov", "--cov-report=", "--cov-fail-under=0")

_NO_TESTS_COLLECTED = 5
_SUMMARY_LINE = re.compile(r"^(FAILED|ERROR) (\S+)")
_LINT_LINE = re.compile(r"^(.+?):(\d+):\d+: (.+)$")
_TYPE_LINE = re.compile(r"^(.+?):(\d+): error: (.+)$")
_BROKEN_CONTRACT = re.compile(r"^(.+) BROKEN$")


def run_format(root: Path) -> list[Finding]:
    """Comprueba el formato con ``ruff format`` (ANCH-030)."""
    result = _run(root, _module("ruff", "format", "--check", "--output-format", "concise", "."))
    if result.returncode == 0:
        return []
    findings = [
        Finding("ANCH-030", "el fichero no tiene el formato de ruff", _relative(match.group(1)))
        for line in result.stdout.splitlines()
        if (match := _LINT_LINE.match(line))
    ]
    return findings or [_failure("ANCH-030", "ruff format", result)]


def run_lint(root: Path) -> list[Finding]:
    """Comprueba el lint con ``ruff check`` (ANCH-030)."""
    result = _run(root, _module("ruff", "check", "--output-format", "concise", "--no-fix", "."))
    if result.returncode == 0:
        return []
    findings = [
        Finding("ANCH-030", match.group(3), _relative(match.group(1)), int(match.group(2)))
        for line in result.stdout.splitlines()
        if (match := _LINT_LINE.match(line))
    ]
    return findings or [_failure("ANCH-030", "ruff check", result)]


def run_types(root: Path) -> list[Finding]:
    """Comprueba los tipos con ``mypy`` (ANCH-031)."""
    result = _run(root, _module("mypy", "--no-error-summary", "--no-color-output"))
    if result.returncode == 0:
        return []
    findings = [
        Finding(
            "ANCH-031", f"mypy: {match.group(3)}", _relative(match.group(1)), int(match.group(2))
        )
        for line in result.stdout.splitlines()
        if (match := _TYPE_LINE.match(line))
    ]
    return findings or [_failure("ANCH-031", "mypy", result)]


def run_architecture(root: Path) -> list[Finding]:
    """Comprueba los contratos de arquitectura con ``import-linter`` (ANCH-031)."""
    result = _run(root, [_script("lint-imports")])
    if result.returncode == 0:
        return []
    findings = [
        Finding("ANCH-031", f"se incumple el contrato de arquitectura «{match.group(1).strip()}»")
        for line in result.stdout.splitlines()
        if (match := _BROKEN_CONTRACT.match(line))
    ]
    return findings or [_failure("ANCH-031", "lint-imports", result)]


def run_tests(root: Path, extra_args: Sequence[str] = ()) -> list[Finding]:
    """Ejecuta la suite de tests de ``root`` e informa de cada test que falla (INV-7)."""
    command = _module("pytest", "-q", "-rfE", "--color=no", "-p", "no:cacheprovider", *extra_args)
    result = _run(root, command)
    if result.returncode in (0, _NO_TESTS_COLLECTED):
        return []
    findings: list[Finding] = []
    for line in result.stdout.splitlines():
        match = _SUMMARY_LINE.match(line)
        if match is not None:
            kind, node = match.groups()
            verb = "falla" if kind == "FAILED" else "no se puede ejecutar"
            findings.append(Finding("INV-7", f"el test {node} {verb}", node.split("::")[0]))
    return findings or [_failure("INV-7", "pytest", result)]


def measure_coverage(root: Path) -> tuple[float | None, float | None]:
    """Devuelve la cobertura total y la de ``core`` de la última ejecución de los tests."""
    return _coverage_percent(root), _coverage_percent(root, f"--include={CORE_FILES}")


def check_coverage(total: float | None, core: float | None) -> list[Finding]:
    """Comprueba los umbrales de cobertura del Artículo X (ANCH-032)."""
    findings: list[Finding] = []
    if total is not None and total < TOTAL_COVERAGE_MIN:
        text = (
            f"la cobertura total es {_percent(total)} y el mínimo es {_percent(TOTAL_COVERAGE_MIN)}"
        )
        findings.append(Finding("ANCH-032", text))
    if core is not None and core < CORE_COVERAGE_MIN:
        text = (
            f"la cobertura de core es {_percent(core)} y el mínimo es {_percent(CORE_COVERAGE_MIN)}"
        )
        findings.append(Finding("ANCH-032", text))
    return findings


def run_packaging(root: Path) -> list[Finding]:
    """Genera el ejecutable y ejecuta su prueba de humo si están configurados (ANCH-033)."""
    config = _anchor_config(root)
    package, smoke = _command(config, "package"), _command(config, "smoke")
    if package:
        result = _run(root, package)
        if result.returncode != 0:
            return [Finding("ANCH-033", f"falló el empaquetado (código {result.returncode})")]
    if smoke:
        result = _run(root, smoke)
        if result.returncode != 0:
            text = f"el ejecutable no supera la prueba de humo (código {result.returncode})"
            return [Finding("ANCH-033", text)]
    return []


def _run(root: Path, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_environment(root),
        check=False,
    )


def _environment(root: Path) -> dict[str, str]:
    # Un hook de git exporta GIT_DIR, GIT_INDEX_FILE…; los tests que crean repositorios
    # temporales los heredarían y escribirían en el repositorio real.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    paths = [str(root / folder) for folder in ("src", "tools") if (root / folder).is_dir()]
    if environment.get("PYTHONPATH"):
        paths.append(environment["PYTHONPATH"])
    return {**environment, "PYTHONUTF8": "1", "PYTHONPATH": os.pathsep.join(paths)}


def _module(name: str, *args: str) -> list[str]:
    return [sys.executable, "-m", name, *args]


def _script(name: str) -> str:
    candidate = Path(sys.executable).with_name(f"{name}.exe" if os.name == "nt" else name)
    return str(candidate) if candidate.exists() else name


def _relative(path: str) -> str:
    return Path(path.strip()).as_posix()


def _failure(rule: str, tool: str, result: subprocess.CompletedProcess[str]) -> Finding:
    tail = " / ".join((result.stdout + result.stderr).strip().splitlines()[-3:])
    return Finding(rule, f"{tool} terminó con código {result.returncode}: {tail}")


def _coverage_percent(root: Path, *args: str) -> float | None:
    with tempfile.TemporaryDirectory() as folder:
        report = Path(folder) / "coverage.json"
        _run(root, _module("coverage", "json", "-q", "-o", str(report), *args))
        if not report.exists():
            return None
        totals = json.loads(report.read_text(encoding="utf-8"))["totals"]
    if totals["num_statements"] + totals.get("num_branches", 0) == 0:
        return None
    return float(totals["percent_covered"])


def _percent(value: float) -> str:
    text = f"{value:.1f}".removesuffix(".0")
    return f"{text.replace('.', ',')} %"


def _anchor_config(root: Path) -> dict[str, object]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return {}
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    section = data.get("tool", {}).get("spec-anchor", {})
    return section if isinstance(section, dict) else {}


def _command(config: dict[str, object], key: str) -> list[str] | None:
    value = config.get(key)
    return [str(part) for part in value] if isinstance(value, list) and value else None
