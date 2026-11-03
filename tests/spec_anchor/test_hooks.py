import subprocess
import sys
from pathlib import Path
from typing import Protocol

import pytest

from spec_anchor.cli import verify_quick
from spec_anchor.gates import run_tests
from spec_anchor.hooks import HOOK_NAMES, MARKER, check_hooks_installed, install
from spec_anchor.model import Finding
from spec_anchor.tree import GitTree

MODULE = "src/pxls/core/demo.py"
TESTS = "tests/test_demo.py"
MARKER_LINE = '@pytest.mark.spec("DEMO-001")\n'
VALID_MESSAGE = "feat: duplicar\n\nChange-Type: behavior\nSpec-Refs: DEMO-001\n"
RUNNER_FOR_TESTS = "python -m spec_anchor"
RUNNER = f'"{Path(sys.executable).as_posix()}" -m spec_anchor'


class Project(Protocol):
    root: Path

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]: ...
    def read(self, path: str) -> str: ...
    def write(self, path: str, text: str) -> None: ...
    def replace(self, path: str, old: str, new: str) -> None: ...


def rules(findings: list[Finding]) -> list[str]:
    return [f.rule for f in findings]


def hooks_dir(project: Project) -> Path:
    return project.root / ".git" / "hooks"


def commit(project: Project, message: str) -> subprocess.CompletedProcess[str]:
    project.git("add", "-A")
    return project.git("commit", "-q", "-m", message, check=False)


def output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def commit_count(project: Project) -> int:
    result = project.git("rev-list", "--count", "HEAD", check=False)
    return int(result.stdout) if result.returncode == 0 else 0


# Árboles de git (antes y después del commit)


@pytest.mark.spec("ANCH-021")
def test_git_tree_reads_a_revision_and_the_index(bare_project: Project) -> None:
    bare_project.git("commit", "-q", "-m", "init")
    bare_project.replace(MODULE, "2 * x", "x + x")
    bare_project.write("nuevo.md", "x\n")
    bare_project.git("add", "-A")
    head, index = GitTree(bare_project.root, "HEAD"), GitTree(bare_project.root, None)
    assert "2 * x" in head.read(MODULE)
    assert "x + x" in index.read(MODULE)
    assert "nuevo.md" in set(index.files()) - set(head.files())


@pytest.mark.spec("ANCH-021")
def test_git_tree_of_an_unborn_branch_is_empty(bare_project: Project) -> None:
    assert list(GitTree(bare_project.root, "HEAD").files()) == []


# ANCH-038 · Instalación de los hooks


@pytest.mark.spec("ANCH-038")
def test_install_creates_the_three_hooks(bare_project: Project) -> None:
    assert install(bare_project.root, RUNNER_FOR_TESTS) == []
    for name in HOOK_NAMES:
        script = (hooks_dir(bare_project) / name).read_text(encoding="utf-8")
        assert MARKER in script
        assert f"{RUNNER_FOR_TESTS} hook {name}" in script
    assert set(HOOK_NAMES) == {"pre-commit", "pre-merge-commit", "commit-msg"}


@pytest.mark.spec("ANCH-038")
def test_install_twice_leaves_the_same_hooks(bare_project: Project) -> None:
    install(bare_project.root, RUNNER_FOR_TESTS)
    before = {name: (hooks_dir(bare_project) / name).read_bytes() for name in HOOK_NAMES}
    assert install(bare_project.root, RUNNER_FOR_TESTS) == []
    after = {name: (hooks_dir(bare_project) / name).read_bytes() for name in HOOK_NAMES}
    assert before == after


@pytest.mark.spec("ANCH-038")
def test_install_uses_uv_by_default(bare_project: Project) -> None:
    install(bare_project.root)
    assert "uv run --frozen spec-anchor hook pre-commit" in (
        hooks_dir(bare_project) / "pre-commit"
    ).read_text(encoding="utf-8")


# ANCH-039 · Hooks ajenos


@pytest.mark.spec("ANCH-039")
def test_foreign_hook_is_kept_and_reported(bare_project: Project) -> None:
    foreign = hooks_dir(bare_project) / "pre-commit"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text("#!/bin/sh\necho mío\n", encoding="utf-8")
    findings = install(bare_project.root, RUNNER_FOR_TESTS)
    assert rules(findings) == ["ANCH-039"]
    assert "pre-commit" in findings[0].message
    assert foreign.read_text(encoding="utf-8") == "#!/bin/sh\necho mío\n"
    assert MARKER in (hooks_dir(bare_project) / "commit-msg").read_text(encoding="utf-8")


# ANCH-041 · Aviso de hooks no instalados


