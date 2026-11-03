from collections.abc import Callable

import pytest

from spec_anchor.invariants import check_modules, check_references, check_tests
from spec_anchor.model import CaseRef, Finding, ModuleRef, Spec
from spec_anchor.pyrefs import find_modules, find_tests, read_module, read_tests
from spec_anchor.specs import parse_spec
from spec_anchor.tree import Tree

TEST_PATH = "tests/core/test_hex.py"
MODULE_PATH = "src/pxls/core/hex.py"


def rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


def cases_of(source: str) -> list[CaseRef]:
    return read_tests(TEST_PATH, source)


def color_spec(*entries: tuple[str, str]) -> Spec:
    reqs = "".join(
        f"### {req_id} · Título\n\n- **Estado:** {status}\n- **Motivo:** x\n\n"
        for req_id, status in entries
    )
    text = (
        "---\ncapability: color-model\nprefix: COLOR\nowner: Bartosz Kucmierz\n---\n\n"
        f"## Requisitos\n\n{reqs}"
    )
    spec, _ = parse_spec("specs/color-model/spec.md", text)
    return spec


# ANCH-011 · Marcadores de test


@pytest.mark.spec("ANCH-011")
def test_ids_of_a_spec_marker_are_read() -> None:
    source = (
        "import pytest\n\n"
        '@pytest.mark.spec("COLOR-001", "COLOR-002")\n'
        "def test_hex() -> None:\n    pass\n"
    )
    [test] = cases_of(source)
    assert (test.name, test.ids) == ("test_hex", ("COLOR-001", "COLOR-002"))
    assert test.path == TEST_PATH
    assert test.line == 4


@pytest.mark.spec("ANCH-011")
def test_ids_of_several_spec_markers_are_joined() -> None:
    source = (
        "import pytest\n\n"
        '@pytest.mark.spec("COLOR-001")\n'
        '@pytest.mark.spec("COLOR-003")\n'
        "def test_hex() -> None:\n    pass\n"
    )
    [test] = cases_of(source)
    assert set(test.ids) == {"COLOR-001", "COLOR-003"}


@pytest.mark.spec("ANCH-011")
def test_marker_imported_as_mark_is_read() -> None:
    source = (
        'from pytest import mark\n\n@mark.spec("COLOR-001")\ndef test_hex() -> None:\n    pass\n'
    )
    [test] = cases_of(source)
    assert test.ids == ("COLOR-001",)


@pytest.mark.spec("ANCH-011")
def test_class_marker_applies_to_all_its_tests() -> None:
    source = (
        "import pytest\n\n"
        '@pytest.mark.spec("COLOR-001")\n'
        "class TestHex:\n"
        "    def test_a(self) -> None:\n        pass\n\n"
        '    @pytest.mark.spec("COLOR-002")\n'
        "    def test_b(self) -> None:\n        pass\n\n"
        "    def helper(self) -> None:\n        pass\n"
    )
    found = {t.name: set(t.ids) for t in cases_of(source)}
    assert found == {
        "TestHex::test_a": {"COLOR-001"},
        "TestHex::test_b": {"COLOR-001", "COLOR-002"},
    }


@pytest.mark.spec("ANCH-011")
def test_module_marker_does_not_count() -> None:
    source = (
        "import pytest\n\n"
        'pytestmark = pytest.mark.spec("COLOR-001")\n\n'
        "def test_hex() -> None:\n    pass\n"
    )
    [test] = cases_of(source)
    assert test.ids == ()


@pytest.mark.spec("ANCH-011")
def test_other_functions_and_markers_are_not_references() -> None:
    source = (
        "import pytest\n\n"
        "def helper() -> None:\n    pass\n\n"
        "@pytest.mark.slow\n"
        '@pytest.mark.parametrize("x", [1])\n'
        "def test_hex(x: int) -> None:\n    pass\n\n"
        "class Helper:\n    def test_not_collected(self) -> None:\n        pass\n"
    )
    assert [(t.name, t.ids) for t in cases_of(source)] == [("test_hex", ())]


@pytest.mark.spec("ANCH-011")
def test_only_test_files_under_tests_are_read(
    make_tree: Callable[[dict[str, str]], Tree],
) -> None:
    tree = make_tree(
        {
            "tests/test_a.py": "",
            "tests/core/test_b.py": "",
            "tests/conftest.py": "",
            "tests/core/helpers.py": "",
            "src/pxls/test_c.py": "",
        }
    )
    assert find_tests(tree) == ["tests/core/test_b.py", "tests/test_a.py"]


# ANCH-012 · Tests sin marcador (INV-2)


@pytest.mark.spec("ANCH-012")
def test_test_without_marker_is_reported_with_file_line_and_name() -> None:
    tests = cases_of("def test_parse() -> None:\n    pass\n")
    findings = check_tests(tests)
    assert rules(findings) == ["INV-2"]
    assert (findings[0].path, findings[0].line) == (TEST_PATH, 1)
    assert "test_parse" in findings[0].message


@pytest.mark.spec("ANCH-012")
def test_marked_test_is_valid() -> None:
    tests = cases_of(
        'import pytest\n\n@pytest.mark.spec("COLOR-001")\ndef test_a() -> None:\n    pass\n'
    )
    assert check_tests(tests) == []


