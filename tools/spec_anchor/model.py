"""Tipos del modelo: specs, requisitos, referencias y errores detectados.

Spec: ANCH-002, ANCH-005, ANCH-008, ANCH-009, ANCH-010, ANCH-011, ANCH-013, ANCH-021
"""

from dataclasses import dataclass
from enum import StrEnum


class Status(StrEnum):
    """Estado de un requisito en su ciclo de vida (constitución IV)."""

    DRAFT = "draft"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    RETIRED = "retired"


@dataclass(frozen=True)
class Finding:
    """Incumplimiento de una regla, con su ubicación si la tiene."""

    rule: str
    message: str
    path: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class Requirement:
    """Requisito leído de una spec."""

    id: str
    title: str
    line: int
    status: Status | None
    has_doubt: bool
    has_reason: bool
    normative: str = ""


@dataclass(frozen=True)
class Spec:
    """Spec leída de ``specs/<capacidad>/spec.md``."""

    path: str
    capability: str | None
    prefix: str | None
    owner: str | None
    requirements: tuple[Requirement, ...]


@dataclass(frozen=True)
class CaseRef:
    """Función de test y los IDs de sus marcadores ``spec``."""

    path: str
    line: int
    name: str
    ids: tuple[str, ...]
    source: str = ""


@dataclass(frozen=True)
class ModuleRef:
    """Módulo anclado y los IDs de la línea ``Spec:`` de su docstring."""

    path: str
    line: int | None
    ids: tuple[str, ...]
    has_definitions: bool
