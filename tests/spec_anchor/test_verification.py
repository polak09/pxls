import subprocess
import sys
import time
from pathlib import Path
from typing import Protocol

import pytest

from spec_anchor.cli import main, verify_full, verify_quick
from spec_anchor.gates import check_coverage, run_architecture, run_packaging, run_types
from spec_anchor.git import uncommitted_changes
from spec_anchor.model import Finding
from spec_anchor.report import exit_code, format_report
from spec_anchor.tree import DiskTree

REPO = Path(__file__).resolve().parents[2]
MODULE = "src/pxls/core/demo.py"
TESTS = "tests/test_demo.py"
SPEC = "specs/demo/spec.md"
MARKER = '@pytest.mark.spec("DEMO-001")\n'


class Project(Protocol):
    root: Path

    def read(self, path: str) -> str: ...
    def write(self, path: str, text: str) -> None: ...
    def replace(self, path: str, old: str, new: str) -> None: ...


def rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


# Copia de trabajo (soporte de ANCH-030)


@pytest.mark.spec("ANCH-030")
def test_disk_tree_lists_tracked_and_untracked_files_but_not_ignored_or_deleted(
    project: Project,
) -> None:
    project.write("nuevo.md", "x\n")
    project.write("ignored.txt", "x\n")
    (project.root / TESTS).unlink()
    tree = DiskTree(project.root)
    files = set(tree.files())
    assert {"nuevo.md", MODULE} <= files
    assert not {"ignored.txt", TESTS} & files
    assert tree.read("nuevo.md") == "x\n"


# ANCH-030 · Verificación rápida


@pytest.mark.spec("ANCH-030")
def test_quick_verification_passes_on_a_correct_project(project: Project) -> None:
    assert verify_quick(project.root) == []


@pytest.mark.spec("ANCH-030")
def test_quick_verification_reports_a_test_without_marker(project: Project) -> None:
    project.replace(TESTS, MARKER, "")
    assert "INV-2" in rules(verify_quick(project.root))


@pytest.mark.spec("ANCH-030")
def test_quick_verification_does_not_run_tests(project: Project) -> None:
    project.replace(TESTS, "== 4", "== 5")
    assert verify_quick(project.root) == []


@pytest.mark.spec("ANCH-030")
def test_quick_verification_reports_formatting_problems(project: Project) -> None:
    project.replace(MODULE, "return 2 * x", "return 2*x")
    findings = verify_quick(project.root)
    assert rules(findings) == ["ANCH-030"]
    assert findings[0].path == MODULE


@pytest.mark.spec("ANCH-030")
def test_quick_verification_reports_lint_errors_with_line(project: Project) -> None:
    project.replace(MODULE, '"""\n\n\n', '"""\n\nimport os\n\n\n')
    findings = verify_quick(project.root)
    assert rules(findings) == ["ANCH-030"]
    assert (findings[0].path, findings[0].line) == (MODULE, 6)
    assert "F401" in findings[0].message


@pytest.mark.spec("ANCH-030")
def test_quick_verification_reports_unparseable_files(project: Project) -> None:
    project.write("tests/test_broken.py", "def test_x(:\n    pass\n")
    findings = verify_quick(project.root)
    assert "ANCH-030" in rules(findings)
    assert any(f.path == "tests/test_broken.py" for f in findings)


# ANCH-031 · Verificación completa


@pytest.mark.spec("ANCH-031")
def test_full_verification_passes_on_a_correct_project(project: Project) -> None:
    assert verify_full(project.root) == []


@pytest.mark.spec("ANCH-031")
def test_full_verification_includes_the_commit_invariants(project: Project) -> None:
    project.replace(SPEC, "implemented", "approved")
    project.replace(TESTS, "== 4", "== 5")
    assert sorted(rules(verify_full(project.root))) == ["INV-6", "INV-7"]


@pytest.mark.spec("ANCH-031")
def test_type_error_is_reported(project: Project) -> None:
    project.replace(MODULE, "return 2 * x", 'return "x"')
    findings = run_types(project.root)
    assert rules(findings) == ["ANCH-031"]
    assert (findings[0].path, findings[0].line) == (MODULE, 9)


@pytest.mark.spec("ANCH-031")
def test_core_importing_adapters_is_reported(project: Project) -> None:
    project.write("src/pxls/adapters/screen.py", '"""Pantalla."""\n\nWIDTH = 1\n')
    project.replace(MODULE, '"""\n\n\n', '"""\n\nfrom pxls.adapters import screen\n\n\n')
    project.replace(MODULE, "2 * x", "screen.WIDTH * x")
    findings = run_architecture(project.root)
    assert rules(findings) == ["ANCH-031"]
    assert "Capas" in findings[0].message


# ANCH-032 · Umbrales de cobertura


@pytest.mark.spec("ANCH-032")
def test_total_coverage_below_85_is_reported_with_value() -> None:
    findings = check_coverage(84.9, None)
    assert rules(findings) == ["ANCH-032"]
    assert "84,9 %" in findings[0].message


