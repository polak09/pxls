"""Trailers y reglas de clase de cambio de un commit (Artículo II y Anexo B).

Spec: ANCH-019, ANCH-020, ANCH-021, ANCH-022, ANCH-023, ANCH-024, ANCH-025, ANCH-026,
    ANCH-027
"""

import re
from collections import Counter
from collections.abc import Callable, Collection
from dataclasses import dataclass
from functools import cached_property

from spec_anchor.invariants import ID
from spec_anchor.model import CaseRef, Finding, Requirement
from spec_anchor.pyrefs import MODULE_FILE, TEST_FILE, read_module, read_tests
from spec_anchor.specs import SPEC_PATH, find_specs, parse_spec
from spec_anchor.tree import Tree

CHANGE_TYPES = ("behavior", "refactor", "editorial", "chore", "constitution")
CONSTITUTION = "CONSTITUTION.md"
IMPROVEMENTS = "mejoras.md"

_TRAILER = re.compile(r"^(Change-Type|Spec-Refs):\s*(.*?)\s*$")
_VERSION = re.compile(r"^\|\s*\*\*Versión\*\*\s*\|\s*(\d+)\.(\d+)\.(\d+)\s*\|", re.MULTILINE)
_NEEDS_REFS = frozenset({"behavior", "editorial"})
_FORBIDS_REFS = frozenset({"refactor", "chore"})


@dataclass(frozen=True)
class Declaration:
    """Clase de cambio e IDs declarados en los trailers de un commit."""

    change_type: str
    refs: tuple[str, ...]


def check_message(message: str) -> tuple[Declaration | None, list[Finding]]:
    """Lee los trailers ``Change-Type`` y ``Spec-Refs`` y comprueba su forma."""
    values: dict[str, list[str]] = {"Change-Type": [], "Spec-Refs": []}
    for line in message.splitlines():
        match = None if line.startswith("#") else _TRAILER.match(line)
        if match is not None:
            values[match.group(1)].append(match.group(2))
    types, refs = values["Change-Type"], values["Spec-Refs"]
    if not types:
        return None, [Finding("ANCH-019", "falta el trailer `Change-Type`")]
    if len(types) > 1:
        return None, [Finding("ANCH-019", "hay más de un trailer `Change-Type`")]
    change_type = types[0]
    if change_type not in CHANGE_TYPES:
        message_text = f"`Change-Type: {change_type}` no es ninguna de {', '.join(CHANGE_TYPES)}"
        return None, [Finding("ANCH-019", message_text)]
    findings: list[Finding] = []
    ids: list[str] = []
    for value in refs:
        parts = [part.strip() for part in value.split(",")]
        if all(ID.match(part) for part in parts):
            ids += parts
        else:
            text = f"`Spec-Refs: {value}` no es una lista de IDs separados por comas"
            findings.append(Finding("ANCH-020", text))
    if change_type in _NEEDS_REFS and not refs:
        findings.append(Finding("ANCH-020", f"un commit `{change_type}` necesita `Spec-Refs`"))
    if change_type in _FORBIDS_REFS and refs:
        text = f"un commit `{change_type}` no puede llevar `Spec-Refs`"
        findings.append(Finding("ANCH-020", text))
    return Declaration(change_type, tuple(dict.fromkeys(ids))), findings


def changed_paths(before: Tree, after: Tree) -> set[str]:
    """Devuelve las rutas añadidas, eliminadas o modificadas entre dos árboles."""
    old, new = set(before.files()), set(after.files())
    return (old ^ new) | {path for path in old & new if before.read(path) != after.read(path)}


def check_change(
    declaration: Declaration, before: Tree, after: Tree, paths: Collection[str]
) -> list[Finding]:
    """Comprueba que el commit respeta las reglas de su clase de cambio (Artículo II)."""
    change = _Change(before, after, frozenset(paths))
    return _RULES[declaration.change_type](change, declaration.refs)


class _Change:
    def __init__(self, before: Tree, after: Tree, paths: frozenset[str]) -> None:
        self.before = before
        self.after = after
        self.paths = sorted(paths)
        self._before_files = set(before.files())
        self._after_files = set(after.files())

    def old(self, path: str) -> str | None:
        return self.before.read(path) if path in self._before_files else None

    def new(self, path: str) -> str | None:
        return self.after.read(path) if path in self._after_files else None

    def of_kind(self, pattern: re.Pattern[str]) -> list[str]:
        return [path for path in self.paths if pattern.match(path)]

    @cached_property
    def old_requirements(self) -> dict[str, Requirement]:
        return _requirements(self.before)

    @cached_property
    def new_requirements(self) -> dict[str, Requirement]:
        return _requirements(self.after)

    def cases(self, path: str) -> tuple[dict[str, CaseRef], dict[str, CaseRef]]:
        old, new = self.old(path), self.new(path)
        before = {c.name: c for c in read_tests(path, old)} if old is not None else {}
        after = {c.name: c for c in read_tests(path, new)} if new is not None else {}
        return before, after


def _requirements(tree: Tree) -> dict[str, Requirement]:
    return {
        req.id: req
        for path in find_specs(tree)
        for req in parse_spec(path, tree.read(path))[0].requirements
    }


