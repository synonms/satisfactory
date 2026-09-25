"""JSON Schema validation for persisted work items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker, RefResolver

from .models import WorkItemValidationError

WORK_ITEM_SCHEMA_PATH = Path(__file__).parents[2] / ".agents/schemas/work-item.schema.json"
SPECIFICATION_SCHEMA_PATH = Path(__file__).parents[2] / ".agents/schemas/specification.schema.json"
TASK_SCHEMA_PATH = Path(__file__).parents[2] / ".agents/schemas/task.schema.json"

class Validator:
    def __init__(self, schema_path: Path) -> None:
        self._schema_path = schema_path
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft7Validator.check_schema(schema)
        except (OSError, json.JSONDecodeError) as error:
            raise WorkItemValidationError(f"Cannot load schema: {error}") from error
        resolver = RefResolver(base_uri=schema_path.resolve().as_uri(), referrer=schema)
        self._validator = Draft7Validator(
            schema,
            resolver=resolver,
            format_checker=FormatChecker(),
        )

    def validate(self, data: dict[str, Any]) -> None:
        errors = sorted(self._validator.iter_errors(data), key=lambda error: list(error.path))
        if not errors:
            return

        details = []
        for error in errors:
            path = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{path}: {error.message}")
        raise WorkItemValidationError("; ".join(details))

class WorkItemValidator(Validator):
    def __init__(self) -> None:
        super().__init__(WORK_ITEM_SCHEMA_PATH)

class SpecificationValidator(Validator):
    def __init__(self) -> None:
        super().__init__(SPECIFICATION_SCHEMA_PATH)


class TaskValidator(Validator):
    def __init__(self) -> None:
        super().__init__(TASK_SCHEMA_PATH)
