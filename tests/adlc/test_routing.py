from datetime import date
from pathlib import Path

import pytest

from tools.adlc import policy, routing
from tools.work_items.json_repository import JsonFileWorkItemRepository
from tools.work_items.service import WorkItemService


def service(board: Path) -> WorkItemService:
    return WorkItemService(
        JsonFileWorkItemRepository(board),
        today=lambda: date(2026, 9, 28),
    )


def metrics() -> dict:
    return {
        "durationSeconds": 1,
        "inputTokens": 1,
        "outputTokens": 1,
        "totalTokens": 2,
        "model": "test-model",
        "estimatedCostUsd": 0.001,
    }


def specification() -> dict:
    return {"summary": "Plan", "architecturalSummary": "Reuse existing structure."}


def tasks() -> list[dict]:
    return [
        {"id": "impl", "phase": "implementation", "scope": "Write the feature."},
        {"id": "unit-test", "phase": "unit-test", "scope": "Test it.", "dependencies": ["impl"]},
        {"id": "review", "phase": "review", "scope": "Review it.", "dependencies": ["unit-test"]},
        {"id": "validate", "phase": "validation", "scope": "Validate it.", "dependencies": ["review"]},
    ]


@pytest.fixture
def approved_work_item(tmp_path: Path) -> tuple[WorkItemService, str]:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request(
        [
            {
                "type": "user-story",
                "request": "Add a feature",
                "description": "A feature is added.",
                "acceptanceCriteria": ["The feature works."],
            }
        ]
    )[0]["id"]
    manager.add_spec(work_item_id, specification(), tasks())
    manager.approve_plan(work_item_id)
    return manager, work_item_id


def record(manager: WorkItemService, work_item_id: str, task_id: str, agent: str, outcome: str, **extra) -> None:
    manager.record_activity(
        work_item_id,
        task_id,
        {"agent": agent, "outcome": outcome, "result": outcome, "metrics": metrics(), **extra},
    )


def test_next_task_follows_dependency_order(approved_work_item) -> None:
    manager, work_item_id = approved_work_item

    assert routing.next_task(manager.get(work_item_id)).task_id == "impl"

    record(manager, work_item_id, "impl", "software-engineer", "implemented")
    assert routing.next_task(manager.get(work_item_id)).task_id == "unit-test"

    record(manager, work_item_id, "unit-test", "quality-assurance-engineer", "passed")
    assert routing.next_task(manager.get(work_item_id)).task_id == "review"

    record(manager, work_item_id, "review", "reviewer", "approved")
    assert routing.next_task(manager.get(work_item_id)).task_id == "validate"

    record(manager, work_item_id, "validate", "implementation-validator", "validated")
    work_item = manager.get(work_item_id)
    assert routing.next_task(work_item) is None
    assert routing.is_complete(work_item)


def test_a_draft_plan_is_never_dispatched(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request(
        [
            {
                "type": "user-story",
                "request": "Add a feature",
                "description": "A feature is added.",
                "acceptanceCriteria": ["The feature works."],
            }
        ]
    )[0]["id"]
    manager.add_spec(work_item_id, specification(), tasks())

    assert routing.next_task(manager.get(work_item_id)) is None


def test_failed_tests_route_back_to_the_same_task(approved_work_item) -> None:
    manager, work_item_id = approved_work_item
    record(manager, work_item_id, "impl", "software-engineer", "implemented")
    record(
        manager,
        work_item_id,
        "unit-test",
        "quality-assurance-engineer",
        "failed",
        failureSignature="abc",
    )

    assert routing.next_task(manager.get(work_item_id)).task_id == "unit-test"


def test_rejected_validation_reopens_the_implementation_chain(approved_work_item) -> None:
    manager, work_item_id = approved_work_item
    record(manager, work_item_id, "impl", "software-engineer", "implemented")
    record(manager, work_item_id, "unit-test", "quality-assurance-engineer", "passed")
    record(manager, work_item_id, "review", "reviewer", "approved")
    record(
        manager,
        work_item_id,
        "validate",
        "implementation-validator",
        "rejected",
        remediationTargetTaskId="impl",
    )

    work_item = manager.get(work_item_id)
    states = {task["id"]: task["state"] for task in work_item["tasks"]}
    assert states["impl"] == "rework-required"
    assert states["unit-test"] == "not-started"
    assert states["review"] == "not-started"
    assert work_item["execution"]["budget"]["validationLoops"] == 1
    assert routing.next_task(work_item).task_id == "impl"


def test_no_progress_detection_trips_on_a_repeated_signature(approved_work_item) -> None:
    manager, work_item_id = approved_work_item
    record(manager, work_item_id, "impl", "software-engineer", "implemented")
    for _ in range(2):
        record(
            manager,
            work_item_id,
            "unit-test",
            "quality-assurance-engineer",
            "failed",
            failureSignature="same-failure",
        )

    work_item = manager.get(work_item_id)
    task = next(task for task in work_item["tasks"] if task["id"] == "unit-test")
    codes = {violation.code for violation in policy.check_failsafes(work_item, task)}
    assert "no-progress" in codes


def test_attempt_cap_trips(approved_work_item) -> None:
    manager, work_item_id = approved_work_item
    for index in range(3):
        record(
            manager,
            work_item_id,
            "impl",
            "software-engineer",
            "implemented",
            artifact=f"changelog.{index}.md",
        )

    work_item = manager.get(work_item_id)
    task = next(task for task in work_item["tasks"] if task["id"] == "impl")
    codes = {violation.code for violation in policy.check_failsafes(work_item, task)}
    assert "task-attempts-exhausted" in codes


def test_run_budget_trips(approved_work_item) -> None:
    manager, work_item_id = approved_work_item
    work_item = manager.get(work_item_id)
    work_item["execution"]["budget"]["totalAgentRuns"] = 40

    codes = {violation.code for violation in policy.check_failsafes(work_item)}
    assert "run-budget-exhausted" in codes


@pytest.mark.parametrize(
    ("agent", "files", "allowed"),
    [
        ("software-engineer", ["src/Api/Endpoint.cs"], True),
        ("software-engineer", ["tests/api/test_endpoint.py"], False),
        ("quality-assurance-engineer", ["tests/api/test_endpoint.py"], True),
        ("quality-assurance-engineer", ["src/Api/Endpoint.cs"], False),
        ("reviewer", [], True),
        ("reviewer", ["src/Api/Endpoint.cs"], False),
        ("implementation-validator", ["tests/api/test_endpoint.py"], False),
    ],
)
def test_ownership_guard(agent: str, files: list[str], allowed: bool) -> None:
    assert (policy.check_ownership(agent, files) == []) is allowed
