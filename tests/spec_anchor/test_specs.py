from collections.abc import Callable

import pytest

from spec_anchor.invariants import check_specs
from spec_anchor.model import Finding, Spec, Status
from spec_anchor.specs import find_specs, load_specs, parse_spec
from spec_anchor.tree import Tree

PATH = "specs/color-model/spec.md"


def header(capability: str = "color-model", prefix: str = "COLOR") -> str:
    return f"---\ncapability: {capability}\nprefix: {prefix}\nowner: Bartosz Kucmierz\n---\n"


def requirement(
    req_id: str = "COLOR-001", status: str | None = "approved", extra: str = "", level: int = 3
) -> str:
    status_line = f"- **Estado:** {status}\n" if status is not None else ""
    return (
        f"{'#' * level} {req_id} · Título\n\n"
        f"{status_line}"
        "- **Enunciado (EARS):** El sistema deberá hacer algo.\n"
        "- **Criterios de aceptación:**\n"
        "  1. Dado x, cuando y, entonces z.\n"
        f"{extra}\n"
    )


def spec_text(*requirements: str, head: str | None = None, notes: str = "") -> str:
    head = header() if head is None else head
    body = "\n".join(requirements)
    return (
        f"{head}\n# Spec\n\n## Propósito\n\nAlgo.\n\n## Requisitos\n\n{body}\n## Notas\n\n{notes}\n"
    )


def parse(text: str, path: str = PATH) -> tuple[Spec, list[Finding]]:
    return parse_spec(path, text)


def rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


# ANCH-001 · Descubrimiento de specs


@pytest.mark.spec("ANCH-001")
def test_only_spec_md_inside_a_capability_folder_is_a_spec(
    make_tree: Callable[[dict[str, str]], Tree],
) -> None:
    tree = make_tree(
        {
            "specs/color-model/spec.md": "",
            "specs/color-model/design.md": "",
            "docs/spec.md": "",
            "specs/spec.md": "",
            "specs/a/b/spec.md": "",
        }
    )
    assert find_specs(tree) == ["specs/color-model/spec.md"]


@pytest.mark.spec("ANCH-001")
def test_load_specs_reads_every_spec_of_the_tree(
    make_tree: Callable[[dict[str, str]], Tree],
) -> None:
    tree = make_tree(
        {
            "specs/color-model/spec.md": spec_text(requirement()),
            "specs/history/spec.md": spec_text(
                requirement("HIST-001"), head=header("history", "HIST")
            ),
            "README.md": "# pxls",
        }
    )
    specs, findings = load_specs(tree)
    assert sorted(s.path for s in specs) == ["specs/color-model/spec.md", "specs/history/spec.md"]
    assert findings == []


# ANCH-002 · Cabecera obligatoria


@pytest.mark.spec("ANCH-002")
def test_complete_header_has_no_error() -> None:
    spec, findings = parse(spec_text(requirement()))
    assert findings == []
    assert (spec.capability, spec.prefix, spec.owner) == (
        "color-model",
        "COLOR",
        "Bartosz Kucmierz",
    )


@pytest.mark.spec("ANCH-002")
def test_missing_header_field_is_reported_with_file_and_field() -> None:
    head = "---\ncapability: color-model\nprefix: COLOR\n---\n"
    _, findings = parse(spec_text(requirement(), head=head))
    assert rules(findings) == ["ANCH-002"]
    assert findings[0].path == PATH
    assert "owner" in findings[0].message


@pytest.mark.spec("ANCH-002")
def test_spec_without_header_is_reported_with_file() -> None:
    _, findings = parse(spec_text(requirement(), head=""))
    assert "ANCH-002" in rules(findings)
    assert all(f.path == PATH for f in findings)


# ANCH-003 · Capacidad coherente con la carpeta


@pytest.mark.spec("ANCH-003")
def test_capability_must_match_folder_name() -> None:
    text = spec_text(requirement("HIST-001"), head=header("historial", "HIST"))
    _, findings = parse(text, path="specs/history/spec.md")
    assert rules(findings) == ["ANCH-003"]
    assert "history" in findings[0].message
    assert "historial" in findings[0].message


# ANCH-004 · Prefijo válido y único


@pytest.mark.spec("ANCH-004")
def test_prefix_must_have_three_to_five_uppercase_letters() -> None:
    _, findings = parse(spec_text(head=header(prefix="Co")))
    assert rules(findings) == ["ANCH-004"]


@pytest.mark.spec("ANCH-004")
def test_prefix_mej_is_reserved() -> None:
    _, findings = parse(spec_text(head=header(prefix="MEJ")))
    assert rules(findings) == ["ANCH-004"]
    assert "reservado" in findings[0].message


@pytest.mark.spec("ANCH-004")
def test_prefix_used_by_two_specs_is_reported_naming_both() -> None:
    first, _ = parse(spec_text(requirement()))
    second, _ = parse(
        spec_text(requirement("COLOR-002"), head=header("palettes")),
        path="specs/palettes/spec.md",
    )
    findings = check_specs([first, second])
    assert rules(findings) == ["ANCH-004"]
    assert PATH in findings[0].message
    assert "specs/palettes/spec.md" in findings[0].message


# ANCH-005 · Reconocimiento de requisitos


@pytest.mark.spec("ANCH-005")
def test_level_3_and_4_headings_with_id_are_requirements() -> None:
    text = spec_text(
        "### Conversiones\n", requirement("COLOR-001", level=4), requirement("COLOR-002")
    )
    spec, findings = parse(text)
    assert [r.id for r in spec.requirements] == ["COLOR-001", "COLOR-002"]
    assert findings == []