@pytest.mark.spec("ANCH-041")
def test_quick_verification_fails_while_hooks_are_not_installed(bare_project: Project) -> None:
    findings = verify_quick(bare_project.root)
    assert rules(findings) == ["ANCH-041"]
    assert "spec-anchor install" in findings[0].message


@pytest.mark.spec("ANCH-041")
def test_installed_hooks_are_detected(project: Project) -> None:
    assert check_hooks_installed(project.root) == []


# ANCH-028 · Sólo dev y main


@pytest.mark.spec("ANCH-028")
def test_commit_on_another_branch_is_rejected(project: Project) -> None:
    project.git("checkout", "-q", "-b", "feature/x")
    result = commit(project, VALID_MESSAGE)
    assert result.returncode != 0
    assert "ANCH-028" in output(result)
    assert "II.6" in output(result)
    assert commit_count(project) == 0


# ANCH-029 · Commits en main


@pytest.mark.spec("ANCH-029")
def test_normal_commit_on_main_is_rejected(project: Project) -> None:
    project.git("checkout", "-q", "-b", "main")
    result = commit(project, VALID_MESSAGE)
    assert result.returncode != 0
    assert "ANCH-029" in output(result)


@pytest.fixture
def history(bare_project: Project) -> Project:
    """Proyecto con ramas `main`, `dev` y `other` creadas antes de instalar los hooks."""
    bare_project.git("commit", "-q", "-m", "init")
    bare_project.git("branch", "main")
    bare_project.git("branch", "other")
    bare_project.replace(MODULE, "2 * x", "x + x")
    bare_project.git("commit", "-q", "-am", "dev change")
    bare_project.git("checkout", "-q", "other")
    bare_project.write("README.md", "otro\n")
    bare_project.git("add", "-A")
    bare_project.git("commit", "-q", "-m", "other change")
    bare_project.git("checkout", "-q", "main")
    assert install(bare_project.root, RUNNER) == []
    return bare_project


@pytest.mark.spec("ANCH-029")
def test_release_merge_from_dev_is_accepted(history: Project) -> None:
    result = history.git("merge", "-q", "--no-ff", "dev", "-m", "release 0.1.0", check=False)
    assert result.returncode == 0, output(result)
    assert "x + x" in history.read(MODULE)


@pytest.mark.spec("ANCH-029")
def test_merge_of_another_branch_into_main_is_rejected(history: Project) -> None:
    result = history.git("merge", "-q", "--no-ff", "other", "-m", "merge other", check=False)
    assert result.returncode != 0
    assert "ANCH-029" in output(result)


# ANCH-040 · Commit bloqueado


@pytest.mark.spec("ANCH-040")
def test_commit_with_a_test_without_marker_is_not_created(project: Project) -> None:
    project.replace(TESTS, MARKER_LINE, "")
    result = commit(project, VALID_MESSAGE)
    assert result.returncode != 0
    assert "INV-2" in output(result)
    assert commit_count(project) == 0


@pytest.mark.spec("ANCH-040")
def test_commit_without_trailers_is_not_created(project: Project) -> None:
    result = commit(project, "feat: duplicar")
    assert result.returncode != 0
    assert "ANCH-019" in output(result)
    assert commit_count(project) == 0


@pytest.mark.spec("ANCH-040")
def test_valid_commit_is_created(project: Project) -> None:
    result = commit(project, VALID_MESSAGE)
    assert result.returncode == 0, output(result)
    assert commit_count(project) == 1


@pytest.mark.spec("ANCH-040")
def test_tools_run_by_the_hooks_do_not_inherit_git_variables(
    bare_project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    bare_project.write(
        "tests/test_env.py",
        "import os\n\n\ndef test_env() -> None:\n    assert 'GIT_DIR' not in os.environ\n",
    )
    monkeypatch.setenv("GIT_DIR", str(Path.cwd() / ".git"))
    assert run_tests(bare_project.root) == []


@pytest.mark.spec("ANCH-029")
def test_release_merge_completed_after_a_conflict_is_accepted(bare_project: Project) -> None:
    bare_project.git("commit", "-q", "-m", "init")
    bare_project.git("branch", "main")
    bare_project.replace(MODULE, "2 * x", "x + x")
    bare_project.git("commit", "-q", "-am", "dev change")
    bare_project.git("checkout", "-q", "main")
    bare_project.replace(MODULE, "2 * x", "x * 2")
    bare_project.git("commit", "-q", "-am", "main change")
    assert install(bare_project.root, RUNNER) == []
    assert bare_project.git("merge", "-q", "--no-ff", "dev", check=False).returncode != 0
    bare_project.git("checkout", "--theirs", MODULE)
    result = commit(bare_project, "release 0.1.0")
    assert result.returncode == 0, output(result)