def _behavior(change: _Change, refs: tuple[str, ...]) -> list[Finding]:
    findings: list[Finding] = []
    touched = _touched_test_ids(change)
    for ref in refs:
        old, new = change.old_requirements.get(ref), change.new_requirements.get(ref)
        if (old.normative if old else None) == (new.normative if new else None):
            text = f"el commit declara {ref} pero no cambia su texto normativo"
            findings.append(Finding("ANCH-021", text))
        if ref not in touched:
            text = (
                f"el commit declara {ref} pero no añade, modifica ni elimina "
                "ningún test marcado con él"
            )
            findings.append(Finding("ANCH-021", text))
    for path in change.of_kind(MODULE_FILE):
        source = change.new(path) or change.old(path) or ""
        module = read_module(path, source)
        ids = module.ids
        if module.has_definitions and not set(ids) & set(refs):
            implemented = ", ".join(ids) or "ningún requisito"
            text = f"el módulo implementa {implemented}, que no está en `Spec-Refs`"
            findings.append(Finding("ANCH-022", text, path))
    return findings


def _touched_test_ids(change: _Change) -> set[str]:
    touched: set[str] = set()
    for path in change.of_kind(TEST_FILE):
        before, after = change.cases(path)
        for name in before.keys() | after.keys():
            old, new = before.get(name), after.get(name)
            if old is None or new is None or old.source != new.source:
                touched.update((old.ids if old else ()) + (new.ids if new else ()))
    return touched


def _refactor(change: _Change, refs: tuple[str, ...]) -> list[Finding]:
    findings = [
        Finding("ANCH-023", "un `refactor` no puede modificar specs", path)
        for path in change.of_kind(SPEC_PATH)
    ]
    counts_before: Counter[str] = Counter()
    counts_after: Counter[str] = Counter()
    for path in change.of_kind(TEST_FILE):
        before, after = change.cases(path)
        counts_before.update(ref for case in before.values() for ref in case.ids)
        counts_after.update(ref for case in after.values() for ref in case.ids)
    for ref, count in sorted(counts_before.items()):
        if counts_after[ref] < count:
            text = f"tras el refactor, {ref} tiene {counts_after[ref]} tests y antes tenía {count}"
            findings.append(Finding("ANCH-023", text))
    return findings


def _editorial(change: _Change, refs: tuple[str, ...]) -> list[Finding]:
    findings = [
        Finding("ANCH-024", "un `editorial` sólo puede modificar documentación Markdown", path)
        for path in change.paths
        if not path.endswith(".md") or path in (CONSTITUTION, IMPROVEMENTS)
    ]
    for path in change.of_kind(SPEC_PATH):
        old = _statuses(path, change.old(path))
        new = _statuses(path, change.new(path))
        for req_id in sorted(new.keys() - old.keys()):
            findings.append(Finding("ANCH-024", f"un `editorial` no puede añadir {req_id}", path))
        for req_id in sorted(old.keys() - new.keys()):
            findings.append(Finding("ANCH-024", f"un `editorial` no puede eliminar {req_id}", path))
        for req_id in sorted(old.keys() & new.keys()):
            if old[req_id] != new[req_id]:
                text = f"un `editorial` no puede cambiar el estado de {req_id}"
                findings.append(Finding("ANCH-024", text, path))
    return findings


def _statuses(path: str, text: str | None) -> dict[str, str | None]:
    if text is None:
        return {}
    return {req.id: req.status for req in parse_spec(path, text)[0].requirements}


def _chore(change: _Change, refs: tuple[str, ...]) -> list[Finding]:
    anchored = [
        *change.of_kind(SPEC_PATH),
        *change.of_kind(TEST_FILE),
        *change.of_kind(MODULE_FILE),
    ]
    return [
        Finding("ANCH-025", "un `chore` no puede modificar specs, tests ni código anclado", path)
        for path in sorted(anchored)
    ]


def _constitution(change: _Change, refs: tuple[str, ...]) -> list[Finding]:
    if CONSTITUTION not in change.paths:
        return [Finding("ANCH-026", f"un commit `constitution` debe modificar `{CONSTITUTION}`")]
    old = _version(change.old(CONSTITUTION))
    new = _version(change.new(CONSTITUTION))
    if new is None or (old is not None and new <= old):
        text = "la enmienda no incrementa la versión de la constitución"
        return [Finding("ANCH-026", text, CONSTITUTION)]
    version = ".".join(map(str, new))
    history_row = re.compile(rf"^\|\s*{re.escape(version)}\s*\|", re.MULTILINE)
    if not history_row.search(change.new(CONSTITUTION) or ""):
        text = f"el historial de enmiendas no tiene una fila para la versión {version}"
        return [Finding("ANCH-026", text, CONSTITUTION)]
    return []


def _version(text: str | None) -> tuple[int, int, int] | None:
    match = _VERSION.search(text or "")
    if match is None:
        return None
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


_RULES: dict[str, Callable[[_Change, tuple[str, ...]], list[Finding]]] = {
    "behavior": _behavior,
    "refactor": _refactor,
    "editorial": _editorial,
    "chore": _chore,
    "constitution": _constitution,
}
