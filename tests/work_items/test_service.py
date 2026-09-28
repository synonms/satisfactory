from datetime import date
from pathlib import Path

import pytest

from tools.work_items.json_repository import JsonFileWorkItemRepository
from tools.work_items.models import (
    PlanConflictError,
    SpecificationValidationError,
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
        "crossTaskIntegrationPoints": [],
        "openQuestionsAndRisks": [],
    }


def metrics() -> dict:
    return {
        "durationSeconds": 10,
        "inputTokens": 10,
        "outputTokens": 5,
        "totalTokens": 15,
        "model": "gpt-5.3-codex",
        "estimatedCostUsd": 0.01,
    }


def tasks() -> list[dict]:
    return [
        {
            "id": "impl-work-items",
            "phase": "implementation",
            "scope": "Implement the plan commands.",
            "technology": "python",
            "acceptanceCriteriaCovered": ["00001-1.1"],
        },
        {
            "id": "unit-test-work-items",
            "phase": "unit-test",
            "scope": "Cover the plan commands.",
            "dependencies": ["impl-work-items"],
            "acceptanceCriteriaCovered": ["00001-1.2"],
        },
        {
            "id": "review-work-items",
            "phase": "review",
            "scope": "Review the delivered change.",
            "dependencies": ["unit-test-work-items"],
        },
        {
            "id": "validate-work-items",
            "phase": "validation",
            "scope": "Validate against the specification.",
            "dependencies": ["review-work-items"],
        },
    ]


def bug_tasks() -> list[dict]:
    return [
        {
            "id": "repro-failure",
            "phase": "bug-repro",
            "scope": "Write a failing reproduction test.",
        },
        {
            "id": "fix-failure",
            "phase": "implementation",
            "scope": "Fix the defect.",
            "dependencies": ["repro-failure"],
        },
        {
            "id": "validate-failure",
            "phase": "validation",
            "scope": "Validate the fix.",
            "dependencies": ["fix-failure"],
        },
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
    fetched = manager.get_plan(work_item_id)
    approved = manager.approve_plan(work_item_id)
    task = manager.get_task(work_item_id, "impl-work-items")
    updated_task = manager.record_activity(
        work_item_id,
        "impl-work-items",
        {
            "agent": "software-engineer",
            "technology": "python",
            "outcome": "implemented",
            "result": "implemented",
            "artifact": "board/00001/tasks/impl-work-items/changelog.1.md",
            "filesChanged": ["tools/work_items/service.py"],
            "metrics": metrics(),
        },
    )

    assert created["planStatus"] == "draft"
    assert created["specification"]["status"] == "draft"
    assert fetched == created
    assert approved["planStatus"] == "approved"
    assert approved["specification"]["status"] == "approved"
    assert task["state"] == "not-started"
    assert task["owner"] == "software-engineer"
    assert updated_task["state"] == "implemented"
    assert updated_task["attempts"] == 1
    assert updated_task["history"][0]["iteration"] == 1
    assert manager.get(work_item_id)["execution"]["totals"]["totalTokens"] == 15


def test_bug_plan_has_no_specification(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([bug()])[0]["id"]

    created = manager.add_tasks(work_item_id, bug_tasks())
    approved = manager.approve_plan(work_item_id)

    assert created["specification"] is None
    assert approved["planStatus"] == "approved"
    assert manager.get(work_item_id)["specification"] is None


def test_specification_is_rejected_for_bug_and_documentation(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([bug()])[0]["id"]

    with pytest.raises(SpecificationValidationError):
        manager.add_spec(work_item_id, specification(), bug_tasks())


def test_user_story_plan_requires_a_specification(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]

    with pytest.raises(SpecificationValidationError):
        manager.add_tasks(work_item_id, tasks())


def test_review_tasks_are_rejected_for_bugs(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([bug()])[0]["id"]
    plan = bug_tasks() + [
        {"id": "review-fix", "phase": "review", "scope": "Review.", "dependencies": ["fix-failure"]}
    ]

    with pytest.raises(TaskValidationError):
        manager.add_tasks(work_item_id, plan)


def test_implementation_task_requires_a_downstream_review(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = [task for task in tasks() if task["phase"] != "review"]
    plan[-1]["dependencies"] = ["unit-test-work-items"]

    with pytest.raises(TaskValidationError):
        manager.add_spec(work_item_id, specification(), plan)


def test_plan_requires_a_validation_task(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = [task for task in tasks() if task["phase"] != "validation"]

    with pytest.raises(TaskValidationError):
        manager.add_spec(work_item_id, specification(), plan)


def test_task_owner_must_match_the_phase(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = tasks()
    plan[0]["owner"] = "reviewer"

    with pytest.raises(TaskValidationError):
        manager.add_spec(work_item_id, specification(), plan)


def test_dependency_cycles_are_rejected(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = tasks()
    plan[0]["dependencies"] = ["validate-work-items"]

    with pytest.raises(TaskValidationError):
        manager.add_spec(work_item_id, specification(), plan)


def test_outcome_must_be_legal_for_the_task_phase(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    manager.add_spec(work_item_id, specification(), tasks())
    manager.approve_plan(work_item_id)

    with pytest.raises(TaskValidationError):
        manager.record_activity(
            work_item_id,
            "impl-work-items",
            {
                "agent": "software-engineer",
                "outcome": "approved",
                "result": "wrong outcome for phase",
                "metrics": metrics(),
            },
        )


def test_activity_requires_an_approved_plan(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    manager.add_spec(work_item_id, specification(), tasks())

    with pytest.raises(PlanConflictError):
        manager.record_activity(
            work_item_id,
            "impl-work-items",
            {
                "agent": "software-engineer",
                "outcome": "implemented",
                "result": "too early",
                "metrics": metrics(),
            },
        )


def test_changes_requested_sends_the_target_task_back_for_rework(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    manager.add_spec(work_item_id, specification(), tasks())
    manager.approve_plan(work_item_id)

    for task_id, agent, outcome in (
        ("impl-work-items", "software-engineer", "implemented"),
        ("unit-test-work-items", "quality-assurance-engineer", "passed"),
    ):
        manager.record_activity(
            work_item_id,
            task_id,
            {"agent": agent, "outcome": outcome, "result": outcome, "metrics": metrics()},
        )

    manager.record_activity(
        work_item_id,
        "review-work-items",
        {
            "agent": "reviewer",
            "outcome": "changes-requested",
            "result": "Missing null guard.",
            "remediationTargetTaskId": "impl-work-items",
            "metrics": metrics(),
        },
    )

    work_item = manager.get(work_item_id)
    states = {task["id"]: task["state"] for task in work_item["tasks"]}
    assert states["impl-work-items"] == "rework-required"
    assert states["unit-test-work-items"] == "not-started"
    assert states["review-work-items"] == "changes-requested"
    assert work_item["execution"]["budget"]["reviewLoops"] == 1


def test_add_spec_requires_tasks(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]

    with pytest.raises(TaskValidationError):
        manager.add_spec(work_item_id, specification(), [])