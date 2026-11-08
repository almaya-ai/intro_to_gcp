"""Run each Claude Code hook as a real subprocess, the way the harness does."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"


def run_hook(name, payload, suite="true", project=ROOT):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project), "HOOK_TEST_COMMAND": suite}
    return subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def edit(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": path}}


@pytest.mark.parametrize(
    "command",
    ["./deploy.sh", "deploy.sh", "gcloud run deploy svc --source .", "cd /tmp && ./deploy.sh"],
)
def test_guard_blocks_deploy_when_tests_fail(command):
    result = run_hook("guard_deploy.py", bash(command), suite="false")
    assert result.returncode == 2
    assert "pytest" in result.stderr


def test_guard_allows_deploy_when_tests_pass():
    assert run_hook("guard_deploy.py", bash("./deploy.sh")).returncode == 0


@pytest.mark.parametrize("command", ["git status", 'git commit -m "update deploy.sh"', "cat deploy.sh"])
def test_guard_ignores_other_commands_even_when_tests_fail(command):
    assert run_hook("guard_deploy.py", bash(command), suite="false").returncode == 0


@pytest.mark.parametrize("path", ["/x/main.py", "/x/templates/page.html"])
def test_after_edit_reports_failing_tests_for_code(path):
    result = run_hook("after_edit.py", edit(path), suite="echo boom; false")
    assert result.returncode == 2
    assert "boom" in result.stderr


def test_after_edit_stays_quiet_when_tests_pass():
    assert run_hook("after_edit.py", edit("/x/main.py")).returncode == 0


def test_after_edit_skips_tests_for_documents():
    assert run_hook("after_edit.py", edit("/x/docs/notes.md"), suite="false").returncode == 0


def test_session_context_reports_candidates_ready_for_promotion(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "skill-candidates.md").write_text(
        "| a | 3 | מוכן לקידום |\n| b | 1 | מועמד |\n", encoding="utf-8"
    )
    result = run_hook("session_context.py", {}, project=tmp_path)
    assert result.returncode == 0
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "SessionStart"
    assert "מוכנים לקידום ל-skill: 1" in output["additionalContext"]


def test_session_context_ignores_the_explanation_table(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "skill-candidates.md").write_text(
        "| 3 ומעלה | `מוכן לקידום` | מציעים למשתמש |\n"
        "| פעולה | 4 | `מוכן לקידום` | הערה |\n"
        "| אחרת | 1 | `מועמד` | כשיגיע מוכן לקידום נדבר |\n",
        encoding="utf-8",
    )
    result = run_hook("session_context.py", {}, project=tmp_path)
    assert "מוכנים לקידום ל-skill: 1" in result.stdout


def test_session_context_survives_a_folder_without_git_or_candidates(tmp_path):
    result = run_hook("session_context.py", {}, project=tmp_path)
    assert result.returncode == 0
    assert "מוכנים לקידום ל-skill: 0" in result.stdout
