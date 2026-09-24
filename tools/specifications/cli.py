"""Command-line interface for specification operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NoReturn, TextIO

from .factory import create_service
from .models import SpecificationError

EXIT_CODES = {
    "validation_error": 2,
    "not_found": 3,
    "conflict": 4,
    "storage_error": 5,
    "specification_error": 1,
}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        _write_json(sys.stderr, {"ok": False, "error": {"code": "validation_error", "message": message}})
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="python -m tools.specifications")
    parser.add_argument("--board-root", type=Path, default=Path("board"))
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create")
    create.add_argument("--input", default="-")

    update = commands.add_parser("update")
    update.add_argument("--input", default="-")

    get = commands.add_parser("get")
    get.add_argument("work_item_id")

    approve = commands.add_parser("approve")
    approve.add_argument("work_item_id")

    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        service = create_service(arguments.board_root)
        if arguments.command == "create":
            payload = _read_input(arguments.input)
            if not isinstance(payload, dict):
                from .models import SpecificationValidationError

                raise SpecificationValidationError("Creation input must be a JSON object")
            result: Any = service.create(payload)
        elif arguments.command == "update":
            payload = _read_input(arguments.input)
            if not isinstance(payload, dict):
                from .models import SpecificationValidationError

                raise SpecificationValidationError("Update input must be a JSON object")
            result: Any = service.update(payload)
        elif arguments.command == "get":
            result = service.get(arguments.work_item_id)
        elif arguments.command == "approve":
            result = service.approve(arguments.work_item_id)
        else:
            from .models import SpecificationValidationError
            raise SpecificationValidationError(f"Unknown command: {arguments.command}")
    except SpecificationError as error:
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