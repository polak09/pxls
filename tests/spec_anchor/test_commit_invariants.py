from pathlib import Path

import pytest

from spec_anchor.gates import run_tests
from spec_anchor.invariants import check_anchored, check_pending
from spec_anchor.model import CaseRef, Finding, ModuleRef, Spec
from spec_anchor.specs import parse_spec

TEST_PATH = "tests/core/test_hex.py"
MODULE_PATH = "src/pxls/core/hex.py"


def rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


def color_spec(*entries: tuple[str, str]) -> Spec:
    reqs = "".join(
        f"### {req_id} · Título\n\n- **Estado:** {status}\n\n" for req_id, status in entries
    )
    text = (
        "---\ncapability: color-model\nprefix: COLOR\nowner: Bartosz Kucmierz\n---\n\n"
        f"## Requisitos\n\n{reqs}"
    )
    spec, _ = parse_spec("specs/color-model/spec.md", text)
    return spec


def case(*ids: str) -> CaseRef:
    return CaseRef(TEST_PATH, 7, "test_x", ids)


def module(*ids: str) -> ModuleRef:
    return ModuleRef(MODULE_PATH, 3, ids, has_definitions=True)


# ANCH-016 · Requisitos implementados anclados (INV-5)


@pytest.mark.spec("ANCH-016")
def test_implemented_requirement_without_tests_is_reported() -> None:
    spec = color_spec(("COLOR-001", "implemented"))
    findings = check_anchored([spec], [], [module("COLOR-001")])
    assert rules(findings) == ["INV-5"]
    assert "COLOR-001" in findings[0].message
    assert "sin tests" in findings[0].message


@pytest.mark.spec("ANCH-016")
def test_implemented_requirement_without_code_is_reported() -> None:
    spec = color_spec(("COLOR-001", "implemented"))
    findings = check_anchored([spec], [case("COLOR-001")], [])
    assert rules(findings) == ["INV-5"]
    assert "sin código" in findings[0].message


@pytest.mark.spec("ANCH-016")
def test_implemented_requirement_with_tests_and_code_is_valid() -> None:
    spec = color_spec(("COLOR-001", "implemented"), ("COLOR-002", "retired"))
    assert check_anchored([spec], [case("COLOR-001")], [module("COLOR-001")]) == []


# ANCH-017 · Sin requisitos pendientes (INV-6)


@pytest.mark.spec("ANCH-017")
@pytest.mark.parametrize("status", ["draft", "approved"])
def test_pending_requirement_is_reported(status: str) -> None:
    findings = check_pending([color_spec(("COLOR-004", status))])
    assert rules(findings) == ["INV-6"]
    assert "COLOR-004" in findings[0].message


@pytest.mark.spec("ANCH-017")
def test_implemented_and_retired_requirements_are_valid() -> None:
    spec = color_spec(("COLOR-001", "implemented"), ("COLOR-002", "retired"))
    assert check_pending([spec]) == []


# ANCH-018 · Tests en verde (INV-7)


def write_project(root: Path, **files: str) -> Path:
    tests = root / "tests"
    tests.mkdir()
    for name, body in files.items():
        (tests / f"{name}.py").write_text(body, encoding="utf-8")
    return root


@pytest.mark.spec("ANCH-018")
def test_failing_test_is_reported_by_name(tmp_path: Path) -> None:
    root = write_project(
        tmp_path,
        test_ok="def test_pass() -> None:\n    assert True\n",
        test_bad="def test_fail() -> None:\n    assert 1 == 2\n",
    )
    findings = run_tests(root)
    assert rules(findings) == ["INV-7"]
    assert "tests/test_bad.py::test_fail" in findings[0].message
    assert findings[0].path == "tests/test_bad.py"


@pytest.mark.spec("ANCH-018")
def test_passing_suite_has_no_error(tmp_path: Path) -> None:
    root = write_project(tmp_path, test_ok="def test_pass() -> None:\n    assert True\n")
    assert run_tests(root) == []


@pytest.mark.spec("ANCH-018")
def test_project_without_tests_has_no_error(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    assert run_tests(tmp_path) == []


@pytest.mark.spec("ANCH-018")
def test_test_file_that_cannot_be_collected_is_reported(tmp_path: Path) -> None:
    root = write_project(tmp_path, test_broken="def test_x(:\n    pass\n")
    findings = run_tests(root)
    assert rules(findings) == ["INV-7"]
    assert "tests/test_broken.py" in findings[0].message


@pytest.mark.spec("ANCH-018")
def test_suite_that_cannot_start_is_reported_with_exit_code(tmp_path: Path) -> None:
    root = write_project(tmp_path, test_ok="def test_pass() -> None:\n    assert True\n")
    findings = run_tests(root, ["--no-such-option"])
    assert rules(findings) == ["INV-7"]
    assert "código 4" in findings[0].message
