"""Punto de entrada ``spec-anchor``, niveles de verificación y hooks de git.

Spec: ANCH-028, ANCH-029, ANCH-030, ANCH-031, ANCH-035, ANCH-036, ANCH-037, ANCH-038,
    ANCH-040, ANCH-041, ANCH-043, ANCH-045
"""

import argparse
import io
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from spec_anchor.changes import check_change, check_message
from spec_anchor.gates import (
    COVERAGE_ARGS,
    check_coverage,
    measure_coverage,
    run_architecture,
    run_format,
    run_lint,
    run_packaging,
    run_tests,
    run_types,
)
from spec_anchor.git import (
    current_branch,
    merge_sources,
    repo_root,
    revision,
    staged_paths,
    uncommitted_changes,
)
from spec_anchor.hooks import HOOK_NAMES, check_hooks_installed, install
from spec_anchor.invariants import (
    check_anchored,
    check_modules,
    check_pending,
    check_references,
    check_specs,
    check_tests,
)
from spec_anchor.model import CaseRef, Finding, ModuleRef, Spec
from spec_anchor.pyrefs import find_modules, find_tests, read_module, read_tests
from spec_anchor.report import exit_code, format_report
from spec_anchor.specs import load_specs
from spec_anchor.tree import DiskTree, GitTree, Tree

INTEGRATED_BRANCHES = ("dev", "main")
RELEASE_SOURCE = "dev"


@dataclass
class Analysis:
    """Specs, tests y módulos leídos de un árbol, con los errores de lectura."""

    specs: list[Spec] = field(default_factory=list)
    tests: list[CaseRef] = field(default_factory=list)
    modules: list[ModuleRef] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def analyse(tree: Tree) -> Analysis:
    """Lee las specs, los tests y los módulos anclados de ``tree``."""
    analysis = Analysis()
    analysis.specs, analysis.findings = load_specs(tree)
    for path in find_tests(tree):
        try:
            analysis.tests += read_tests(path, tree.read(path))
        except SyntaxError as error:
            analysis.findings.append(_unparseable(path, error))
    for path in find_modules(tree):
        try:
            analysis.modules.append(read_module(path, tree.read(path)))
        except SyntaxError as error:
            analysis.findings.append(_unparseable(path, error))
    return analysis


def verify_quick(root: Path) -> list[Finding]:
    """Verificación rápida sobre la copia de trabajo (ANCH-030)."""
    return _quick(root, analyse(DiskTree(root)))


def verify_full(root: Path) -> list[Finding]:
    """Verificación completa sobre la copia de trabajo, sin reglas de commit (ANCH-031)."""
    analysis = analyse(DiskTree(root))
    findings = _quick(root, analysis)
    findings += run_types(root)
    findings += run_architecture(root)
    findings += run_tests(root, COVERAGE_ARGS)
    findings += check_coverage(*measure_coverage(root))
    findings += check_anchored(analysis.specs, analysis.tests, analysis.modules)
    findings += check_pending(analysis.specs)
    findings += run_packaging(root)
    return findings


def run_hook(name: str, root: Path, args: Sequence[str]) -> list[Finding]:
    """Ejecuta las comprobaciones del hook de git ``name`` (ANCH-028, ANCH-029, ANCH-040)."""
    branch = current_branch(root)
    if name == "commit-msg":
        return _commit_message_rules(root, branch, Path(args[0]))
    if branch not in INTEGRATED_BRANCHES:
        where = f"`{branch}`" if branch else "un HEAD separado"
        text = f"sólo se hacen commits en `dev` y `main` (constitución II.6), no en {where}"
        return [Finding("ANCH-028", text)]
    if branch == "main" and merge_sources(root) != [revision(root, RELEASE_SOURCE)]:
        return [Finding("ANCH-029", "en `main` sólo se integran versiones con un merge de `dev`")]
    return [*uncommitted_changes(root), *verify_full(root)]


def main(argv: Sequence[str] | None = None) -> int:
    """Ejecuta ``spec-anchor`` y devuelve su código de salida."""
    parser = argparse.ArgumentParser(
        prog="spec-anchor", description="Verifica el anclaje entre specs, tests y código."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="ejecuta una verificación")
    level = check.add_mutually_exclusive_group(required=True)
    level.add_argument("--quick", action="store_true", help="verificación rápida")
    level.add_argument("--full", action="store_true", help="verificación completa")
    commands.add_parser("install", help="instala los hooks de git")
    hook = commands.add_parser("hook", help="lo ejecutan los hooks de git")
    hook.add_argument("name", choices=HOOK_NAMES)
    hook.add_argument("args", nargs="*")
    claude = commands.add_parser("claude", help="lo ejecutan los hooks de Claude Code")
    claude.add_argument("action", choices=("stop", "guard"))
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if args.command == "claude":
        return _claude(args.action)
    root = repo_root(Path.cwd())
    if args.command == "check":
        findings = verify_quick(root) if args.quick else verify_full(root)
    elif args.command == "install":
        findings = install(root)
    else:
        findings = run_hook(args.name, root, args.args)
    print(format_report(findings), end="")
    return exit_code(findings)


def _quick(root: Path, analysis: Analysis) -> list[Finding]:
    return [
        *check_hooks_installed(root),
        *run_format(root),
        *run_lint(root),
        *analysis.findings,
        *check_specs(analysis.specs),
        *check_tests(analysis.tests),
        *check_modules(analysis.modules),
        *check_references(analysis.specs, analysis.tests, analysis.modules),
    ]


def _claude(action: str) -> int:
    # Importación tardía: spec_anchor.claude usa verify_quick de este módulo.
    from spec_anchor.claude import BLOCK, guard, stop

    payload = json.loads(sys.stdin.read() or "{}")
    if action == "stop":
        code, out, err = stop(repo_root(Path.cwd()), payload)
    else:
        finding = guard(payload)
        code, out = (BLOCK, "") if finding is not None else (0, "")
        err = (
            f"spec-anchor bloquea esta acción [{finding.rule}]: {finding.message}\n"
            if finding
            else ""
        )
    print(out, end="")
    print(err, end="", file=sys.stderr)
    return code


def _commit_message_rules(root: Path, branch: str, message_file: Path) -> list[Finding]:
    if branch != RELEASE_SOURCE:
        return []
    declaration, findings = check_message(message_file.read_text(encoding="utf-8"))
    if declaration is None:
        return findings
    before, after = GitTree(root, "HEAD"), GitTree(root, None)
    return findings + check_change(declaration, before, after, staged_paths(root))


def _unparseable(path: str, error: SyntaxError) -> Finding:
    return Finding("ANCH-030", f"no se puede analizar el fichero: {error.msg}", path, error.lineno)