@pytest.mark.spec("ANCH-005")
def test_heading_without_id_is_not_a_requirement() -> None:
    spec, _ = parse(spec_text("### Conversiones\n\nTexto.\n"))
    assert spec.requirements == ()


@pytest.mark.spec("ANCH-005")
def test_heading_outside_requirements_section_is_not_a_requirement() -> None:
    spec, _ = parse(spec_text(requirement(), notes=requirement("COLOR-009")))
    assert [r.id for r in spec.requirements] == ["COLOR-001"]


@pytest.mark.spec("ANCH-005")
def test_heading_inside_a_code_block_is_not_a_requirement() -> None:
    fenced = "```markdown\n" + requirement("COLOR-009") + "```\n"
    spec, _ = parse(spec_text(requirement(), fenced))
    assert [r.id for r in spec.requirements] == ["COLOR-001"]


@pytest.mark.spec("ANCH-005")
def test_requirement_records_its_heading_line() -> None:
    text = spec_text(requirement())
    spec, _ = parse(text)
    line = text.splitlines().index("### COLOR-001 · Título") + 1
    assert spec.requirements[0].line == line


# ANCH-006 · IDs bien formados (INV-1)


@pytest.mark.spec("ANCH-006")
def test_id_without_three_digits_is_malformed() -> None:
    spec, _ = parse(spec_text(requirement("COLOR-1")))
    findings = check_specs([spec])
    assert rules(findings) == ["INV-1"]
    assert "COLOR-1" in findings[0].message
    assert "formato" in findings[0].message


@pytest.mark.spec("ANCH-006")
def test_id_with_another_prefix_is_reported() -> None:
    spec, _ = parse(spec_text(requirement("PAL-001")))
    findings = check_specs([spec])
    assert rules(findings) == ["INV-1"]
    assert "prefijo" in findings[0].message


# ANCH-007 · IDs únicos (INV-1)


@pytest.mark.spec("ANCH-007")
def test_duplicated_id_is_reported_with_both_locations() -> None:
    text = spec_text(requirement(), requirement())
    spec, _ = parse(text)
    findings = check_specs([spec])
    lines = [i + 1 for i, line in enumerate(text.splitlines()) if line.startswith("### COLOR-001")]
    assert rules(findings) == ["INV-1"]
    assert all(f"{PATH}:{n}" in findings[0].message for n in lines)


# ANCH-008 · Estado obligatorio


@pytest.mark.spec("ANCH-008")
@pytest.mark.parametrize("status", list(Status))
def test_valid_statuses_are_read(status: Status) -> None:
    extra = "- **Motivo:** ya no aplica\n" if status is Status.RETIRED else ""
    spec, findings = parse(spec_text(requirement(status=status.value, extra=extra)))
    assert findings == []
    assert spec.requirements[0].status is status


@pytest.mark.spec("ANCH-008")
def test_missing_status_is_reported_with_id() -> None:
    spec, findings = parse(spec_text(requirement(status=None)))
    assert rules(findings) == ["ANCH-008"]
    assert "COLOR-001" in findings[0].message
    assert spec.requirements[0].status is None


@pytest.mark.spec("ANCH-008")
def test_unknown_status_is_reported_with_id_and_value() -> None:
    _, findings = parse(spec_text(requirement(status="hecho")))
    assert rules(findings) == ["ANCH-008"]
    assert "COLOR-001" in findings[0].message
    assert "hecho" in findings[0].message


# ANCH-009 · Sin dudas en requisitos aprobados o implementados (INV-1)

DOUBT = "- **Notas:** [NEEDS CLARIFICATION: ¿cuántos?]\n"


@pytest.mark.spec("ANCH-009")
def test_draft_requirement_may_have_open_doubts() -> None:
    spec, _ = parse(spec_text(requirement(status="draft", extra=DOUBT)))
    assert check_specs([spec]) == []


@pytest.mark.spec("ANCH-009")
@pytest.mark.parametrize("status", ["approved", "implemented"])
def test_approved_or_implemented_requirement_with_doubt_is_reported(status: str) -> None:
    spec, _ = parse(spec_text(requirement(status=status, extra=DOUBT)))
    findings = check_specs([spec])
    assert rules(findings) == ["INV-1"]
    assert "COLOR-001" in findings[0].message


# ANCH-010 · Requisitos retirados


@pytest.mark.spec("ANCH-010")
def test_retired_requirement_with_reason_is_valid() -> None:
    extra = "- **Motivo:** sustituido por COLOR-012\n"
    _, findings = parse(spec_text(requirement(status="retired", extra=extra)))
    assert findings == []


@pytest.mark.spec("ANCH-010")
def test_retired_requirement_without_reason_is_reported() -> None:
    _, findings = parse(spec_text(requirement(status="retired")))
    assert rules(findings) == ["ANCH-010"]
    assert "COLOR-001" in findings[0].message


@pytest.mark.spec("ANCH-002")
def test_header_without_closing_line_is_reported() -> None:
    text = "---\ncapability: color-model\nprefix: COLOR\nowner: Bartosz Kucmierz\n\n# Spec\n"
    _, findings = parse(text)
    assert rules(findings) == ["ANCH-002"]
    assert "cierre" in findings[0].message


@pytest.mark.spec("ANCH-002")
def test_header_lines_without_key_value_are_ignored() -> None:
    head = header().replace("owner:", "nota libre\nowner:")
    _, findings = parse(spec_text(requirement(), head=head))
    assert findings == []


@pytest.mark.spec("ANCH-005")
def test_requirement_at_end_of_file_is_read() -> None:
    text = header() + "\n## Requisitos\n\n" + requirement()
    spec, _ = parse(text)
    assert [r.id for r in spec.requirements] == ["COLOR-001"]
