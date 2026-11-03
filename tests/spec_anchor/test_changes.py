from collections.abc import Callable

import pytest

from spec_anchor.changes import changed_paths, check_change, check_message
from spec_anchor.model import Finding
from spec_anchor.tree import Tree

SPEC = "specs/color-model/spec.md"
TESTS = "tests/test_color.py"
MODULE_A = "src/pxls/core/hex.py"
MODULE_B = "src/pxls/core/hsl.py"
CRITERION = "Dado x, cuando y, entonces z."

Files = dict[str, str]
Check = Callable[[Files, Files, str], list[Finding]]


def rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


def req(
    req_id: str,
    status: str = "implemented",
    criterion: str = CRITERION,
    notes: str = "",
    statement: str = "El sistema deberá algo.",
) -> str:
    text = (
        f"### {req_id} · Título\n\n- **Estado:** {status}\n"
        f"- **Enunciado (EARS):** {statement}\n"
        f"- **Criterios de aceptación:**\n  1. {criterion}\n"
    )
    if notes:
        text += f"- **Notas:** {notes}\n"
    if status == "retired":
        text += "- **Motivo:** ya no aplica\n"
    return text + "\n"


def spec(*reqs: str) -> str:
    head = "---\ncapability: color-model\nprefix: COLOR\nowner: Bartosz Kucmierz\n---\n\n"
    return head + "## Requisitos\n\n" + "".join(reqs)


def case(name: str, req_id: str, value: int = 1) -> str:
    return f'@pytest.mark.spec("{req_id}")\ndef {name}() -> None:\n    assert {value}\n\n'


def suite(*cases: str) -> str:
    return "import pytest\n\n" + "".join(cases)


def module(req_id: str, value: int = 1) -> str:
    return f'"""Módulo.\n\nSpec: {req_id}\n"""\n\n\ndef f() -> int:\n    return {value}\n'


BEFORE: Files = {
    SPEC: spec(req("COLOR-001"), req("COLOR-004")),
    TESTS: suite(
        case("test_a", "COLOR-001"), case("test_b", "COLOR-001"), case("test_c", "COLOR-004")
    ),
    MODULE_A: module("COLOR-001"),
    MODULE_B: module("COLOR-004"),
    "README.md": "# pxls\n",
    "pyproject.toml": "[project]\n",
    "mejoras.md": "# Mejoras\n",
    "tareas.md": "# Tareas\n",
}


def message(change_type: str, refs: str | None = None) -> str:
    text = f"subject\n\nbody\n\nChange-Type: {change_type}\n"
    return text + (f"Spec-Refs: {refs}\n" if refs is not None else "")


@pytest.fixture
def check(make_tree: Callable[[Files], Tree]) -> Check:
    def run(before: Files, after: Files, msg: str) -> list[Finding]:
        declaration, findings = check_message(msg)
        assert declaration is not None
        old, new = make_tree(before), make_tree(after)
        return findings + check_change(declaration, old, new, changed_paths(old, new))

    return run


def edit(**changes: str | None) -> Files:
    files = dict(BEFORE)
    for key, value in changes.items():
        path = {
            "spec": SPEC,
            "tests": TESTS,
            "a": MODULE_A,
            "b": MODULE_B,
            "readme": "README.md",
            "design": "specs/color-model/design.md",
            "pyproject": "pyproject.toml",
            "mejoras": "mejoras.md",
            "tareas": "tareas.md",
            "constitution": "CONSTITUTION.md",
        }[key]
        if value is None:
            files.pop(path, None)
        else:
            files[path] = value
    return files


# ANCH-019 · Trailer Change-Type


@pytest.mark.spec("ANCH-019")
def test_message_without_change_type_is_rejected() -> None:
    declaration, findings = check_message("subject\n\nbody\n")
    assert declaration is None
    assert rules(findings) == ["ANCH-019"]


@pytest.mark.spec("ANCH-019")
def test_unknown_change_type_is_rejected() -> None:
    declaration, findings = check_message(message("feature"))
    assert declaration is None
    assert rules(findings) == ["ANCH-019"]
    assert "feature" in findings[0].message


@pytest.mark.spec("ANCH-019")
def test_two_change_types_are_rejected() -> None:
    _, findings = check_message(message("chore") + "Change-Type: refactor\n")
    assert rules(findings) == ["ANCH-019"]