@pytest.mark.spec("ANCH-032")
def test_core_coverage_below_95_is_reported_with_value() -> None:
    findings = check_coverage(90.0, 94.0)
    assert rules(findings) == ["ANCH-032"]
    assert "94 %" in findings[0].message
    assert "core" in findings[0].message


@pytest.mark.spec("ANCH-032")
@pytest.mark.parametrize(("total", "core"), [(85.0, 95.0), (100.0, None)])
def test_coverage_on_the_thresholds_is_valid(total: float, core: float | None) -> None:
    assert check_coverage(total, core) == []


# ANCH-033 · Empaquetado


def add_packaging(project: Project, package: str, smoke: str) -> None:
    python = Path(sys.executable).as_posix()
    config = (
        "\n[tool.spec-anchor]\n"
        f'package = ["{python}", "-c", "{package}"]\n'
        f'smoke = ["{python}", "-c", "{smoke}"]\n'
    )
    project.write("pyproject.toml", project.read("pyproject.toml") + config)


@pytest.mark.spec("ANCH-033")
def test_packaging_is_skipped_when_not_configured(project: Project) -> None:
    assert run_packaging(project.root) == []


@pytest.mark.spec("ANCH-033")
def test_failing_smoke_test_is_reported(project: Project) -> None:
    add_packaging(project, "pass", "raise SystemExit(1)")
    findings = run_packaging(project.root)
    assert rules(findings) == ["ANCH-033"]
    assert "humo" in findings[0].message


@pytest.mark.spec("ANCH-033")
def test_failing_packaging_is_reported(project: Project) -> None:
    add_packaging(project, "raise SystemExit(2)", "pass")
    findings = run_packaging(project.root)
    assert rules(findings) == ["ANCH-033"]
    assert "empaquetado" in findings[0].message


@pytest.mark.spec("ANCH-033")
def test_successful_packaging_and_smoke_test_are_valid(project: Project) -> None:
    add_packaging(project, "pass", "pass")
    assert run_packaging(project.root) == []


# ANCH-034 · El commit es todo lo que hay en disco


@pytest.mark.spec("ANCH-034")
def test_unstaged_and_untracked_files_are_listed(project: Project) -> None:
    project.replace(MODULE, "return 2 * x", "return x + x")
    project.write("nuevo.md", "x\n")
    findings = uncommitted_changes(project.root)
    assert rules(findings) == ["ANCH-034", "ANCH-034"]
    assert {f.path for f in findings} == {MODULE, "nuevo.md"}


@pytest.mark.spec("ANCH-034")
def test_ignored_files_are_not_taken_into_account(project: Project) -> None:
    project.write("ignored.txt", "x\n")
    assert uncommitted_changes(project.root) == []


# ANCH-035 · Informe de errores


@pytest.mark.spec("ANCH-035")
def test_report_shows_each_error_and_a_summary() -> None:
    findings = [
        Finding("INV-2", "el test test_parse no tiene marcador `spec`", "tests/test_hex.py", 12),
        Finding("ANCH-019", "falta el trailer `Change-Type`"),
    ]
    assert format_report(findings).splitlines() == [
        "ERROR [INV-2] tests/test_hex.py:12 · el test test_parse no tiene marcador `spec`",
        "ERROR [ANCH-019] falta el trailer `Change-Type`",
        "2 errores",
    ]


@pytest.mark.spec("ANCH-035")
def test_report_summary_for_one_and_no_errors() -> None:
    report = format_report([Finding("ANCH-034", "fichero sin preparar", "a.py")])
    assert report.splitlines() == ["ERROR [ANCH-034] a.py · fichero sin preparar", "1 error"]
    assert format_report([]) == "0 errores\n"


# ANCH-036 · Código de salida


@pytest.mark.spec("ANCH-036")
def test_exit_code_is_0_without_errors_and_1_with_errors() -> None:
    assert exit_code([]) == 0
    assert exit_code([Finding("INV-2", "x")]) == 1


@pytest.mark.spec("ANCH-036")
def test_command_line_returns_the_exit_code(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(project.root)
    assert main(["check", "--quick"]) == 0
    project.replace(TESTS, MARKER, "")
    assert main(["check", "--quick"]) == 1
    assert "INV-2" in capsys.readouterr().out


# ANCH-037 · Duración de la verificación rápida


@pytest.mark.spec("ANCH-037")
def test_quick_verification_of_the_project_takes_less_than_10_seconds() -> None:
    start = time.perf_counter()
    verify_quick(REPO)
    assert time.perf_counter() - start < 10


@pytest.mark.spec("ANCH-035")
def test_report_is_written_in_utf_8_when_output_is_a_pipe(project: Project) -> None:
    project.replace(TESTS, MARKER, "")
    command = [sys.executable, "-m", "spec_anchor", "check", "--quick"]
    result = subprocess.run(command, cwd=project.root, capture_output=True, check=False)
    assert result.returncode == 1
    assert "tests/test_demo.py:6 · el test" in result.stdout.decode("utf-8")
