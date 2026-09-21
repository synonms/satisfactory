"""Command-line interface for work-item operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NoReturn, TextIO

from .factory import create_service
from .models import WorkItemError, WorkItemStatus, WorkItemType

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
    parser = JsonArgumentParser(prog="python -m tools.work_items")
    parser.add_argument("--board-root", type=Path, default=Path("board"))
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create-request")
    create.add_argument("--input", default="-")

    get = commands.add_parser("get")
    get.add_argument("work_item_id")

    list_command = commands.add_parser("list")
    list_command.add_argument("--status", choices=[status.value for status in WorkItemStatus])
    list_command.add_argument("--type", dest="item_type", choices=[item.value for item in WorkItemType])
    list_command.add_argument("--request-id")

    change_status = commands.add_parser("change-status")
    change_status.add_argument("work_item_id")
    change_status.add_argument("status", choices=[status.value for status in WorkItemStatus])
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        service = create_service(arguments.board_root)
        if arguments.command == "create-request":
            payload = _read_input(arguments.input)
            if not isinstance(payload, list):
                from .models import WorkItemValidationError

                raise WorkItemValidationError("Creation input must be a JSON array")
            result: Any = service.create_request(payload)
        elif arguments.command == "get":
            result = service.get(arguments.work_item_id)
        elif arguments.command == "list":
            result = service.list(
                status=WorkItemStatus(arguments.status) if arguments.status else None,
                item_type=WorkItemType(arguments.item_type) if arguments.item_type else None,
                request_id=arguments.request_id,
            )
        else:
            result = service.change_status(
                arguments.work_item_id, WorkItemStatus(arguments.status)
            )
    except WorkItemError as error:
        _write_json(
            sys.stderr,
            {"ok": False, "error": {"code": error.code, "message": str(error)}},
        )
        return EXIT_CODES.get(error.code, 1)
    except (OSError, json.JSONDecodeError) as error:
        _write_json(
            sys.stderr,
            {"ok": False, "error": {"code": "validation_error", "message": str(error)}},
        )
        return 2

    _write_json(sys.stdout, {"ok": True, "data": result})
    return 0


def _read_input(input_path: str) -> Any:
    if input_path == "-":
        return json.load(sys.stdin)
    with Path(input_path).open(encoding="utf-8") as input_file:
        return json.load(input_file)


def _write_json(stream: TextIO, value: object) -> None:
    json.dump(value, stream, separators=(",", ":"), ensure_ascii=True)
    stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())