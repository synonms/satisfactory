"""Storage-independent work-item behavior."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import date
from datetime import datetime, timezone
from typing import Any

from .models import (
    WorkItem,
    WorkItemConflictError,
    WorkItemStatus,
    WorkItemType,
    WorkItemValidationError,
    Specification,
    SpecificationConflictError,
    SpecificationStatus,
    SpecificationValidationError,
    Task,
    TaskActivity,
    TaskOutcome,
    TaskState,
    TaskValidationError,
)
from .repository import WorkItemRepository
from .validation import WorkItemValidator, SpecificationValidator, TaskValidator

WORK_ITEM_COMMON_INPUT_FIELDS = {"type", "request", "description", "source"}
WORK_ITEM_TYPE_INPUT_FIELDS = {
    WorkItemType.USER_STORY: {"acceptanceCriteria"},
    WorkItemType.CHORE: {"acceptanceCriteria"},
    WorkItemType.BUG: {"stepsToReproduce", "expectedResult", "actualResult"},
    WorkItemType.DOCUMENTATION: {"content"},
}
WORK_ITEM_TRANSITIONS = {
    WorkItemStatus.NEW: {WorkItemStatus.IN_PROGRESS},
    WorkItemStatus.IN_PROGRESS: {WorkItemStatus.DONE, WorkItemStatus.BLOCKED},
    WorkItemStatus.DONE: set(),
    WorkItemStatus.BLOCKED: set(),
}
SPECIFICATION_COMMON_INPUT_FIELDS = {
    "summary",
    "architecturalSummary",
    "keyDesignDecisions",
    "apiContracts",
    "databaseSchema",
    "uiComponents",
    "testingRequirements",
    "crossTaskIntegrationPoints",
    "openQuestionsAndRisks",
}
TASK_COMMON_INPUT_FIELDS = {
    "id",
    "owner",
    "scope",
    "affectedPaths",
    "contracts",
    "dependencies",
    "acceptanceCriteriaCovered",
    "state",
    "implementAttempts",
    "testAttempts",
    "lastFailureSignature",
    "latestArtifact",
    "history",
}
ACTIVITY_COMMON_INPUT_FIELDS = {
    "agent",
    "technology",
    "outcome",
    "result",
    "artifact",
    "filesChanged",
    "nextOwner",
    "metrics",
}
SPECIFICATION_TRANSITIONS = {
    SpecificationStatus.DRAFT: {SpecificationStatus.APPROVED},
    SpecificationStatus.APPROVED: set()
}

class WorkItemService:
    def __init__(
        self,
        repository: WorkItemRepository,
        work_item_validator: WorkItemValidator | None = None,
        specification_validator: SpecificationValidator | None = None,
        task_validator: TaskValidator | None = None,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._repository = repository
        self._work_item_validator = work_item_validator or WorkItemValidator()
        self._specification_validator = specification_validator or SpecificationValidator()
        self._task_validator = task_validator or TaskValidator()
        self._today = today


    def create(self, inputs: Sequence[Mapping[str, Any]]) -> list[WorkItem]:
        if not inputs:
            raise WorkItemValidationError("A request must contain at least one work item")
        normalized = [deepcopy(dict(item)) for item in inputs]

        def build(request_id: str) -> list[WorkItem]:
            return [
                self._build_work_item(request_id, sequence, item)
                for sequence, item in enumerate(normalized, start=1)
            ]

        return self._repository.create(build)


    def create_request(self, inputs: Sequence[Mapping[str, Any]]) -> list[WorkItem]:
        return self.create(inputs)


    def get(self, work_item_id: str) -> WorkItem:
        return self._repository.get(work_item_id)


    def list(
        self,
        *,
        status: WorkItemStatus | None = None,
        item_type: WorkItemType | None = None,
        request_id: str | None = None,
    ) -> list[WorkItem]:
        records = self._repository.list()
        if status is not None:
            records = [record for record in records if record["status"] == status]
        if item_type is not None:
            records = [record for record in records if record["type"] == item_type]
        if request_id is not None:
            if len(request_id) != 5 or not request_id.isdigit():
                raise WorkItemValidationError(f"Invalid request ID: {request_id}")
            records = [record for record in records if record["id"].startswith(request_id + "-")]
        return records


    def update_status(self, work_item_id: str, new_status: WorkItemStatus) -> WorkItem:
        current = self.get(work_item_id)
        current_status = WorkItemStatus(current["status"])
        if current_status == new_status:
            return current
        if new_status not in WORK_ITEM_TRANSITIONS[current_status]:
            raise WorkItemConflictError(
                f"Cannot transition {work_item_id} from {current_status.value} "
                f"to {new_status.value}"
            )
        return self._repository.update_status(work_item_id, current_status.value, new_status.value)


    def change_status(self, work_item_id: str, new_status: WorkItemStatus) -> WorkItem:
        return self.update_status(work_item_id, new_status)


    def add_spec(self, work_item_id: str, input: Mapping[str, Any], tasks_input: Sequence[Mapping[str, Any]]) -> Specification:
        if not input:
            raise SpecificationValidationError("'add_spec' request must contain a specification")
        if not tasks_input:
            raise TaskValidationError("'add_spec' request must contain at least one task")
        normalized = deepcopy(dict(input))  # type: ignore
        normalized_tasks = [deepcopy(dict(task)) for task in tasks_input]

        work_item = self.get(work_item_id)
        if work_item["type"] not in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            raise SpecificationValidationError(
                f"Specifications are only supported for user-story and chore work items: {work_item_id}"
            )

        specification = self._build_specification(work_item_id, normalized)
        tasks = self._build_tasks(work_item, normalized_tasks)

        return self._repository.add_spec(work_item_id, specification, tasks)


    def revise_spec(self, work_item_id: str, input: Mapping[str, Any], tasks_input: Sequence[Mapping[str, Any]]) -> Specification:
        if not input:
            raise SpecificationValidationError("'revise_spec' request must contain a specification")
        if not tasks_input:
            raise TaskValidationError("'revise_spec' request must contain at least one task")
        normalized = deepcopy(dict(input))  # type: ignore
        normalized_tasks = [deepcopy(dict(task)) for task in tasks_input]

        work_item = self.get(work_item_id)
        if work_item["type"] not in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            raise SpecificationValidationError(
                f"Specifications are only supported for user-story and chore work items: {work_item_id}"
            )

        specification = self._build_specification(work_item_id, normalized)
        tasks = self._build_tasks(work_item, normalized_tasks)

        return self._repository.revise_spec(work_item_id, specification, tasks)


    def get_spec(self, work_item_id: str) -> Specification:
        work_item = self.get(work_item_id)
        if work_item["type"] not in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            raise SpecificationValidationError(
                f"Specifications are only supported for user-story and chore work items: {work_item_id}"
            )
        return self._repository.get_spec(work_item_id)


    def approve_spec(self, work_item_id: str) -> Specification:
        work_item = self.get(work_item_id)
        if work_item["type"] not in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            raise SpecificationValidationError(
                f"Specifications are only supported for user-story and chore work items: {work_item_id}"
            )

        specification = self.get_spec(work_item_id)
        current_status = SpecificationStatus(specification["status"])
        if current_status == SpecificationStatus.APPROVED:
            return specification
        if SpecificationStatus.APPROVED not in SPECIFICATION_TRANSITIONS[current_status]:
            raise SpecificationConflictError(
                f"Cannot transition specification for work item {work_item_id} "
                f"from {current_status.value} to {SpecificationStatus.APPROVED.value}"
            )
        return self._repository.approve_spec(work_item_id)


    def get_task(self, work_item_id: str, task_id: str) -> Task:
        if not task_id:
            raise TaskValidationError("task_id must be a non-empty string")
        return self._repository.get_task(work_item_id, task_id)


    def record_activity(
        self,
        work_item_id: str,
        task_id: str,
        input: Mapping[str, Any],
    ) -> Task:
        if not input:
            raise TaskValidationError("'record_activity' request must contain an activity payload")
        normalized = deepcopy(dict(input))  # type: ignore
        activity = self._build_activity(normalized)
        return self._repository.record_activity(work_item_id, task_id, activity)



    def _build_work_item(self, request_id: str, sequence: int, item: dict[str, Any]) -> WorkItem:
        try:
            item_type = WorkItemType(item.get("type"))
        except (TypeError, ValueError) as error:
            raise WorkItemValidationError(f"Invalid work-item type: {item.get('type')}") from error

        allowed = WORK_ITEM_COMMON_INPUT_FIELDS | WORK_ITEM_TYPE_INPUT_FIELDS[item_type]
        unexpected = sorted(set(item) - allowed)
        if unexpected:
            raise WorkItemValidationError(
                f"Creation input contains unsupported fields: {', '.join(unexpected)}"
            )

        work_item_id = f"{request_id}-{sequence}"
        record: WorkItem = {
            "id": work_item_id,
            "type": item_type.value,
            "created": self._today().isoformat(),
            "status": WorkItemStatus.NEW.value,
        }
        for field in ("request", "description", "source"):
            if field in item:
                record[field] = item[field]

        record["tasks"] = []

        if item_type in {WorkItemType.USER_STORY, WorkItemType.CHORE}:
            criteria = item.get("acceptanceCriteria")
            if not isinstance(criteria, list):
                raise WorkItemValidationError("acceptanceCriteria must be an array of descriptions")
            record["acceptanceCriteria"] = [
                {"id": f"{work_item_id}.{index}", "description": description}
                for index, description in enumerate(criteria, start=1)
            ]
            record["specification"] = None
        else:
            for field in WORK_ITEM_TYPE_INPUT_FIELDS[item_type]:
                if field in item:
                    record[field] = item[field]

        self._work_item_validator.validate(record)
        return record

    def _build_specification(self, work_item_id: str, item: dict[str, Any]) -> Specification:
        allowed = SPECIFICATION_COMMON_INPUT_FIELDS
        unexpected = sorted(set(item) - allowed)
        if unexpected:
            raise SpecificationValidationError(f"Creation input contains unsupported fields: {', '.join(unexpected)}")

        record: Specification = {
            "workItemId": work_item_id,
            "created": self._today().isoformat(),
            "status": SpecificationStatus.DRAFT.value
        }
        for field in ("summary", "architecturalSummary", "keyDesignDecisions", "apiContracts", "databaseSchema", "uiComponents", "testingRequirements", "crossTaskIntegrationPoints", "openQuestionsAndRisks"):
            if field in item:
                record[field] = item[field]

        self._specification_validator.validate(record)
        return record


    def _build_tasks(self, work_item: WorkItem, items: Sequence[dict[str, Any]]) -> list[Task]:
        if not items:
            raise TaskValidationError("At least one task is required")

        task_ids: set[str] = set()
        tasks: list[Task] = []
        for item in items:
            allowed = TASK_COMMON_INPUT_FIELDS
            unexpected = sorted(set(item) - allowed)
            if unexpected:
                raise TaskValidationError(
                    f"Task input contains unsupported fields: {', '.join(unexpected)}"
                )

            task_id = item.get("id")
            if not isinstance(task_id, str) or not task_id:
                raise TaskValidationError("Each task must include a non-empty string id")
            if task_id in task_ids:
                raise TaskValidationError(f"Duplicate task id: {task_id}")
            task_ids.add(task_id)

            task: Task = {
                "id": task_id,
                "owner": item.get("owner", "software-engineer"),
                "scope": item.get("scope", ""),
                "affectedPaths": item.get("affectedPaths", []),
                "contracts": item.get("contracts", []),
                "dependencies": item.get("dependencies", []),
                "acceptanceCriteriaCovered": item.get("acceptanceCriteriaCovered", []),
                "state": item.get("state", TaskState.NOT_STARTED.value),
                "implementAttempts": item.get("implementAttempts", 0),
                "testAttempts": item.get("testAttempts", 0),
                "lastFailureSignature": item.get("lastFailureSignature"),
                "latestArtifact": item.get("latestArtifact"),
                "history": item.get("history", []),
            }

            self._task_validator.validate(task)
            tasks.append(task)

        if work_item["type"] in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            known_criteria = {
                criterion["id"]
                for criterion in work_item.get("acceptanceCriteria", [])
                if isinstance(criterion, Mapping) and "id" in criterion
            }
            for task in tasks:
                unknown = sorted(set(task.get("acceptanceCriteriaCovered", [])) - known_criteria)
                if unknown:
                    raise TaskValidationError(
                        "Task references unknown acceptance criteria: "
                        + ", ".join(unknown)
                    )

        return tasks


    def _build_activity(self, item: dict[str, Any]) -> TaskActivity:
        allowed = ACTIVITY_COMMON_INPUT_FIELDS
        unexpected = sorted(set(item) - allowed)
        if unexpected:
            raise TaskValidationError(
                f"Activity input contains unsupported fields: {', '.join(unexpected)}"
            )

        agent = item.get("agent")
        outcome = item.get("outcome")
        next_owner = item.get("nextOwner")
        if not isinstance(agent, str) or not agent:
            raise TaskValidationError("Activity requires a non-empty 'agent'")
        if not isinstance(outcome, str) or not outcome:
            raise TaskValidationError("Activity requires a non-empty 'outcome'")
        if not isinstance(next_owner, str) or not next_owner:
            raise TaskValidationError("Activity requires a non-empty 'nextOwner'")

        try:
            parsed_outcome = TaskOutcome(outcome)
        except ValueError as error:
            raise TaskValidationError(f"Unsupported task activity outcome: {outcome}") from error

        activity: TaskActivity = {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "iteration": 0,
            "agent": agent,
            "outcome": parsed_outcome.value,
            "result": item.get("result", parsed_outcome.value),
            "artifact": item.get("artifact"),
            "filesChanged": item.get("filesChanged", []),
            "nextOwner": next_owner,
        }
        if "technology" in item:
            activity["technology"] = item["technology"]
        if "metrics" in item:
            activity["metrics"] = item["metrics"]
        return activity