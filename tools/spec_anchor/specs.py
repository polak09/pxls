"""Descubrimiento y lectura de specs.

Spec: ANCH-001, ANCH-002, ANCH-003, ANCH-004, ANCH-005, ANCH-008, ANCH-010, ANCH-021
"""

import re
from dataclasses import dataclass, field

from spec_anchor.model import Finding, Requirement, Spec, Status
from spec_anchor.tree import Tree

SPEC_PATH = re.compile(r"^specs/([^/]+)/spec\.md$")
HEADER_FIELDS = ("capability", "prefix", "owner")
PREFIX = re.compile(r"^[A-Z]{3,5}$")
RESERVED_PREFIXES = frozenset({"MEJ"})
REQUIREMENTS_SECTION = "Requisitos"

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_REQUIREMENT_TITLE = re.compile(r"^([A-Z]+-\d+) · (.+)$")
_STATUS_LINE = re.compile(r"^\s*-\s*\*\*Estado:\*\*\s*(.*?)\s*$")
_REASON_LINE = re.compile(r"^\s*-\s*\*\*Motivo:\*\*\s*\S")
_DOUBT = "[NEEDS CLARIFICATION"
_FIELD_LINE = re.compile(r"^- \*\*(.+?):\*\*")
_NORMATIVE_FIELDS = ("Enunciado", "Criterios de aceptación")


@dataclass
class _Block:
    id: str
    title: str
    line: int
    level: int
    body: list[str] = field(default_factory=list)


def find_specs(tree: Tree) -> list[str]:
    """Devuelve, ordenadas, las rutas de las specs del árbol."""
    return sorted(path for path in tree.files() if SPEC_PATH.match(path))


def load_specs(tree: Tree) -> tuple[list[Spec], list[Finding]]:
    """Lee todas las specs del árbol y los errores de formato que contienen."""
    specs: list[Spec] = []
    findings: list[Finding] = []
    for path in find_specs(tree):
        spec, found = parse_spec(path, tree.read(path))
        specs.append(spec)
        findings.extend(found)
    return specs, findings


def parse_spec(path: str, text: str) -> tuple[Spec, list[Finding]]:
    """Lee una spec y devuelve su modelo junto con sus errores de formato."""
    lines = text.splitlines()
    header, body_start, findings = _parse_header(path, lines)
    capability = header.get("capability")
    prefix = header.get("prefix")
    findings += _check_capability(path, capability)
    findings += _check_prefix(path, prefix)
    requirements: list[Requirement] = []
    for block in _requirement_blocks(lines, body_start):
        requirement, found = _to_requirement(path, block)
        requirements.append(requirement)
        findings += found
    spec = Spec(path, capability, prefix, header.get("owner"), tuple(requirements))
    return spec, findings


def _parse_header(path: str, lines: list[str]) -> tuple[dict[str, str], int, list[Finding]]:
    if not lines or lines[0].strip() != "---":
        return {}, 0, [Finding("ANCH-002", "la spec no empieza con una cabecera `---`", path, 1)]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, 0, [Finding("ANCH-002", "la cabecera no tiene línea `---` de cierre", path, 1)]
    header: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if sep:
            header[key.strip()] = value.strip()
    findings = [
        Finding("ANCH-002", f"falta el campo `{name}` en la cabecera", path, 1)
        for name in HEADER_FIELDS
        if not header.get(name)
    ]
    return header, end + 1, findings


def _check_capability(path: str, capability: str | None) -> list[Finding]:
    match = SPEC_PATH.match(path)
    if match is None or capability is None or capability == match.group(1):
        return []
    message = f"`capability` es `{capability}` pero la carpeta es `{match.group(1)}`"
    return [Finding("ANCH-003", message, path, 1)]


def _check_prefix(path: str, prefix: str | None) -> list[Finding]:
    if prefix is None:
        return []
    if not PREFIX.match(prefix):
        message = f"el prefijo `{prefix}` debe tener de 3 a 5 letras mayúsculas"
        return [Finding("ANCH-004", message, path, 1)]
    if prefix in RESERVED_PREFIXES:
        message = f"el prefijo `{prefix}` está reservado para `mejoras.md`"
        return [Finding("ANCH-004", message, path, 1)]
    return []


def _requirement_blocks(lines: list[str], start: int) -> list[_Block]:
    blocks: list[_Block] = []
    current: _Block | None = None
    section: str | None = None
    in_fence = False
    for number, line in enumerate(lines[start:], start=start + 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        heading = None if in_fence else _HEADING.match(line)
        if heading is not None:
            level, title = len(heading.group(1)), heading.group(2)
            if current is not None and level <= current.level:
                blocks.append(current)
                current = None
            if level <= 2:
                section = title if level == 2 else None
            elif section == REQUIREMENTS_SECTION and level in (3, 4):
                match = _REQUIREMENT_TITLE.match(title)
                if match is not None:
                    current = _Block(match.group(1), match.group(2), number, level)
                    continue
        if current is not None:
            current.body.append(line)
    if current is not None:
        blocks.append(current)
    return blocks


def _to_requirement(path: str, block: _Block) -> tuple[Requirement, list[Finding]]:
    findings: list[Finding] = []
    raw_status = next((m.group(1) for line in block.body if (m := _STATUS_LINE.match(line))), None)
    status: Status | None = None
    if raw_status is None:
        message = f"el requisito {block.id} no tiene línea `**Estado:**`"
        findings.append(Finding("ANCH-008", message, path, block.line))
    else:
        try:
            status = Status(raw_status)
        except ValueError:
            message = f"el requisito {block.id} tiene un estado desconocido: `{raw_status}`"
            findings.append(Finding("ANCH-008", message, path, block.line))
    has_reason = any(_REASON_LINE.match(line) for line in block.body)
    if status is Status.RETIRED and not has_reason:
        message = f"el requisito retirado {block.id} no tiene línea `**Motivo:**`"
        findings.append(Finding("ANCH-010", message, path, block.line))
    requirement = Requirement(
        id=block.id,
        title=block.title,
        line=block.line,
        status=status,
        has_doubt=any(_DOUBT in line for line in block.body),
        has_reason=has_reason,
        normative=_normative_text(block.body),
    )
    return requirement, findings


def _normative_text(body: list[str]) -> str:
    """Devuelve el enunciado y los criterios de aceptación, con los espacios normalizados."""
    kept: list[str] = []
    normative = False
    for line in body:
        field_match = _FIELD_LINE.match(line)
        if field_match is not None:
            normative = field_match.group(1).startswith(_NORMATIVE_FIELDS)
        if normative and line.strip():
            kept.append(" ".join(line.split()))
    return "\n".join(kept)