@pytest.mark.spec("ANCH-019")
def test_comment_lines_are_ignored() -> None:
    declaration, findings = check_message(message("chore") + "# Change-Type: refactor\n")
    assert findings == []
    assert declaration is not None
    assert declaration.change_type == "chore"


# ANCH-020 · Trailer Spec-Refs


@pytest.mark.spec("ANCH-020")
@pytest.mark.parametrize("change_type", ["behavior", "editorial"])
def test_spec_refs_is_required_in_behavior_and_editorial(change_type: str) -> None:
    _, findings = check_message(message(change_type))
    assert rules(findings) == ["ANCH-020"]


@pytest.mark.spec("ANCH-020")
@pytest.mark.parametrize("change_type", ["refactor", "chore"])
def test_spec_refs_is_forbidden_in_refactor_and_chore(change_type: str) -> None:
    _, findings = check_message(message(change_type, "COLOR-001"))
    assert rules(findings) == ["ANCH-020"]


@pytest.mark.spec("ANCH-020")
def test_spec_refs_must_be_a_comma_separated_list_of_ids() -> None:
    _, findings = check_message(message("behavior", "COLOR-001; COLOR-002"))
    assert rules(findings) == ["ANCH-020"]


@pytest.mark.spec("ANCH-020")
def test_spec_refs_is_optional_in_constitution() -> None:
    _, findings = check_message(message("constitution"))
    assert findings == []


@pytest.mark.spec("ANCH-020")
def test_declared_ids_are_read() -> None:
    declaration, findings = check_message(message("behavior", "COLOR-001, COLOR-004"))
    assert findings == []
    assert declaration is not None
    assert declaration.refs == ("COLOR-001", "COLOR-004")


# ANCH-021 · behavior: cada ID declarado cambia en spec y tests


@pytest.mark.spec("ANCH-021")
def test_behavior_changing_criteria_and_a_marked_test_is_accepted(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004", criterion="Dado w, cuando y, entonces z.")),
        tests=suite(
            case("test_a", "COLOR-001"), case("test_b", "COLOR-001"), case("test_c", "COLOR-004", 2)
        ),
        b=module("COLOR-004", 2),
    )
    assert check(BEFORE, after, message("behavior", "COLOR-004")) == []


@pytest.mark.spec("ANCH-021")
def test_behavior_changing_only_notes_is_rejected(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004", notes="aclaración")),
        tests=suite(
            case("test_a", "COLOR-001"), case("test_b", "COLOR-001"), case("test_c", "COLOR-004", 2)
        ),
    )
    findings = check(BEFORE, after, message("behavior", "COLOR-004"))
    assert rules(findings) == ["ANCH-021"]
    assert "texto normativo" in findings[0].message


@pytest.mark.spec("ANCH-021")
def test_behavior_without_test_changes_is_rejected(check: Check) -> None:
    after = edit(spec=spec(req("COLOR-001"), req("COLOR-004", criterion="Dado w, cuando y.")))
    findings = check(BEFORE, after, message("behavior", "COLOR-004"))
    assert rules(findings) == ["ANCH-021"]
    assert "test" in findings[0].message


@pytest.mark.spec("ANCH-021")
def test_behavior_changing_a_test_of_another_requirement_is_rejected(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004", criterion="Dado w, cuando y.")),
        tests=suite(
            case("test_a", "COLOR-001", 2), case("test_b", "COLOR-001"), case("test_c", "COLOR-004")
        ),
    )
    assert rules(check(BEFORE, after, message("behavior", "COLOR-004"))) == ["ANCH-021"]


@pytest.mark.spec("ANCH-021")
def test_behavior_adding_a_requirement_and_its_test_is_accepted(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004"), req("COLOR-010")),
        tests=BEFORE[TESTS] + case("test_d", "COLOR-010"),
        pyproject="[project]\nversion = '1'\n",
    )
    assert check(BEFORE, after, message("behavior", "COLOR-010")) == []


@pytest.mark.spec("ANCH-021")
def test_behavior_retiring_a_requirement_and_deleting_its_test_is_accepted(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004", status="retired", criterion="—")),
        tests=suite(case("test_a", "COLOR-001"), case("test_b", "COLOR-001")),
        b=None,
    )
    assert check(BEFORE, after, message("behavior", "COLOR-004")) == []


# ANCH-022 · behavior: el código cambiado pertenece a los IDs declarados


