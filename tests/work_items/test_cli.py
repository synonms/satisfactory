import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).parents[2]


def run_cli(board: Path, *arguments: str, input_value: object | None = None) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        ".agents/run.py",
        "work_items",
        "--board-root",
        str(board),
        *arguments,
    ]
    input_text = json.dumps(input_value) if input_value is not None else None
    return subprocess.run(
        command,
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def create_input() -> list[dict]:
    return [
        {
            "type": "documentation",
            "request": "Document work-item commands",
            "description": "Describe the supported command interface.",
            "content": "Creation, retrieval, listing, and lifecycle transitions.",
        }
    ]


def response(process: subprocess.CompletedProcess[str]) -> dict:
    assert process.stdout
    assert process.stderr == ""
    return json.loads(process.stdout)


def test_cli_creates_and_reads_work_item_across_processes(tmp_path: Path) -> None:
    board = tmp_path / "board with spaces"

    created = run_cli(board, "create-request", "--input", "-", input_value=create_input())
    fetched = run_cli(board, "get", "00001-1")

    assert created.returncode == 0
    assert response(created)["data"][0]["id"] == "00001-1"
    assert fetched.returncode == 0
    assert response(fetched)["data"]["request"] == "Document work-item commands"


def test_cli_defaults_to_bundled_board(tmp_path: Path) -> None:
    shutil.copytree(
        ROOT / ".agents", tmp_path / ".agents", ignore=shutil.ignore_patterns("board", "__pycache__")
    )
    created = subprocess.run(
        [sys.executable, ".agents/run.py", "work_items", "create-request", "--input", "-"],
        cwd=tmp_path,
        input=json.dumps(create_input()),
        text=True,
        capture_output=True,
        check=False,
    )
    status = subprocess.run(
        [sys.executable, ".agents/run.py", "adlc", "status", "00001-1"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert created.returncode == 0, created.stderr
    assert (tmp_path / ".agents/board/00001/00001-1.work-item.json").is_file()
    assert not (tmp_path / "board").exists()
    assert status.returncode == 0, status.stderr
    assert json.loads(status.stdout)["data"]["workItemId"] == "00001-1"


def test_cli_records_intake_metrics(tmp_path: Path) -> None:
    board = tmp_path / "board"
    run_cli(board, "create-request", "--input", "-", input_value=create_input())

    intake = run_cli(
        board,
        "record_intake",
        "00001-1",
        "--input",
        "-",
        input_value={
            "agent": "software-architect",
            "result": "Authored the documentation task plan.",
            "metrics": {
                "durationSeconds": 30,
                "inputTokens": 200,
                "outputTokens": 100,
                "totalTokens": 300,
                "model": "gpt-5.3-codex",
                "estimatedCostUsd": 0.05,
            },
        },
    )

    assert intake.returncode == 0
    data = response(intake)["data"]
    assert data["intake"][0]["result"] == "Authored the documentation task plan."
    assert data["execution"]["totals"]["totalTokens"] == 300



def test_cli_lists_and_changes_status(tmp_path: Path) -> None:
    board = tmp_path / "board"
    run_cli(board, "create-request", "--input", "-", input_value=create_input())

    changed = run_cli(board, "change-status", "00001-1", "in-progress")
    listed = run_cli(board, "list", "--status", "in-progress", "--type", "documentation")

    assert changed.returncode == 0
    assert response(changed)["data"]["status"] == "in-progress"
    assert listed.returncode == 0
    assert [item["id"] for item in response(listed)["data"]] == ["00001-1"]


def test_cli_reports_structured_errors_to_stderr(tmp_path: Path) -> None:
    process = run_cli(tmp_path / "board", "get", "00001-1")

    assert process.returncode == 3
    assert process.stdout == ""
    error = json.loads(process.stderr)
    assert error["ok"] is False
    assert error["error"]["code"] == "not_found"


def test_cli_rejects_non_array_creation_input(tmp_path: Path) -> None:
    process = run_cli(
        tmp_path / "board",
        "create-request",
        "--input",
        "-",
        input_value={"type": "documentation"},
    )

    assert process.returncode == 2
    assert process.stdout == ""
    assert json.loads(process.stderr)["error"]["code"] == "validation_error"


def test_concurrent_cli_creations_allocate_unique_request_ids(tmp_path: Path) -> None:
    board = tmp_path / "board"

    with ThreadPoolExecutor(max_workers=4) as executor:
        processes = list(
            executor.map(
                lambda _: run_cli(
                    board, "create-request", "--input", "-", input_value=create_input()
                ),
                range(4),
            )
            )

        assert all(process.returncode == 0 for process in processes), [
            process.stderr for process in processes
        ]
    ids = {json.loads(process.stdout)["data"][0]["id"] for process in processes}
    assert ids == {"00001-1", "00002-1", "00003-1", "00004-1"}


def test_cli_rejects_an_unknown_configured_backend(tmp_path: Path) -> None:
    command = [
        sys.executable,
        ".agents/run.py",
        "work_items",
        "--board-root",
        str(tmp_path / "board"),
        "list",
    ]
    process = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, "SATISFACTORY_WORK_ITEM_BACKEND": "sqlite"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert process.returncode == 2
    assert json.loads(process.stderr)["error"]["code"] == "validation_error"


def test_cli_get_task_and_record_activity(tmp_path: Path) -> None:
    board = tmp_path / "board"
    created = run_cli(
        board,
        "create-request",
        "--input",
        "-",
        input_value=[
            {
                "type": "user-story",
                "request": "Add task APIs",
                "description": "Expose task-level ADLC operations.",
                "acceptanceCriteria": ["A task can be read by id."]
            }
        ],
    )
    assert created.returncode == 0

    add_spec = run_cli(
        board,
        "add_spec",
        "00001-1",
        "--input",
        "-",
        input_value={
            "specification": {
                "summary": "Task API plan",
                "architecturalSummary": "Keep operations storage-independent.",
                "keyDesignDecisions": [],
                "apiContracts": [],
                "databaseSchema": [],
                "uiComponents": [],
                "crossTaskIntegrationPoints": [],
                "openQuestionsAndRisks": []
            },
            "tasks": [
                {
                    "id": "impl-task-commands",
                    "phase": "implementation",
                    "scope": "Implement task commands.",
                    "acceptanceCriteriaCovered": ["00001-1.1"]
                },
                {
                    "id": "unit-test-task-commands",
                    "phase": "unit-test",
                    "scope": "Cover task commands.",
                    "dependencies": ["impl-task-commands"]
                },
                {
                    "id": "review-task-commands",
                    "phase": "review",
                    "scope": "Review task commands.",
                    "dependencies": ["unit-test-task-commands"]
                },
                {
                    "id": "validate-task-commands",
                    "phase": "validation",
                    "scope": "Validate task commands.",
                    "dependencies": ["review-task-commands"]
                }
            ]
        },
    )
    assert add_spec.returncode == 0
    assert response(add_spec)["data"]["planStatus"] == "draft"

    approved = run_cli(board, "approve_plan", "00001-1")
    assert approved.returncode == 0
    assert response(approved)["data"]["planStatus"] == "approved"

    task = run_cli(board, "get_task", "00001-1", "impl-task-commands")
    assert task.returncode == 0
    assert response(task)["data"]["owner"] == "software-engineer"

    activity = run_cli(
        board,
        "record_activity",
        "00001-1",
        "impl-task-commands",
        "--input",
        "-",
        input_value={
            "agent": "software-engineer",
            "technology": "python",
            "outcome": "implemented",
            "result": "Implemented the task commands.",
            "artifact": ".agents/board/00001/tasks/impl-task-commands/changelog.1.md",
            "filesChanged": [".agents/tools/work_items/cli.py"],
            "metrics": {
                "durationSeconds": 12,
                "inputTokens": 100,
                "outputTokens": 40,
                "totalTokens": 140,
                "model": "gpt-5.3-codex",
                "estimatedCostUsd": 0.02
            }
        },
    )
    assert activity.returncode == 0
    data = response(activity)["data"]
    assert data["state"] == "implemented"
    assert data["history"][0]["iteration"] == 1


def test_cli_rejects_a_specification_for_a_bug(tmp_path: Path) -> None:
    board = tmp_path / "board"
    run_cli(
        board,
        "create-request",
        "--input",
        "-",
        input_value=[
            {
                "type": "bug",
                "request": "Fix the failing command",
                "description": "The command fails under valid input.",
                "stepsToReproduce": "Run the command.",
                "expectedResult": "It succeeds.",
                "actualResult": "It fails."
            }
        ],
    )

    process = run_cli(
        board,
        "add_spec",
        "00001-1",
        "--input",
        "-",
        input_value={
            "specification": {
                "summary": "Not allowed",
                "architecturalSummary": "Not allowed"
            },
            "tasks": [
                {"id": "fix-it", "phase": "implementation", "scope": "Fix."},
                {
                    "id": "validate-it",
                    "phase": "validation",
                    "scope": "Validate.",
                    "dependencies": ["fix-it"]
                }
            ]
        },
    )

    assert process.returncode == 2
    assert json.loads(process.stderr)["error"]["code"] == "validation_error"