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
    SpecificationStatus,
    SpecificationValidationError,
    PlanConflictError,
    PlanNotFoundError,
    PlanStatus,
    Task,
    TaskActivity,
    TaskOutcome,
    TaskPhase,
    TaskState,
    TaskValidationError,
)
from . import phases
from .repository import WorkItemRepository
from .validation import WorkItemValidator, SpecificationValidator, TaskValidator

SPECIFICATION_TYPES = {WorkItemType.USER_STORY, WorkItemType.CHORE}
REVIEWED_TYPES = SPECIFICATION_TYPES

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
    "crossTaskIntegrationPoints",
    "openQuestionsAndRisks",
}
TASK_COMMON_INPUT_FIELDS = {
    "id",
    "phase",
    "owner",
    "scope",
    "deliverables",
    "verification",
    "technology",
    "affectedPaths",
    "contracts",
    "dependencies",
    "acceptanceCriteriaCovered",
}
ACTIVITY_COMMON_INPUT_FIELDS = {
    "agent",
    "technology",
    "outcome",
    "result",
    "artifact",
    "filesChanged",
    "remediationTargetTaskId",
    "failureSignature",
    "metrics",
}
INTAKE_INPUT_FIELDS = {"agent", "result", "metrics"}
METRIC_FIELDS = {
    "durationSeconds",
    "inputTokens",
    "outputTokens",
    "totalTokens",
    "model",
    "estimatedCostUsd",
}
PLACEHOLDER_MODELS = {"unknown", "n/a", "na", "none", "null", "model", "tbd"}
INTAKE_AGENTS = {"triage", "software-architect"}
PLAN_RISKS = {"low", "medium", "high"}
PLAN_MODES = {"lean", "balanced", "strict"}
DEFAULT_EXECUTION = {
    "branch": None,
    "budget": {
        "maxTaskAttempts": 3,
        "maxReviewLoops": 3,
        "maxValidationLoops": 3,
        "maxTotalAgentRuns": 40,
        "reviewLoops": 0,
        "validationLoops": 0,
        "totalAgentRuns": 0,
    },
    "totals": {
        "durationSeconds": 0,
        "totalTokens": 0,
        "estimatedCostUsd": 0,
    },
    "escalations": [],
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


    def add_spec(
        self,
        work_item_id: str,
        input: Mapping[str, Any],
        tasks_input: Sequence[Mapping[str, Any]],
        plan_policy: Mapping[str, Any] | None = None,
        repository_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._author_plan(
            work_item_id,
            input,
            tasks_input,
            revise=False,
            plan_policy=plan_policy,
            repository_context=repository_context,
        )


    def revise_spec(
        self,
        work_item_id: str,
        input: Mapping[str, Any],
        tasks_input: Sequence[Mapping[str, Any]],
        plan_policy: Mapping[str, Any] | None = None,
        repository_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._author_plan(
            work_item_id,
            input,
            tasks_input,
            revise=True,
            plan_policy=plan_policy,
            repository_context=repository_context,
        )


    def add_tasks(
        self,
        work_item_id: str,
        tasks_input: Sequence[Mapping[str, Any]],
        plan_policy: Mapping[str, Any] | None = None,
        repository_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._author_plan(
            work_item_id,
            None,
            tasks_input,
            revise=False,
            plan_policy=plan_policy,
            repository_context=repository_context,
        )


    def revise_tasks(
        self,
        work_item_id: str,
        tasks_input: Sequence[Mapping[str, Any]],
        plan_policy: Mapping[str, Any] | None = None,
        repository_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._author_plan(
            work_item_id,
            None,
            tasks_input,
            revise=True,
            plan_policy=plan_policy,
            repository_context=repository_context,
        )


    def get_plan(self, work_item_id: str) -> dict[str, Any]:
        self.get(work_item_id)
        return self._repository.get_plan(work_item_id)


    def approve_plan(self, work_item_id: str) -> dict[str, Any]:
        work_item = self.get(work_item_id)
        current_status = work_item.get("planStatus")
        if current_status is None:
            raise PlanNotFoundError(f"Work item {work_item_id} has no task plan to approve")
        if current_status == PlanStatus.APPROVED.value:
            return self._repository.get_plan(work_item_id)
        if current_status != PlanStatus.DRAFT.value:
            raise PlanConflictError(
                f"Cannot approve the plan for work item {work_item_id} from status {current_status}"
            )
        return self._repository.approve_plan(work_item_id)


    def get_spec(self, work_item_id: str) -> Specification:
        self.get(work_item_id)
        return self._repository.get_spec(work_item_id)


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
        work_item = self.get(work_item_id)
        if work_item.get("planStatus") != PlanStatus.APPROVED.value:
            raise PlanConflictError(
                f"Work item {work_item_id} has no approved plan; activity cannot be recorded"
            )
        task = self._repository.get_task(work_item_id, task_id)
        normalized = deepcopy(dict(input))  # type: ignore
        activity, failure_signature = self._build_activity(task, normalized)
        return self._repository.record_activity(work_item_id, task_id, activity, failure_signature)


    def record_intake(self, work_item_id: str, input: Mapping[str, Any]) -> WorkItem:
        if not input:
            raise TaskValidationError("'record_intake' request must contain an activity payload")
        self.get(work_item_id)
        activity = self._build_intake_activity(deepcopy(dict(input)))
        return self._repository.record_intake(work_item_id, activity)


    def _author_plan(
        self,
        work_item_id: str,
        specification_input: Mapping[str, Any] | None,
        tasks_input: Sequence[Mapping[str, Any]],
        *,
        revise: bool,
        plan_policy: Mapping[str, Any] | None = None,
        repository_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not tasks_input:
            raise TaskValidationError("A task plan must contain at least one task")

        work_item = self.get(work_item_id)
        item_type = WorkItemType(work_item["type"])
        requires_specification = item_type in SPECIFICATION_TYPES

        if requires_specification and not specification_input:
            raise SpecificationValidationError(
                f"Work item {work_item_id} of type {item_type.value} requires a specification"
            )
        if not requires_specification and specification_input:
            raise SpecificationValidationError(
                f"Work item {work_item_id} of type {item_type.value} must not have a specification"
            )

        current_status = work_item.get("planStatus")
        if current_status == PlanStatus.APPROVED.value:
            raise PlanConflictError(f"Work item {work_item_id} already has an approved plan")
        if revise and current_status is None:
            raise PlanConflictError(f"Work item {work_item_id} has no task plan to revise")
        if not revise and current_status is not None:
            raise PlanConflictError(f"Work item {work_item_id} already has a task plan")

        specification = (
            self._build_specification(work_item_id, deepcopy(dict(specification_input)))
            if specification_input
            else None
        )
        tasks = self._build_tasks(work_item, [deepcopy(dict(task)) for task in tasks_input])
        normalized_policy = (
            _build_plan_policy(plan_policy)
            if plan_policy is not None
            else work_item.get("planPolicy")
        )
        if repository_context is not None and not isinstance(repository_context, Mapping):
            raise TaskValidationError("Repository context must be an object")
        normalized_context = (
            deepcopy(dict(repository_context))
            if repository_context is not None
            else work_item.get("repositoryContext")
        )

        return self._repository.set_plan(
            work_item_id, specification, tasks, normalized_policy, normalized_context
        )



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
        record["specification"] = None
        record["planStatus"] = None
        record["intake"] = []
        record["execution"] = deepcopy(DEFAULT_EXECUTION)

        if item_type in {WorkItemType.USER_STORY, WorkItemType.CHORE}:
            criteria = item.get("acceptanceCriteria")
            if not isinstance(criteria, list):
                raise WorkItemValidationError("acceptanceCriteria must be an array of descriptions")
            record["acceptanceCriteria"] = [
                {"id": f"{work_item_id}.{index}", "description": description}
                for index, description in enumerate(criteria, start=1)
            ]
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
        for field in ("summary", "architecturalSummary", "keyDesignDecisions", "apiContracts", "databaseSchema", "uiComponents", "crossTaskIntegrationPoints", "openQuestionsAndRisks"):
            if field in item:
                record[field] = item[field]

        self._specification_validator.validate(record)
        return record


    def _build_tasks(self, work_item: WorkItem, items: Sequence[dict[str, Any]]) -> list[Task]:
        if not items:
            raise TaskValidationError("At least one task is required")

        item_type = WorkItemType(work_item["type"])
        task_ids: set[str] = set()
        tasks: list[Task] = []
        for item in items:
            unexpected = sorted(set(item) - TASK_COMMON_INPUT_FIELDS)
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

            try:
                phase = TaskPhase(item.get("phase"))
            except (TypeError, ValueError) as error:
                raise TaskValidationError(
                    f"Task {task_id} has an invalid phase: {item.get('phase')}"
                ) from error

            expected_owner = phases.owner_for(phase)
            owner = item.get("owner", expected_owner)
            if owner != expected_owner:
                raise TaskValidationError(
                    f"Task {task_id} in phase {phase.value} must be owned by {expected_owner}"
                )

            task: Task = {
                "id": task_id,
                "phase": phase.value,
                "owner": owner,
                "scope": item.get("scope", ""),
                "deliverables": item.get("deliverables", []),
                "verification": item.get("verification", []),
                "affectedPaths": item.get("affectedPaths", []),
                "contracts": item.get("contracts", []),
                "dependencies": item.get("dependencies", []),
                "acceptanceCriteriaCovered": item.get("acceptanceCriteriaCovered", []),
                "state": TaskState.NOT_STARTED.value,
                "attempts": 0,
                "lastFailureSignature": None,
                "previousFailureSignature": None,
                "latestArtifact": None,
                "remediationTargetTaskId": None,
                "blockedReason": None,
                "history": [],
            }
            if "technology" in item:
                task["technology"] = item["technology"]

            self._task_validator.validate(task)
            tasks.append(task)

        self._validate_dependencies(tasks, task_ids)
        self._validate_graph_shape(item_type, tasks)

        if item_type in SPECIFICATION_TYPES:
            known_criteria = {
                criterion["id"]
                for criterion in work_item.get("acceptanceCriteria", [])
                if isinstance(criterion, Mapping) and "id" in criterion
            }
            for task in tasks:
                unknown = sorted(set(task.get("acceptanceCriteriaCovered", [])) - known_criteria)
                if unknown:
                    raise TaskValidationError(
                        "Task references unknown acceptance criteria: " + ", ".join(unknown)
                    )

        return tasks


    @staticmethod
    def _validate_dependencies(tasks: Sequence[Task], task_ids: set[str]) -> None:
        for task in tasks:
            unknown = sorted(set(task["dependencies"]) - task_ids)
            if unknown:
                raise TaskValidationError(
                    f"Task {task['id']} depends on unknown tasks: {', '.join(unknown)}"
                )
            if task["id"] in task["dependencies"]:
                raise TaskValidationError(f"Task {task['id']} cannot depend on itself")

        dependencies = {task["id"]: list(task["dependencies"]) for task in tasks}
        resolved: set[str] = set()
        visiting: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in resolved:
                return
            if task_id in visiting:
                raise TaskValidationError(f"Task dependencies contain a cycle involving {task_id}")
            visiting.add(task_id)
            for dependency in dependencies[task_id]:
                visit(dependency)
            visiting.discard(task_id)
            resolved.add(task_id)

        for task_id in dependencies:
            visit(task_id)


    @staticmethod
    def _validate_graph_shape(item_type: WorkItemType, tasks: Sequence[Task]) -> None:
        by_phase: dict[str, list[Task]] = {}
        for task in tasks:
            by_phase.setdefault(task["phase"], []).append(task)

        if not by_phase.get(TaskPhase.VALIDATION.value):
            raise TaskValidationError("A task plan must contain a validation task")

        review_tasks = by_phase.get(TaskPhase.REVIEW.value, [])
        implementation_tasks = by_phase.get(TaskPhase.IMPLEMENTATION.value, [])

        if item_type not in REVIEWED_TYPES:
            if review_tasks:
                raise TaskValidationError(
                    f"Work items of type {item_type.value} must not contain review tasks"
                )
            return

        dependents: dict[str, list[str]] = {task["id"]: [] for task in tasks}
        for task in tasks:
            for dependency in task["dependencies"]:
                dependents[dependency].append(task["id"])
        phase_by_id = {task["id"]: task["phase"] for task in tasks}

        for task in implementation_tasks:
            if not _reaches_phase(task["id"], TaskPhase.REVIEW.value, dependents, phase_by_id):
                raise TaskValidationError(
                    f"Implementation task {task['id']} is not covered by a review task"
                )


    def _build_activity(
        self, task: Task, item: dict[str, Any]
    ) -> tuple[TaskActivity, str | None]:
        unexpected = sorted(set(item) - ACTIVITY_COMMON_INPUT_FIELDS)
        if unexpected:
            raise TaskValidationError(
                f"Activity input contains unsupported fields: {', '.join(unexpected)}"
            )

        agent = item.get("agent")
        outcome = item.get("outcome")
        if not isinstance(agent, str) or not agent:
            raise TaskValidationError("Activity requires a non-empty 'agent'")
        if agent != task["owner"]:
            raise TaskValidationError(
                f"Task {task['id']} is owned by {task['owner']}, not {agent}"
            )
        if not isinstance(outcome, str) or not outcome:
            raise TaskValidationError("Activity requires a non-empty 'outcome'")

        try:
            parsed_outcome = TaskOutcome(outcome)
        except ValueError as error:
            raise TaskValidationError(f"Unsupported task activity outcome: {outcome}") from error

        phase = TaskPhase(task["phase"])
        if parsed_outcome not in phases.allowed_outcomes(phase):
            allowed = ", ".join(sorted(value.value for value in phases.allowed_outcomes(phase)))
            raise TaskValidationError(
                f"Outcome {parsed_outcome.value} is not valid for a {phase.value} task. "
                f"Allowed outcomes: {allowed}"
            )

        metrics = item.get("metrics")
        if not isinstance(metrics, Mapping):
            raise TaskValidationError("Activity requires a 'metrics' object")
        _validate_metrics(metrics)

        remediation_target = item.get("remediationTargetTaskId")
        if parsed_outcome in phases.REMEDIATION_OUTCOMES and not remediation_target:
            raise TaskValidationError(
                f"Outcome {parsed_outcome.value} requires a 'remediationTargetTaskId'"
            )

        activity: TaskActivity = {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "iteration": 0,
            "agent": agent,
            "outcome": parsed_outcome.value,
            "result": item.get("result", parsed_outcome.value),
            "artifact": item.get("artifact"),
            "filesChanged": item.get("filesChanged", []),
            "metrics": dict(metrics),
        }
        if "technology" in item:
            activity["technology"] = item["technology"]
        if remediation_target:
            activity["remediationTargetTaskId"] = remediation_target

        failure_signature = item.get("failureSignature")
        return activity, failure_signature


    @staticmethod
    def _build_intake_activity(item: dict[str, Any]) -> dict[str, Any]:
        unexpected = sorted(set(item) - INTAKE_INPUT_FIELDS)
        if unexpected:
            raise TaskValidationError(
                f"Intake input contains unsupported fields: {', '.join(unexpected)}"
            )

        agent = item.get("agent")
        if agent not in INTAKE_AGENTS:
            allowed = ", ".join(sorted(INTAKE_AGENTS))
            raise TaskValidationError(f"Intake activity must be recorded by one of: {allowed}")

        result = item.get("result")
        if not isinstance(result, str) or not result:
            raise TaskValidationError("Intake activity requires a non-empty 'result'")

        metrics = item.get("metrics")
        if not isinstance(metrics, Mapping):
            raise TaskValidationError("Intake activity requires a 'metrics' object")
        _validate_metrics(metrics)

        return {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "agent": agent,
            "result": result,
            "metrics": dict(metrics),
        }


def _validate_metrics(metrics: Mapping[str, Any]) -> None:
    """Reject missing or placeholder run metrics; see .agents/resources/tasks.md#run-metrics."""
    missing = sorted(METRIC_FIELDS - set(metrics))
    if missing:
        raise TaskValidationError(f"Metrics are missing required fields: {', '.join(missing)}")
    unexpected = sorted(set(metrics) - METRIC_FIELDS)
    if unexpected:
        raise TaskValidationError(f"Metrics contain unsupported fields: {', '.join(unexpected)}")

    def is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    for field in ("inputTokens", "outputTokens", "totalTokens"):
        value = metrics[field]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise TaskValidationError(
                f"Metrics field '{field}' must be a positive integer estimate of the run's tokens"
            )
    if metrics["totalTokens"] != metrics["inputTokens"] + metrics["outputTokens"]:
        raise TaskValidationError("Metrics 'totalTokens' must equal inputTokens + outputTokens")

    duration = metrics["durationSeconds"]
    if not is_number(duration) or duration <= 0:
        raise TaskValidationError(
            "Metrics 'durationSeconds' must be a positive number measured from the run's start time"
        )

    cost = metrics["estimatedCostUsd"]
    if not is_number(cost) or cost < 0:
        raise TaskValidationError("Metrics 'estimatedCostUsd' must be a non-negative number")

    model = metrics["model"]
    if not isinstance(model, str) or model.strip().lower() in PLACEHOLDER_MODELS | {""}:
        raise TaskValidationError("Metrics 'model' must name the model that performed the run")


def _build_plan_policy(item: Mapping[str, Any]) -> dict[str, str]:
    unexpected = sorted(set(item) - {"risk", "mode"})
    if unexpected:
        raise TaskValidationError(
            "Plan policy contains unsupported fields: " + ", ".join(unexpected)
        )

    risk = item.get("risk")
    mode = item.get("mode")
    if not isinstance(risk, str) or risk not in PLAN_RISKS:
        raise TaskValidationError("Plan policy risk must be low, medium, or high")
    if not isinstance(mode, str) or mode not in PLAN_MODES:
        raise TaskValidationError("Plan policy mode must be lean, balanced, or strict")

    return {"risk": risk, "mode": mode}


def _reaches_phase(
    task_id: str,
    phase: str,
    dependents: Mapping[str, list[str]],
    phase_by_id: Mapping[str, str],
) -> bool:
    seen: set[str] = set()
    queue = list(dependents[task_id])
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        seen.add(current)
        if phase_by_id[current] == phase:
            return True
        queue.extend(dependents[current])
    return False