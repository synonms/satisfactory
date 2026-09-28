"""Command-line interface for deterministic ADLC routing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NoReturn, TextIO

from tools.work_items.factory import create_service
from tools.work_items.models import PlanStatus, TaskState, WorkItemError, WorkItemStatus

from . import policy, routing

EXIT_CODES = {
    "validation_error": 2,
    "not_found": 3,
    "conflict": 4,
    "storage_error": 5,
    "work_item_error": 1,
}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        _write_json(sys.stderr, {"ok": False, "error": {"code": "validation_error", "message": message}})
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="python -m tools.adlc")
    parser.add_argument("--board-root", type=Path, default=Path("board"))
    commands = parser.add_subparsers(dest="command", required=True)

    next_command = commands.add_parser("next")
    next_command.add_argument("work_item_id")

    status = commands.add_parser("status")
    status.add_argument("work_item_id")

    guard = commands.add_parser("guard")
    guard.add_argument("agent")
    guard.add_argument("files", nargs="*")

    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.command == "guard":
            violations = policy.check_ownership(arguments.agent, list(arguments.files))
            result: Any = {
                "agent": arguments.agent,
                "allowed": not violations,
                "violations": [violation.to_dict() for violation in violations],
            }
        else:
            service = create_service(arguments.board_root)
            work_item = service.get(arguments.work_item_id)
            result = _next(work_item) if arguments.command == "next" else _status(work_item)
    except WorkItemError as error:
        _write_json(sys.stderr, {"ok": False, "error": {"code": error.code, "message": str(error)}})
        return EXIT_CODES.get(error.code, 1)

    _write_json(sys.stdout, {"ok": True, "data": result})
    return 0


def _next(work_item: dict[str, Any]) -> dict[str, Any]:
    if work_item["status"] in {WorkItemStatus.DONE.value, WorkItemStatus.BLOCKED.value}:
        return {"action": "stop", "reason": f"Work item is {work_item['status']}"}

    if work_item.get("planStatus") != PlanStatus.APPROVED.value:
        return {
            "action": "await-approval",
            "reason": "The task plan is not approved. A human must approve it before dispatch.",
            "planStatus": work_item.get("planStatus"),
        }

    violations = policy.check_failsafes(work_item)
    if violations:
        return _blocked(violations)

    dispatch = routing.next_task(work_item)
    if dispatch is None:
        if routing.is_complete(work_item):
            return {"action": "ready-for-user", "reason": "Every task reached a success state."}
        blocked = routing.blocked_tasks(work_item)
        if blocked:
            return {
                "action": "block",
                "reason": "Blocked tasks require human intervention.",
                "tasks": [task["id"] for task in blocked],
            }
        return {"action": "stop", "reason": "No task is dispatchable."}

    task = next(task for task in work_item["tasks"] if task["id"] == dispatch.task_id)
    task_violations = policy.check_failsafes(work_item, task)
    if task_violations:
        return _blocked(task_violations)

    return {
        "action": "dispatch",
        "dispatch": dispatch.to_dict(),
        "recommendedWorkItemStatus": WorkItemStatus.IN_PROGRESS.value,
    }


def _status(work_item: dict[str, Any]) -> dict[str, Any]:
    tasks = work_item.get("tasks", [])
    return {
        "workItemId": work_item["id"],
        "type": work_item["type"],
        "status": work_item["status"],
        "planStatus": work_item.get("planStatus"),
        "execution": work_item.get("execution"),
        "tasks": [
            {
                "id": task["id"],
                "phase": task["phase"],
                "owner": task["owner"],
                "state": task["state"],
                "attempts": task["attempts"],
                "iterations": len(task.get("history", [])),
            }
            for task in tasks
        ],
        "complete": routing.is_complete(work_item),
        "blocked": [task["id"] for task in tasks if task["state"] == TaskState.BLOCKED.value],
    }


def _blocked(violations: list[policy.FailsafeViolation]) -> dict[str, Any]:
    return {
        "action": "block",
        "reason": "One or more failsafes tripped.",
        "violations": [violation.to_dict() for violation in violations],
        "recommendedWorkItemStatus": WorkItemStatus.BLOCKED.value,
    }


def _write_json(stream: TextIO, value: object) -> None:
    json.dump(value, stream, separators=(",", ":"), ensure_ascii=True)
    stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