@pytest.mark.spec("ANCH-022")
def test_behavior_modifying_a_module_of_another_requirement_is_rejected(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004", criterion="Dado w, cuando y.")),
        tests=suite(
            case("test_a", "COLOR-001"), case("test_b", "COLOR-001"), case("test_c", "COLOR-004", 2)
        ),
        a=module("COLOR-001", 2),
    )
    findings = check(BEFORE, after, message("behavior", "COLOR-004"))
    assert rules(findings) == ["ANCH-022"]
    assert findings[0].path == MODULE_A


@pytest.mark.spec("ANCH-022")
def test_behavior_adding_a_module_without_definitions_is_accepted(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001"), req("COLOR-004", criterion="Dado w, cuando y.")),
        tests=suite(
            case("test_a", "COLOR-001"), case("test_b", "COLOR-001"), case("test_c", "COLOR-004", 2)
        ),
    )
    after["src/pxls/core/__init__.py"] = (
        '"""Dominio."""\n\nfrom pxls.core.hsl import f\n\n__all__ = ["f"]\n'
    )
    assert check(BEFORE, after, message("behavior", "COLOR-004")) == []


# ANCH-023 · refactor


@pytest.mark.spec("ANCH-023")
def test_refactor_modifying_a_spec_is_rejected(check: Check) -> None:
    after = edit(spec=spec(req("COLOR-001", notes="nota"), req("COLOR-004")))
    findings = check(BEFORE, after, message("refactor"))
    assert rules(findings) == ["ANCH-023"]
    assert findings[0].path == SPEC


@pytest.mark.spec("ANCH-023")
def test_refactor_removing_a_test_of_a_requirement_is_rejected(check: Check) -> None:
    after = edit(tests=suite(case("test_a", "COLOR-001"), case("test_c", "COLOR-004")))
    findings = check(BEFORE, after, message("refactor"))
    assert rules(findings) == ["ANCH-023"]
    assert "COLOR-001" in findings[0].message


@pytest.mark.spec("ANCH-023")
def test_refactor_modifying_only_modules_is_accepted(check: Check) -> None:
    after = edit(a=module("COLOR-001", 2), b=module("COLOR-004", 3), pyproject="[project]\nx = 1\n")
    assert check(BEFORE, after, message("refactor")) == []


# ANCH-024 · editorial


@pytest.mark.spec("ANCH-024")
def test_editorial_fixing_a_typo_in_a_statement_is_accepted(check: Check) -> None:
    after = edit(spec=spec(req("COLOR-001", statement="El sistema deberá algo,"), req("COLOR-004")))
    assert check(BEFORE, after, message("editorial", "COLOR-001")) == []


@pytest.mark.spec("ANCH-024")
def test_editorial_fixing_readme_and_design_is_accepted(check: Check) -> None:
    after = edit(readme="# pxls\n\nColor picker.\n", design="# Diseño\n")
    assert check(BEFORE, after, message("editorial", "COLOR-001")) == []


@pytest.mark.spec("ANCH-024")
def test_editorial_changing_a_status_is_rejected(check: Check) -> None:
    after = edit(spec=spec(req("COLOR-001", status="retired"), req("COLOR-004")))
    findings = check(BEFORE, after, message("editorial", "COLOR-001"))
    assert rules(findings) == ["ANCH-024"]
    assert "COLOR-001" in findings[0].message


@pytest.mark.spec("ANCH-024")
def test_editorial_adding_or_removing_requirements_is_rejected(check: Check) -> None:
    after = edit(spec=spec(req("COLOR-001"), req("COLOR-005")))
    assert rules(check(BEFORE, after, message("editorial", "COLOR-001"))) == [
        "ANCH-024",
        "ANCH-024",
    ]


@pytest.mark.spec("ANCH-024")
@pytest.mark.parametrize("key", ["mejoras", "pyproject", "a", "tests"])
def test_editorial_touching_non_documentation_files_is_rejected(check: Check, key: str) -> None:
    after = edit(**{key: BEFORE[edit_path(key)] + "\n# cambio\n"})
    findings = check(BEFORE, after, message("editorial", "COLOR-001"))
    assert rules(findings) == ["ANCH-024"]


def edit_path(key: str) -> str:
    return {"mejoras": "mejoras.md", "pyproject": "pyproject.toml", "a": MODULE_A, "tests": TESTS}[
        key
    ]


# ANCH-025 · chore


@pytest.mark.spec("ANCH-025")
def test_chore_modifying_only_configuration_is_accepted(check: Check) -> None:
    after = edit(pyproject="[project]\nname = 'pxls'\n", mejoras="# Mejoras\n\n## MEJ-009\n")
    assert check(BEFORE, after, message("chore")) == []


