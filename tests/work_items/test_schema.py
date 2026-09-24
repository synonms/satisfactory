import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).parents[2]
SCHEMA = json.loads((ROOT / ".agents/schemas/work-item.schema.json").read_text())
VALIDATOR = Draft7Validator(SCHEMA, format_checker=FormatChecker())


def work_item(item_type: str) -> dict:
    item = {
        "id": "00001-1",
        "type": item_type,
        "created": "2026-09-21",
        "status": "new",
        "request": "Manage work items through code",
        "description": "Provide a storage-independent work-item service.",
    }
    if item_type in {"user-story", "chore"}:
        item["acceptanceCriteria"] = [
            {"id": "00001-1.1", "description": "The operation is testable."}
        ]
        item["specification"] = None
    elif item_type == "bug":
        item.update(
            stepsToReproduce="Run the failing operation.",
            expectedResult="The operation succeeds.",
            actualResult="The operation fails.",
        )
    else:
        item["content"] = "Document the supported operations."
    return item


@pytest.mark.parametrize("item_type", ["user-story", "chore", "bug", "documentation"])
def test_schema_accepts_each_work_item_type(item_type: str) -> None:
    VALIDATOR.validate(work_item(item_type))


def test_schema_accepts_blocked_status() -> None:
    item = work_item("bug")
    item["status"] = "blocked"

    VALIDATOR.validate(item)


@pytest.mark.parametrize(
    ("item_type", "field"),
    [
        ("user-story", "acceptanceCriteria"),
        ("chore", "acceptanceCriteria"),
        ("bug", "stepsToReproduce"),
        ("bug", "expectedResult"),
        ("bug", "actualResult"),
        ("documentation", "content"),
    ],
)
def test_schema_rejects_missing_type_specific_fields(item_type: str, field: str) -> None:
    item = work_item(item_type)
    del item[field]

    assert list(VALIDATOR.iter_errors(item))


def test_schema_rejects_fields_from_another_type() -> None:
    item = work_item("bug")
    item["content"] = "Unexpected documentation content."

    assert list(VALIDATOR.iter_errors(item))


def test_schema_rejects_invalid_identifiers_and_unknown_fields() -> None:
    item = work_item("user-story")
    item["id"] = "1-1"
    item["unknown"] = True

    errors = list(VALIDATOR.iter_errors(item))

    assert len(errors) >= 2


def test_schema_rejects_empty_requirement_text() -> None:
    item = work_item("documentation")
    item["content"] = ""

    assert list(VALIDATOR.iter_errors(item))