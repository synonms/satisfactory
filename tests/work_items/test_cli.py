import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).parents[2]


def run_cli(board: Path, *arguments: str, input_value: object | None = None) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        "-m",
        "tools.work_items",
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
        "-m",
        "tools.work_items",
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