import io
import json
from pathlib import Path
from typing import Protocol

import pytest

from spec_anchor.claude import MAX_STOP_BLOCKS, guard, stop
from spec_anchor.cli import main

REPO = Path(__file__).resolve().parents[2]
MODULE = "src/pxls/core/demo.py"


class Project(Protocol):
    root: Path

    def replace(self, path: str, old: str, new: str) -> None: ...


def bash(command: str, tool: str = "Bash") -> dict[str, object]:
    return {"tool_name": tool, "tool_input": {"command": command}}


def edit(path: str, tool: str = "Edit") -> dict[str, object]:
    return {"tool_name": tool, "tool_input": {"file_path": path}}


def blocked_by(payload: dict[str, object]) -> str | None:
    finding = guard(payload)
    return finding.rule if finding is not None else None


# ANCH-042 · Instrucciones para agentes


@pytest.mark.spec("ANCH-042")
def test_claude_md_points_to_the_constitution_and_the_task_list() -> None:
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    assert "[CONSTITUTION.md](CONSTITUTION.md)" in text
    assert "[tareas.md](tareas.md)" in text
    assert "antes de cualquier cambio" in text.lower()


# ANCH-043 · Verificación al final de cada turno


@pytest.mark.spec("ANCH-043")
def test_turn_leaving_a_module_without_spec_cannot_end(project: Project) -> None:
    project.replace(MODULE, "Spec: DEMO-001\n", "")
    code, out, err = stop(project.root, {})
    assert code == 2
    assert "INV-3" in err
    assert out == ""


@pytest.mark.spec("ANCH-043")
def test_turn_leaving_a_correct_working_copy_ends(project: Project) -> None:
    assert stop(project.root, {}) == (0, "", "")


@pytest.mark.spec("ANCH-043")
def test_repository_wires_the_claude_code_hooks() -> None:
    settings = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks = settings["hooks"]
    stop_commands = [h["command"] for entry in hooks["Stop"] for h in entry["hooks"]]
    assert any("spec_anchor claude stop" in command for command in stop_commands)
    [pre_tool] = hooks["PreToolUse"]
    assert set(pre_tool["matcher"].split("|")) >= {"Bash", "PowerShell", "Edit", "Write"}
    assert "spec_anchor claude guard" in pre_tool["hooks"][0]["command"]


# ANCH-047 · Salida tras bloqueos repetidos


@pytest.mark.spec("ANCH-047")
def test_agent_can_end_after_two_consecutive_blocks_and_the_person_sees_the_report(
    project: Project,
) -> None:
    project.replace(MODULE, "Spec: DEMO-001\n", "")
    assert [stop(project.root, {})[0] for _ in range(MAX_STOP_BLOCKS)] == [2, 2]
    code, out, _ = stop(project.root, {})
    assert code == 0
    assert "INV-3" in json.loads(out)["systemMessage"]
    assert stop(project.root, {})[0] == 2


@pytest.mark.spec("ANCH-047")
def test_fixing_the_problem_resets_the_count_and_ends_without_warning(project: Project) -> None:
    project.replace(MODULE, "Spec: DEMO-001\n", "")
    assert stop(project.root, {})[0] == 2
    project.replace(MODULE, '"""Demo.\n', '"""Demo.\n\nSpec: DEMO-001\n')
    assert stop(project.root, {}) == (0, "", "")
    project.replace(MODULE, "Spec: DEMO-001\n", "")
    assert [stop(project.root, {})[0] for _ in range(MAX_STOP_BLOCKS)] == [2, 2]


# ANCH-044 · Sin --no-verify


@pytest.mark.spec("ANCH-044")
@pytest.mark.parametrize(
    "command",
    ["git commit --no-verify -m x", "git push --no-verify", "git commit -n -m x", "git commit -qn"],
)
def test_skipping_git_hooks_is_blocked(command: str) -> None:
    assert blocked_by(bash(command)) == "ANCH-044"


# ANCH-045 · El agente no hace commits


@pytest.mark.spec("ANCH-045")
@pytest.mark.parametrize(
    "command",
    [
        "git commit -m x",
        "git merge dev",
        "git -C D:/dev/pxls cherry-pick abc",
        "git revert HEAD",
        "cd tools && git rebase main",
        "git am < parche.patch",
    ],
)
def test_git_commands_that_create_commits_are_blocked(command: str) -> None:
    assert blocked_by(bash(command)) == "ANCH-045"


@pytest.mark.spec("ANCH-045")
def test_commit_commands_are_also_blocked_in_powershell() -> None:
    assert blocked_by(bash("git commit -m x", tool="PowerShell")) == "ANCH-045"


@pytest.mark.spec("ANCH-045")
@pytest.mark.parametrize(
    "command",
    ["git status", "git log --grep=commit", "git merge-base dev main", "git diff --cached", "ls"],
)
def test_read_only_commands_are_allowed(command: str) -> None:
    assert blocked_by(bash(command)) is None


# ANCH-046 · Protección de la configuración


@pytest.mark.spec("ANCH-046")
@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit"])
def test_editing_the_claude_code_settings_is_blocked(tool: str) -> None:
    assert blocked_by(edit(r"D:\dev\pxls\.claude\settings.json", tool)) == "ANCH-046"


@pytest.mark.spec("ANCH-046")
def test_writing_a_git_hook_is_blocked() -> None:
    assert blocked_by(edit("D:/dev/pxls/.git/hooks/pre-commit", "Write")) == "ANCH-046"


@pytest.mark.spec("ANCH-046")
@pytest.mark.parametrize(
    "command",
    ["git config core.hooksPath /tmp", "rm .git/hooks/pre-commit", "del .git\\hooks\\commit-msg"],
)
def test_weakening_the_git_hooks_from_a_shell_is_blocked(command: str) -> None:
    assert blocked_by(bash(command)) == "ANCH-046"


@pytest.mark.spec("ANCH-046")
def test_editing_other_files_and_unknown_tools_are_allowed() -> None:
    assert blocked_by(edit("D:/dev/pxls/src/pxls/core/demo.py")) is None
    assert (
        blocked_by({"tool_name": "Read", "tool_input": {"file_path": ".claude/settings.json"}})
        is None
    )


# Línea de comandos de los hooks de Claude Code


@pytest.mark.spec("ANCH-045")
def test_guard_command_reads_the_tool_call_from_stdin_and_exits_with_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(bash("git commit -m x"))))
    assert main(["claude", "guard"]) == 2
    assert "ANCH-045" in capsys.readouterr().err


@pytest.mark.spec("ANCH-043")
def test_stop_command_runs_in_the_repository_of_the_current_directory(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project.root)
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    assert main(["claude", "stop"]) == 0
