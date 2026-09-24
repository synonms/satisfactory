"""JSON Schema validation for persisted specifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

from .models import SpecificationValidationError

DEFAULT_SCHEMA_PATH = Path(__file__).parents[2] / ".agents/schemas/specification.schema.json"


class SpecificationValidator:
    def __init__(self, schema_path: Path = DEFAULT_SCHEMA_PATH) -> None:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft7Validator.check_schema(schema)
        except (OSError, json.JSONDecodeError) as error:
            raise SpecificationValidationError(f"Cannot load specification schema: {error}") from error
        self._validator = Draft7Validator(schema, format_checker=FormatChecker())

    def validate(self, work_item: dict[str, Any]) -> None:
        errors = sorted(self._validator.iter_errors(work_item), key=lambda error: list(error.path))
        if not errors:
            return

        details = []
        for error in errors:
            path = ".".join(str(part) for part in error.absolute_path) or "$"
            details.append(f"{path}: {error.message}")
        raise SpecificationValidationError("; ".join(details))