# ANCH-013 · Declaración Spec: de los módulos


@pytest.mark.spec("ANCH-013")
def test_spec_line_of_module_docstring_is_read() -> None:
    source = (
        '"""Conversiones HEX.\n\nSpec: COLOR-001, COLOR-003\n"""\n\n'
        'def to_hex() -> str:\n    return ""\n'
    )
    module = read_module(MODULE_PATH, source)
    assert module.ids == ("COLOR-001", "COLOR-003")
    assert module.has_definitions
    assert module.line == 3


@pytest.mark.spec("ANCH-013")
def test_anchored_modules_are_python_files_under_src_and_tools(
    make_tree: Callable[[dict[str, str]], Tree],
) -> None:
    tree = make_tree(
        {
            "src/pxls/core/hex.py": "",
            "tools/spec_anchor/cli.py": "",
            "tests/test_a.py": "",
            "src/pxls/py.typed": "",
            "setup.py": "",
        }
    )
    assert find_modules(tree) == ["src/pxls/core/hex.py", "tools/spec_anchor/cli.py"]


# ANCH-014 · Módulos sin Spec: (INV-3)


@pytest.mark.spec("ANCH-014")
def test_module_with_definitions_and_no_docstring_is_reported() -> None:
    findings = check_modules([read_module(MODULE_PATH, "def to_hex() -> str:\n    return ''\n")])
    assert rules(findings) == ["INV-3"]
    assert findings[0].path == MODULE_PATH


@pytest.mark.spec("ANCH-014")
def test_reexporting_init_is_exempt() -> None:
    source = '"""Paquete."""\n\nfrom pxls.core.hex import to_hex\n\n__all__ = ["to_hex"]\n'
    assert check_modules([read_module("src/pxls/core/__init__.py", source)]) == []


@pytest.mark.spec("ANCH-014")
def test_module_with_empty_spec_line_is_reported() -> None:
    source = '"""Modelo.\n\nSpec:\n"""\n\nclass Color:\n    pass\n'
    findings = check_modules([read_module(MODULE_PATH, source)])
    assert rules(findings) == ["INV-3"]


@pytest.mark.spec("ANCH-014")
def test_async_function_counts_as_definition() -> None:
    module = read_module(MODULE_PATH, "async def run() -> None:\n    pass\n")
    assert module.has_definitions
    assert rules(check_modules([module])) == ["INV-3"]


# ANCH-015 · Referencias válidas (INV-4)


def case_ref(*ids: str) -> CaseRef:
    return CaseRef(TEST_PATH, 7, "test_x", ids)


@pytest.mark.spec("ANCH-015")
def test_reference_to_unknown_id_is_reported_with_place() -> None:
    findings = check_references(
        [color_spec(("COLOR-001", "approved"))], [case_ref("COLOR-099")], []
    )
    assert rules(findings) == ["INV-4"]
    assert (findings[0].path, findings[0].line) == (TEST_PATH, 7)
    assert "COLOR-099" in findings[0].message


@pytest.mark.spec("ANCH-015")
def test_reference_to_an_improvement_is_reported() -> None:
    module = ModuleRef(MODULE_PATH, 3, ("MEJ-003",), has_definitions=True)
    findings = check_references([color_spec(("COLOR-001", "approved"))], [], [module])
    assert rules(findings) == ["INV-4"]
    assert "mejora" in findings[0].message


@pytest.mark.spec("ANCH-015")
def test_reference_to_a_task_is_reported() -> None:
    findings = check_references([color_spec(("COLOR-001", "approved"))], [case_ref("T-012")], [])
    assert rules(findings) == ["INV-4"]
    assert "tarea" in findings[0].message


@pytest.mark.spec("ANCH-015")
def test_reference_to_a_retired_requirement_is_reported() -> None:
    findings = check_references([color_spec(("COLOR-001", "retired"))], [case_ref("COLOR-001")], [])
    assert rules(findings) == ["INV-4"]
    assert "retirado" in findings[0].message


@pytest.mark.spec("ANCH-015")
@pytest.mark.parametrize("status", ["draft", "approved", "implemented"])
def test_reference_to_a_live_requirement_is_valid(status: str) -> None:
    spec = color_spec(("COLOR-001", status))
    module = ModuleRef(MODULE_PATH, 3, ("COLOR-001",), has_definitions=True)
    assert check_references([spec], [case_ref("COLOR-001")], [module]) == []


@pytest.mark.spec("ANCH-013")
def test_spec_line_continues_on_the_following_indented_lines() -> None:
    source = '"""Módulo.\n\nSpec: COLOR-001,\n    COLOR-002, COLOR-003\n"""\n\nX = 1\n'
    module = read_module(MODULE_PATH, source)
    assert module.ids == ("COLOR-001", "COLOR-002", "COLOR-003")
    assert module.line == 3


@pytest.mark.spec("ANCH-013")
def test_spec_line_ends_at_a_blank_line() -> None:
    source = '"""Módulo.\n\nSpec: COLOR-001\n\n    COLOR-002\n"""\n'
    assert read_module(MODULE_PATH, source).ids == ("COLOR-001",)
