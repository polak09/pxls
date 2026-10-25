"""Lectura de las referencias a requisitos en tests y módulos anclados.

Spec: ANCH-011, ANCH-013, ANCH-021, ANCH-023
"""

import ast
import re

from spec_anchor.model import CaseRef, ModuleRef
from spec_anchor.tree import Tree

TEST_FILE = re.compile(r"^tests/(?:.+/)?test_[^/]*\.py$")
MODULE_FILE = re.compile(r"^(?:src|tools)/.+\.py$")

_SPEC_LINE = re.compile(r"^\s*Spec:(.*)$")
_FUNCTION = (ast.FunctionDef, ast.AsyncFunctionDef)
_DEFINITION = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def find_tests(tree: Tree) -> list[str]:
    """Devuelve, ordenadas, las rutas de los ficheros de test del árbol."""
    return sorted(path for path in tree.files() if TEST_FILE.match(path))


def find_modules(tree: Tree) -> list[str]:
    """Devuelve, ordenadas, las rutas de los módulos anclados del árbol."""
    return sorted(path for path in tree.files() if MODULE_FILE.match(path))


def read_tests(path: str, source: str) -> list[CaseRef]:
    """Devuelve las funciones de test de un fichero con los IDs de sus marcadores."""
    lines = source.splitlines()
    found: list[CaseRef] = []
    for node in ast.parse(source, filename=path).body:
        if isinstance(node, _FUNCTION) and node.name.startswith("test"):
            ids = _marker_ids(node)
            found.append(CaseRef(path, node.lineno, node.name, ids, _segment(lines, node)))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            inherited = _marker_ids(node)
            for item in node.body:
                if isinstance(item, _FUNCTION) and item.name.startswith("test"):
                    ids = tuple(dict.fromkeys(inherited + _marker_ids(item)))
                    name = f"{node.name}::{item.name}"
                    found.append(CaseRef(path, item.lineno, name, ids, _segment(lines, item)))
    return found


def _segment(lines: list[str], node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Devuelve el código del test, decoradores incluidos."""
    start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    return "\n".join(lines[start - 1 : node.end_lineno])


def read_module(path: str, source: str) -> ModuleRef:
    """Devuelve los IDs de la línea ``Spec:`` del docstring de un módulo y su continuación."""
    module = ast.parse(source, filename=path)
    has_definitions = any(isinstance(node, _DEFINITION) for node in module.body)
    first = module.body[0] if module.body else None
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        lines = first.value.value.splitlines()
        for offset, text in enumerate(lines):
            match = _SPEC_LINE.match(text)
            if match is not None:
                listed = [match.group(1)]
                for following in lines[offset + 1 :]:
                    if not following.strip() or not following[0].isspace():
                        break
                    listed.append(following)
                parts = (part.strip() for chunk in listed for part in chunk.split(","))
                ids = tuple(part for part in parts if part)
                return ModuleRef(path, first.lineno + offset, ids, has_definitions)
    return ModuleRef(path, None, (), has_definitions)


def _marker_ids(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> tuple[str, ...]:
    ids: list[str] = []
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and _is_spec_mark(decorator.func):
            ids += [
                arg.value
                for arg in decorator.args
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
            ]
    return tuple(dict.fromkeys(ids))


def _is_spec_mark(func: ast.expr) -> bool:
    if not isinstance(func, ast.Attribute) or func.attr != "spec":
        return False
    owner = func.value
    return (isinstance(owner, ast.Attribute) and owner.attr == "mark") or (
        isinstance(owner, ast.Name) and owner.id == "mark"
    )
