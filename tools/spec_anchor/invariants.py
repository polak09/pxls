"""Invariantes del Artículo III sobre specs, tests y módulos anclados.

Spec: ANCH-004, ANCH-006, ANCH-007, ANCH-009, ANCH-012, ANCH-014, ANCH-015, ANCH-016,
    ANCH-017
"""

import re
from collections import defaultdict
from collections.abc import Sequence

from spec_anchor.model import CaseRef, Finding, ModuleRef, Spec, Status

ID = re.compile(r"^[A-Z]{3,5}-\d{3}$")
_SETTLED = frozenset({Status.APPROVED, Status.IMPLEMENTED})
_PENDING = frozenset({Status.DRAFT, Status.APPROVED})
_IMPROVEMENT = re.compile(r"^MEJ-\d+$")
_TASK = re.compile(r"^T-\d+$")


def check_tests(tests: Sequence[CaseRef]) -> list[Finding]:
    """Comprueba que todo test tiene al menos un marcador ``spec`` (INV-2)."""
    return [
        Finding("INV-2", f"el test {test.name} no tiene marcador `spec`", test.path, test.line)
        for test in tests
        if not test.ids
    ]


def check_modules(modules: Sequence[ModuleRef]) -> list[Finding]:
    """Comprueba que todo módulo con definiciones declara ``Spec:`` (INV-3)."""
    message = "el módulo define funciones o clases y su docstring no tiene `Spec:` con IDs"
    return [
        Finding("INV-3", message, module.path, module.line or 1)
        for module in modules
        if module.has_definitions and not module.ids
    ]


def check_references(
    specs: Sequence[Spec], tests: Sequence[CaseRef], modules: Sequence[ModuleRef]
) -> list[Finding]:
    """Comprueba que toda referencia apunta a un requisito vivo (INV-4)."""
    statuses = {req.id: req.status for spec in specs for req in spec.requirements}
    places = [(t.path, t.line, ref) for t in tests for ref in t.ids]
    places += [(m.path, m.line or 1, ref) for m in modules for ref in m.ids]
    findings: list[Finding] = []
    for path, line, ref in places:
        if _IMPROVEMENT.match(ref):
            message = f"`{ref}` es una mejora de `mejoras.md`, no un requisito"
        elif _TASK.match(ref):
            message = f"`{ref}` es una tarea de `tareas.md`, no un requisito"
        elif ref not in statuses:
            message = f"`{ref}` no es ningún requisito"
        elif statuses[ref] is Status.RETIRED:
            message = f"`{ref}` está retirado"
        else:
            continue
        findings.append(Finding("INV-4", message, path, line))
    return findings


def check_anchored(
    specs: Sequence[Spec], tests: Sequence[CaseRef], modules: Sequence[ModuleRef]
) -> list[Finding]:
    """Comprueba que todo requisito implementado tiene tests y código (INV-5)."""
    tested = {ref for test in tests for ref in test.ids}
    coded = {ref for module in modules for ref in module.ids}
    findings: list[Finding] = []
    for spec in specs:
        for req in spec.requirements:
            if req.status is not Status.IMPLEMENTED:
                continue
            if req.id not in tested:
                message = f"el requisito {req.id} está `implemented` y sin tests que lo referencien"
                findings.append(Finding("INV-5", message, spec.path, req.line))
            if req.id not in coded:
                message = f"el requisito {req.id} está `implemented` y sin código que lo referencie"
                findings.append(Finding("INV-5", message, spec.path, req.line))
    return findings


def check_pending(specs: Sequence[Spec]) -> list[Finding]:
    """Comprueba que no quedan requisitos ``draft`` ni ``approved`` (INV-6)."""
    return [
        Finding(
            "INV-6",
            f"el requisito {req.id} está `{req.status}`: un commit sólo admite "
            "requisitos `implemented` o `retired`",
            spec.path,
            req.line,
        )
        for spec in specs
        for req in spec.requirements
        if req.status in _PENDING
    ]


def check_specs(specs: Sequence[Spec]) -> list[Finding]:
    """Comprueba la unicidad de prefijos e IDs, su formato y las dudas abiertas (INV-1)."""
    return [
        *_duplicated_prefixes(specs),
        *_malformed_ids(specs),
        *_duplicated_ids(specs),
        *_open_doubts(specs),
    ]


def _duplicated_prefixes(specs: Sequence[Spec]) -> list[Finding]:
    paths: dict[str, list[str]] = defaultdict(list)
    for spec in specs:
        if spec.prefix is not None:
            paths[spec.prefix].append(spec.path)
    return [
        Finding(
            "ANCH-004", f"el prefijo `{prefix}` lo usan varias specs: {', '.join(used)}", used[0]
        )
        for prefix, used in paths.items()
        if len(used) > 1
    ]


def _malformed_ids(specs: Sequence[Spec]) -> list[Finding]:
    findings: list[Finding] = []
    for spec in specs:
        for req in spec.requirements:
            if not ID.match(req.id):
                message = f"el ID `{req.id}` no tiene el formato <PREFIJO>-<NNN>"
            elif spec.prefix is not None and not req.id.startswith(f"{spec.prefix}-"):
                message = f"el ID `{req.id}` no usa el prefijo `{spec.prefix}` de su spec"
            else:
                continue
            findings.append(Finding("INV-1", message, spec.path, req.line))
    return findings


def _duplicated_ids(specs: Sequence[Spec]) -> list[Finding]:
    places: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for spec in specs:
        for req in spec.requirements:
            places[req.id].append((spec.path, req.line))
    findings: list[Finding] = []
    for req_id, found in places.items():
        if len(found) > 1:
            where = ", ".join(f"{path}:{line}" for path, line in found)
            path, line = found[0]
            findings.append(
                Finding("INV-1", f"el ID `{req_id}` está repetido: {where}", path, line)
            )
    return findings


def _open_doubts(specs: Sequence[Spec]) -> list[Finding]:
    return [
        Finding(
            "INV-1",
            f"el requisito {req.id} está `{req.status}` y tiene dudas abiertas",
            spec.path,
            req.line,
        )
        for spec in specs
        for req in spec.requirements
        if req.status in _SETTLED and req.has_doubt
    ]
