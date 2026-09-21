import json
from pathlib import Path

import pytest

from tools.work_items.json_repository import JsonFileWorkItemRepository
from tools.work_items.models import (
    WorkItemConflictError,
    WorkItemStorageError,
    WorkItemValidationError,
)
from tools.work_items.service import WorkItemService


def documentation_item() -> dict:
    return {
        "type": "documentation",
        "request": "Document work-item operations",
        "description": "Keep agent instructions concise.",
        "content": "Describe each supported operation.",
    }


def test_allocation_recovers_from_existing_request_directories(tmp_path: Path) -> None:
    board = tmp_path / "board"
    (board / "00007").mkdir(parents=True)
    (board / ".id").write_text("3\n", encoding="utf-8")

    created = WorkItemService(JsonFileWorkItemRepository(board)).create_request(
        [documentation_item()]
    )

    assert created[0]["id"] == "00008-1"
    assert (board / ".id").read_text(encoding="utf-8") == "00008\n"


def test_get_rejects_corrupt_json(tmp_path: Path) -> None:
    path = tmp_path / "board/00001/00001-1.work-item.json"
    path.parent.mkdir(parents=True)
    path.write_text("{", encoding="utf-8")

    with pytest.raises(WorkItemStorageError):
        JsonFileWorkItemRepository(tmp_path / "board").get("00001-1")


def test_get_validates_persisted_records(tmp_path: Path) -> None:
    path = tmp_path / "board/00001/00001-1.work-item.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"id": "00001-1"}), encoding="utf-8")

    with pytest.raises(WorkItemValidationError):
        JsonFileWorkItemRepository(tmp_path / "board").get("00001-1")


def test_invalid_id_is_rejected_before_storage_access(tmp_path: Path) -> None:
    with pytest.raises(WorkItemValidationError):
        JsonFileWorkItemRepository(tmp_path / "board").get("../record")


def test_status_update_rejects_a_stale_expected_status(tmp_path: Path) -> None:
    repository = JsonFileWorkItemRepository(tmp_path / "board")
    work_item_id = WorkItemService(repository).create_request([documentation_item()])[0]["id"]
    repository.update_status(work_item_id, "new", "in-progress")

    with pytest.raises(WorkItemConflictError):
        repository.update_status(work_item_id, "new", "blocked")