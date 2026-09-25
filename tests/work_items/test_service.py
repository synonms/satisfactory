from datetime import date
from pathlib import Path

import pytest

from tools.work_items.json_repository import JsonFileWorkItemRepository
from tools.work_items.models import (
    TaskValidationError,
    WorkItemConflictError,
    WorkItemStatus,
    WorkItemValidationError,
)
from tools.work_items.service import WorkItemService


def service(board: Path) -> WorkItemService:
    return WorkItemService(
        JsonFileWorkItemRepository(board),
        today=lambda: date(2026, 9, 21),
    )


def story(request: str = "Add coded work-item management") -> dict:
    return {
        "type": "user-story",
        "request": request,
        "description": "Agents manage work items through stable operations.",
        "acceptanceCriteria": ["An agent can create a request.", "An agent can read an item."],
    }


def bug() -> dict:
    return {
        "type": "bug",
        "request": "Fix failing create-request",
        "description": "The create operation fails under valid input.",
        "stepsToReproduce": "Run create-request with a valid payload.",
        "expectedResult": "The work item is created.",
        "actualResult": "The command fails with a validation error.",
    }


def specification() -> dict:
    return {
        "summary": "Implementation plan",
        "architecturalSummary": "Use the existing service structure.",
        "keyDesignDecisions": [],
        "apiContracts": [],
        "databaseSchema": [],
        "uiComponents": [],
        "testingRequirements": [],
        "crossTaskIntegrationPoints": [],
        "openQuestionsAndRisks": [],
    }


def tasks() -> list[dict]:
    return [
        {
            "id": "python-work-items",
            "owner": "software-engineer",
            "scope": "Implement the specification commands.",
            "acceptanceCriteriaCovered": ["00001-1.1"],
        }
    ]


def test_create_request_assigns_stable_ids_and_persists_json(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")

    created = manager.create_request([story(), {**story(), "type": "chore"}])

    assert [item["id"] for item in created] == ["00001-1", "00001-2"]
    assert created[0]["acceptanceCriteria"][1]["id"] == "00001-1.2"
    assert created[0]["created"] == "2026-09-21"
    assert created[0]["specification"] is None
    assert created[1]["specification"] is None
    assert (tmp_path / "board/00001/00001-1.work-item.json").is_file()
    assert manager.get("00001-2") == created[1]


def test_request_ids_advance_across_service_instances(tmp_path: Path) -> None:
    board = tmp_path / "board"
    assert service(board).create_request([story()])[0]["id"] == "00001-1"
    assert service(board).create_request([story()])[0]["id"] == "00002-1"


def test_list_filters_by_status_type_and_request(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    first = manager.create_request([story(), {**story(), "type": "chore"}])
    manager.create_request(
        [
            {
                "type": "bug",
                "request": "Fix creation",
                "description": "Creation fails.",
                "stepsToReproduce": "Create a request.",
                "expectedResult": "It succeeds.",
                "actualResult": "It fails.",
            }
        ]
    )
    manager.change_status(first[0]["id"], WorkItemStatus.IN_PROGRESS)

    assert [item["id"] for item in manager.list(status=WorkItemStatus.IN_PROGRESS)] == ["00001-1"]
    assert [item["id"] for item in manager.list(request_id="00001")] == ["00001-1", "00001-2"]
    assert [item["id"] for item in manager.list(item_type="bug")] == ["00002-1"]


def test_status_changes_follow_lifecycle_and_are_idempotent(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]

    changed = manager.change_status(work_item_id, WorkItemStatus.IN_PROGRESS)
    repeated = manager.change_status(work_item_id, WorkItemStatus.IN_PROGRESS)
    finished = manager.change_status(work_item_id, WorkItemStatus.DONE)

    assert changed["status"] == "in-progress"
    assert repeated == changed
    assert finished["status"] == "done"
    with pytest.raises(WorkItemConflictError):
        manager.change_status(work_item_id, WorkItemStatus.BLOCKED)


def test_creation_rejects_identity_and_invalid_type_fields(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")

    with pytest.raises(WorkItemValidationError):
        manager.create_request([{**story(), "id": "99999-1"}])
    with pytest.raises(WorkItemValidationError):
        manager.create_request([{**story(), "content": "Wrong field."}])


def test_specification_lifecycle_for_user_story(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]

    created = manager.add_spec(work_item_id, specification(), tasks())
    fetched = manager.get_spec(work_item_id)
    approved = manager.approve_spec(work_item_id)
    task = manager.get_task(work_item_id, "python-work-items")
    updated_task = manager.record_activity(
        work_item_id,
        "python-work-items",
        {
            "agent": "software-engineer",
            "technology": "python",
            "outcome": "implemented",
            "result": "implemented",
            "artifact": "board/00001/chunks/python-work-items/changelog.1.md",
            "filesChanged": ["tools/work_items/service.py"],
            "nextOwner": "quality-assurance-engineer",
            "metrics": {
                "durationSeconds": 10,
                "inputTokens": 10,
                "outputTokens": 5,
                "totalTokens": 15,
                "model": "gpt-5.3-codex",
                "estimatedCostUsd": 0.01,
            },
        },
    )

    assert created["workItemId"] == work_item_id
    assert created["status"] == "draft"
    assert fetched == created
    assert approved["status"] == "approved"
    assert task["state"] == "not-started"
    assert updated_task["state"] == "implemented"
    assert updated_task["implementAttempts"] == 1
    assert updated_task["history"][0]["iteration"] == 1


def test_specification_lifecycle_for_bug(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([bug()])[0]["id"]

    created = manager.add_spec(work_item_id, specification(), tasks())
    fetched = manager.get_spec(work_item_id)
    approved = manager.approve_spec(work_item_id)

    assert created["workItemId"] == work_item_id
    assert fetched == created
    assert approved["status"] == "approved"


def test_add_spec_requires_tasks(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]

    with pytest.raises(TaskValidationError):
        manager.add_spec(work_item_id, specification(), [])