@pytest.mark.spec("ANCH-025")
@pytest.mark.parametrize("key", ["a", "tests", "spec"])
def test_chore_modifying_anchored_files_is_rejected(check: Check, key: str) -> None:
    path = {"a": MODULE_A, "tests": TESTS, "spec": SPEC}[key]
    after = edit(**{key: BEFORE[path] + "\n# cambio\n"})
    findings = check(BEFORE, after, message("chore"))
    assert rules(findings) == ["ANCH-025"]
    assert findings[0].path == path


# ANCH-026 · constitution


def constitution(version: str, *history: str) -> str:
    rows = "".join(f"| {v} | 2026-10-25 | constitution | Cambio. |\n" for v in history)
    return (
        f"# Constitución\n\n| | |\n|---|---|\n| **Versión** | {version} |\n\n"
        "## Historial de enmiendas\n\n"
        f"| Versión | Fecha | Clase | Cambio |\n|---|---|---|---|\n{rows}"
    )


@pytest.mark.spec("ANCH-026")
def test_constitution_raising_version_with_history_row_is_accepted(check: Check) -> None:
    before = edit(constitution=constitution("1.1.0", "1.0.0", "1.1.0"))
    after = edit(constitution=constitution("1.2.0", "1.0.0", "1.1.0", "1.2.0"), tareas="# T\n")
    assert check(before, after, message("constitution")) == []


@pytest.mark.spec("ANCH-026")
def test_constitution_without_raising_version_is_rejected(check: Check) -> None:
    before = edit(constitution=constitution("1.1.0", "1.1.0"))
    after = edit(constitution=constitution("1.1.0", "1.1.0") + "\nTexto nuevo.\n")
    findings = check(before, after, message("constitution"))
    assert rules(findings) == ["ANCH-026"]
    assert "versión" in findings[0].message


@pytest.mark.spec("ANCH-026")
def test_constitution_without_history_row_is_rejected(check: Check) -> None:
    before = edit(constitution=constitution("1.1.0", "1.1.0"))
    after = edit(constitution=constitution("1.2.0", "1.1.0"))
    findings = check(before, after, message("constitution"))
    assert rules(findings) == ["ANCH-026"]
    assert "1.2.0" in findings[0].message


@pytest.mark.spec("ANCH-026")
def test_constitution_without_version_field_is_rejected(check: Check) -> None:
    before = edit(constitution=constitution("1.1.0", "1.1.0"))
    after = edit(constitution="# Constitución\n\nSin cabecera.\n")
    assert rules(check(before, after, message("constitution"))) == ["ANCH-026"]


@pytest.mark.spec("ANCH-024")
def test_editorial_creating_a_spec_is_rejected(check: Check) -> None:
    after = edit()
    after["specs/history/spec.md"] = spec(req("HIST-001")).replace("color-model", "history")
    findings = check(BEFORE, after, message("editorial", "HIST-001"))
    assert rules(findings) == ["ANCH-024"]
    assert "HIST-001" in findings[0].message


@pytest.mark.spec("ANCH-026")
def test_constitution_commit_must_modify_the_constitution(check: Check) -> None:
    after = edit(readme="# pxls\n\nOtro.\n")
    assert rules(check(BEFORE, after, message("constitution"))) == ["ANCH-026"]


# ANCH-027 · tareas.md en cualquier clase


@pytest.mark.spec("ANCH-027")
def test_tasks_file_is_accepted_with_a_chore(check: Check) -> None:
    after = edit(pyproject="[project]\nname = 'pxls'\n", tareas="# Tareas\n\n- T-001\n")
    assert check(BEFORE, after, message("chore")) == []


@pytest.mark.spec("ANCH-027")
def test_tasks_file_is_accepted_with_an_editorial(check: Check) -> None:
    after = edit(
        spec=spec(req("COLOR-001", statement="El sistema deberá algo,"), req("COLOR-004")),
        tareas="# Tareas\n\n- T-001\n",
    )
    assert check(BEFORE, after, message("editorial", "COLOR-001")) == []


@pytest.mark.spec("ANCH-027")
def test_tasks_file_is_accepted_with_a_refactor(check: Check) -> None:
    after = edit(a=module("COLOR-001", 2), tareas="# Tareas\n\n- T-001\n")
    assert check(BEFORE, after, message("refactor")) == []
