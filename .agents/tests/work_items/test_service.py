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
from tools.work_items.plan_lint import lint_plan
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


def test_intake_activity_is_recorded_and_rolled_into_totals(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    created = manager.create_request([story()])[0]
    assert created["intake"] == []

    manager.record_intake(
        created["id"],
        {"agent": "triage", "result": "Triaged the request.", "metrics": metrics()},
    )
    updated = manager.record_intake(
        created["id"],
        {"agent": "software-architect", "result": "Authored the plan.", "metrics": metrics()},
    )

    assert [entry["agent"] for entry in updated["intake"]] == ["triage", "software-architect"]
    assert updated["execution"]["totals"]["totalTokens"] == 30
    assert updated["execution"]["totals"]["estimatedCostUsd"] == 0.02
    assert updated["execution"]["budget"]["totalAgentRuns"] == 0


def test_intake_activity_requires_a_known_agent_result_and_metrics(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]

    with pytest.raises(TaskValidationError):
        manager.record_intake(work_item_id, {"agent": "orchestrator", "result": "Triaged.", "metrics": metrics()})
    with pytest.raises(TaskValidationError):
        manager.record_intake(work_item_id, {"result": "Triaged.", "metrics": metrics()})
    with pytest.raises(TaskValidationError):
        manager.record_intake(work_item_id, {"agent": "triage", "result": "Triaged."})
    with pytest.raises(TaskValidationError):
        manager.record_intake(work_item_id, {"agent": "triage", "metrics": metrics()})


@pytest.mark.parametrize(
    "override",
    [
        {"durationSeconds": 0, "inputTokens": 0, "outputTokens": 0, "totalTokens": 0, "model": "unknown", "estimatedCostUsd": 0},
        {"inputTokens": 0, "totalTokens": 5},
        {"durationSeconds": 0},
        {"totalTokens": 99},
        {"model": "unknown"},
        {"model": ""},
        {"estimatedCostUsd": -1},
        {"inputTokens": True, "totalTokens": 6},
        {"extra": 1},
    ],
)
def test_placeholder_or_invalid_metrics_are_rejected(tmp_path: Path, override: dict) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    manager.add_spec(work_item_id, specification(), tasks())
    manager.approve_plan(work_item_id)
    invalid = {**metrics(), **override}

    with pytest.raises(TaskValidationError):
        manager.record_activity(
            work_item_id,
            "impl-work-items",
            {"agent": "software-engineer", "outcome": "implemented", "metrics": invalid},
        )
    with pytest.raises(TaskValidationError):
        manager.record_intake(work_item_id, {"agent": "triage", "result": "Triaged.", "metrics": invalid})
    assert manager.get_task(work_item_id, "impl-work-items")["history"] == []


def test_metrics_missing_a_field_are_rejected(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    incomplete = {key: value for key, value in metrics().items() if key != "model"}

    with pytest.raises(TaskValidationError):
        manager.record_intake(work_item_id, {"agent": "triage", "result": "Triaged.", "metrics": incomplete})


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
            "artifact": ".agents/board/00001/tasks/impl-work-items/changelog.1.md",
            "filesChanged": [".agents/tools/work_items/service.py"],
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


def test_multiple_implementations_can_share_test_and_review_tasks(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = [
        {
            "id": "impl-contract",
            "phase": "implementation",
            "scope": "Update the shared contract.",
            "acceptanceCriteriaCovered": ["00001-1.1"],
        },
        {
            "id": "impl-ui",
            "phase": "implementation",
            "scope": "Display the shared contract in the UI.",
            "acceptanceCriteriaCovered": ["00001-1.2"],
        },
        {
            "id": "test-feature",
            "phase": "integration-test",
            "scope": "Verify the feature across its contract and UI boundary.",
            "dependencies": ["impl-contract", "impl-ui"],
            "acceptanceCriteriaCovered": ["00001-1.1", "00001-1.2"],
        },
        {
            "id": "review-feature",
            "phase": "review",
            "scope": "Review the complete feature and its tests.",
            "dependencies": ["test-feature"],
        },
        {
            "id": "validate-feature",
            "phase": "validation",
            "scope": "Validate the complete feature against its requirements.",
            "dependencies": ["review-feature"],
            "acceptanceCriteriaCovered": ["00001-1.1", "00001-1.2"],
        },
    ]

    created = manager.add_spec(work_item_id, specification(), plan)

    assert [task["id"] for task in created["tasks"]] == [task["id"] for task in plan]


def test_plan_policy_is_persisted_and_validated(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    first_id = manager.create_request([story()])[0]["id"]
    context = {
        "technology": "dotnet",
        "scopePaths": ["src/Api"],
        "facts": [{"name": "sdkVersion", "value": "10.0.100", "source": "global.json"}],
        "projects": [
            {
                "path": "src/Api/Api.csproj",
                "name": "Api",
                "kind": "application",
                "targetFrameworks": ["net10.0"],
                "testFrameworks": [],
                "references": [],
                "source": "src/Api/Api.csproj",
            }
        ],
        "resources": [".agents/resources/developer-commands.md"],
    }

    plan = manager.add_spec(
        first_id,
        specification(),
        tasks(),
        {"risk": "low", "mode": "lean"},
        context,
    )

    assert plan["planPolicy"] == {"risk": "low", "mode": "lean"}
    assert plan["repositoryContext"] == context
    assert manager.get(first_id)["planPolicy"] == {"risk": "low", "mode": "lean"}
    assert manager.get(first_id)["repositoryContext"] == context

    second_id = manager.create_request([story()])[0]["id"]
    invalid_tasks = tasks()
    for task in invalid_tasks:
        task["acceptanceCriteriaCovered"] = [
            criterion.replace(first_id, second_id)
            for criterion in task.get("acceptanceCriteriaCovered", [])
        ]
    with pytest.raises(TaskValidationError, match="Plan policy mode"):
        manager.add_spec(
            second_id,
            specification(),
            invalid_tasks,
            {"risk": "low", "mode": "fast"},
        )


def test_plan_lint_warns_about_fragmented_handoffs(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = tasks()
    plan.append(
        {
            "id": "review-second",
            "phase": "review",
            "scope": "Review another implementation slice.",
            "dependencies": ["unit-test-work-items"],
        }
    )

    report = lint_plan(
        manager.get(work_item_id),
        {"planPolicy": {"risk": "low", "mode": "lean"}, "tasks": plan},
    )

    assert report["estimatedAgentRuns"] == 5
    assert {warning["code"] for warning in report["warnings"]} == {
        "lean-handoff-budget",
        "fragmented-review",
    }


def test_plan_lint_warns_when_review_can_run_before_qa(tmp_path: Path) -> None:
    manager = service(tmp_path / "board")
    work_item_id = manager.create_request([story()])[0]["id"]
    plan = tasks()
    plan[2]["dependencies"] = ["impl-work-items"]

    report = lint_plan(
        manager.get(work_item_id),
        {"planPolicy": {"risk": "low", "mode": "lean"}, "tasks": plan},
    )

    assert "review-before-tests" in {warning["code"] for warning in report["warnings"]}


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