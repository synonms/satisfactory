"""JSON-file implementation of the work-item repository."""

from __future__ import annotations

import json
import os
import re
import shutil
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterator

from filelock import FileLock, Timeout

from .models import (
    WorkItem,
    WorkItemConflictError,
    WorkItemNotFoundError,
    WorkItemStorageError,
    WorkItemValidationError,
    IntakeActivity,
    Specification,
    SpecificationNotFoundError,
    SpecificationValidationError,
    PlanConflictError,
    PlanNotFoundError,
    PlanStatus,
    Task,
    TaskActivity,
    TaskNotFoundError,
    TaskOutcome,
    TaskPhase,
    TaskState,
)
from . import phases
from .repository import RequestFactory
from .validation import WorkItemValidator, SpecificationValidator

WORK_ITEM_ID = re.compile(r"^(?P<request>[0-9]{5})-[1-9][0-9]*$")


class JsonFileWorkItemRepository:
    def __init__(self, board_root: Path, work_item_validator: WorkItemValidator | None = None, specification_validator: SpecificationValidator | None = None) -> None:
        self._board_root = board_root
        self._work_item_validator = work_item_validator or WorkItemValidator()
        self._specification_validator = specification_validator or SpecificationValidator()

    def create(self, factory: RequestFactory) -> list[WorkItem]:
        self._board_root.mkdir(parents=True, exist_ok=True)
        with self._lock():
            request_id = f"{self._next_request_number():05d}"
            request_directory = self._board_root / request_id
            if request_directory.exists():
                raise WorkItemConflictError(f"Request {request_id} already exists")

            records = [deepcopy(record) for record in factory(request_id)]
            if not records:
                raise WorkItemValidationError("A request must contain at least one work item")
            for record in records:
                self._work_item_validator.validate(record)

            request_directory.mkdir()
            try:
                for record in records:
                    self._write_atomic(self._path_for(record["id"]), record)
                self._write_text_atomic(self._board_root / ".id", request_id + "\n")
            except Exception:
                shutil.rmtree(request_directory, ignore_errors=True)
                raise
            return records

    def get(self, work_item_id: str) -> WorkItem:
        path = self._path_for(work_item_id)
        if not path.is_file():
            raise WorkItemNotFoundError(f"Work item {work_item_id} was not found")
        return self._read(path)

    def list(self) -> list[WorkItem]:
        if not self._board_root.exists():
            return []
        records = [self._read(path) for path in self._board_root.glob("[0-9]????/*.work-item.json")]
        return sorted(records, key=lambda record: _id_parts(record["id"]))

    def update_status(self, work_item_id: str, expected_status: str, status: str) -> WorkItem:
        self._board_root.mkdir(parents=True, exist_ok=True)
        with self._lock():
            record = self.get(work_item_id)
            if record["status"] != expected_status:
                raise WorkItemConflictError(
                    f"Work item {work_item_id} status changed from {expected_status} "
                    f"to {record['status']}"
                )
            record["status"] = status
            self._work_item_validator.validate(record)
            self._write_atomic(self._path_for(work_item_id), record)
            return record

    def set_plan(
        self,
        work_item_id: str,
        specification: Specification | None,
        tasks: list[Task],
    ) -> dict[str, Any]:
        if not tasks:
            raise SpecificationValidationError("A task plan must supply at least one task")
        with self._lock():
            work_item = self.get(work_item_id)
            if work_item.get("planStatus") == PlanStatus.APPROVED.value:
                raise PlanConflictError(f"Work item {work_item_id} already has an approved plan")

            if specification is not None:
                self._specification_validator.validate(specification)
                if specification["status"] != "draft":
                    raise SpecificationValidationError(
                        "New and revised specifications must have status 'draft'"
                    )

            work_item["specification"] = specification
            work_item["tasks"] = tasks
            work_item["planStatus"] = PlanStatus.DRAFT.value
            self._work_item_validator.validate(work_item)
            self._write_atomic(self._path_for(work_item_id), work_item)
            return _plan_of(work_item)

    def get_plan(self, work_item_id: str) -> dict[str, Any]:
        work_item = self.get(work_item_id)
        if work_item.get("planStatus") is None:
            raise PlanNotFoundError(f"No task plan found for work item {work_item_id}")
        return _plan_of(work_item)

    def approve_plan(self, work_item_id: str) -> dict[str, Any]:
        with self._lock():
            work_item = self.get(work_item_id)
            if work_item.get("planStatus") != PlanStatus.DRAFT.value:
                raise PlanConflictError(
                    f"Plan for work item {work_item_id} is not in draft status"
                )

            work_item["planStatus"] = PlanStatus.APPROVED.value
            specification = work_item.get("specification")
            if specification:
                specification["status"] = "approved"
                self._specification_validator.validate(specification)

            self._work_item_validator.validate(work_item)
            self._write_atomic(self._path_for(work_item_id), work_item)
            return _plan_of(work_item)

    def get_spec(self, work_item_id: str) -> Specification:
        work_item = self.get(work_item_id)
        specification = work_item.get("specification")

        if not specification:
            raise SpecificationNotFoundError(f"No specification found for work item {work_item_id}")

        self._specification_validator.validate(specification)

        return specification


    def get_task(self, work_item_id: str, task_id: str) -> Task:
        work_item = self.get(work_item_id)
        for task in work_item.get("tasks", []):
            if task.get("id") == task_id:
                return task
        raise TaskNotFoundError(f"Task {task_id} was not found for work item {work_item_id}")


    def record_activity(
        self,
        work_item_id: str,
        task_id: str,
        activity: TaskActivity,
        failure_signature: str | None = None,
    ) -> Task:
        with self._lock():
            work_item = self.get(work_item_id)
            tasks = work_item.get("tasks", [])
            for task in tasks:
                if task.get("id") != task_id:
                    continue

                history = task.setdefault("history", [])
                activity_entry = deepcopy(activity)
                activity_entry["iteration"] = len(history) + 1
                history.append(activity_entry)

                phase = TaskPhase(task["phase"])
                outcome = TaskOutcome(activity_entry["outcome"])
                next_state = phases.state_for_outcome(phase, outcome)
                if next_state is None:
                    raise WorkItemValidationError(
                        f"Outcome {outcome.value} is not valid for a {phase.value} task"
                    )

                task["state"] = next_state.value
                task["attempts"] = int(task.get("attempts", 0)) + 1
                task["previousFailureSignature"] = task.get("lastFailureSignature")
                task["lastFailureSignature"] = failure_signature
                task["remediationTargetTaskId"] = activity_entry.get("remediationTargetTaskId")
                task["blockedReason"] = (
                    activity_entry["result"] if next_state is TaskState.BLOCKED else None
                )

                artifact = activity_entry.get("artifact")
                if artifact:
                    task["latestArtifact"] = artifact

                _apply_remediation(work_item, task, outcome)
                _accumulate(work_item, activity_entry)

                self._work_item_validator.validate(work_item)
                self._write_atomic(self._path_for(work_item_id), work_item)
                return task

        raise TaskNotFoundError(f"Task {task_id} was not found for work item {work_item_id}")


    def record_intake(self, work_item_id: str, activity: IntakeActivity) -> WorkItem:
        with self._lock():
            work_item = self.get(work_item_id)
            work_item.setdefault("intake", []).append(deepcopy(activity))
            _accumulate_totals(work_item, activity.get("metrics", {}))
            self._work_item_validator.validate(work_item)
            self._write_atomic(self._path_for(work_item_id), work_item)
            return work_item


    def _next_request_number(self) -> int:
        stored = 0
        id_path = self._board_root / ".id"
        if id_path.exists():
            try:
                value = id_path.read_text(encoding="utf-8").strip()
                stored = int(value) if value else 0
            except (OSError, ValueError) as error:
                raise WorkItemStorageError(f"Cannot read request ID store: {error}") from error

        existing = [
            int(path.name)
            for path in self._board_root.iterdir()
            if path.is_dir() and re.fullmatch(r"[0-9]{5}", path.name)
        ]
        return max([stored, *existing], default=0) + 1

    def _path_for(self, work_item_id: str) -> Path:
        match = WORK_ITEM_ID.fullmatch(work_item_id)
        if not match:
            raise WorkItemValidationError(f"Invalid work-item ID: {work_item_id}")
        return self._board_root / match.group("request") / f"{work_item_id}.work-item.json"

    def _read(self, path: Path) -> WorkItem:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise WorkItemStorageError(f"Cannot read {path}: {error}") from error
        if not isinstance(value, dict):
            raise WorkItemValidationError(f"Work item in {path} must be a JSON object")
        self._work_item_validator.validate(value)
        return value

    def _write_atomic(self, path: Path, value: WorkItem) -> None:
        text = json.dumps(value, indent=2, ensure_ascii=True) + "\n"
        self._write_text_atomic(path, text)

    @staticmethod
    def _write_text_atomic(path: Path, text: str) -> None:
        temporary_path = path.with_name(path.name + ".tmp")
        try:
            temporary_path.write_text(text, encoding="utf-8", newline="\n")
            os.replace(temporary_path, path)
        except OSError as error:
            temporary_path.unlink(missing_ok=True)
            raise WorkItemStorageError(f"Cannot write {path}: {error}") from error

    @contextmanager
    def _lock(self) -> Iterator[None]:
        lock_path = self._board_root / ".work-items.lock"
        try:
            with FileLock(lock_path, timeout=30):
                yield
        except (OSError, Timeout) as error:
            raise WorkItemStorageError(f"Cannot lock work-item store: {error}") from error


def _id_parts(work_item_id: str) -> tuple[int, int]:
    request_id, sequence = work_item_id.split("-", maxsplit=1)
    return int(request_id), int(sequence)


def _plan_of(work_item: WorkItem) -> dict[str, Any]:
    return {
        "workItemId": work_item["id"],
        "planStatus": work_item["planStatus"],
        "specification": work_item.get("specification"),
        "tasks": work_item.get("tasks", []),
    }


def _apply_remediation(work_item: WorkItem, source: Task, outcome: TaskOutcome) -> None:
    """Send the named task back for rework and reset everything downstream of it."""
    if outcome not in phases.REMEDIATION_OUTCOMES:
        return

    target_id = source.get("remediationTargetTaskId")
    tasks = {task["id"]: task for task in work_item.get("tasks", [])}
    target = tasks.get(target_id)
    if target is None:
        raise WorkItemValidationError(f"Remediation target {target_id} was not found")

    target["state"] = phases.REWORK_STATE[TaskPhase(target["phase"])].value

    dependents: dict[str, list[str]] = {task_id: [] for task_id in tasks}
    for task in tasks.values():
        for dependency in task.get("dependencies", []):
            dependents[dependency].append(task["id"])

    queue = list(dependents[target_id])
    seen: set[str] = set()
    while queue:
        current = queue.pop()
        if current in seen or current == source["id"]:
            continue
        seen.add(current)
        tasks[current]["state"] = TaskState.NOT_STARTED.value
        queue.extend(dependents[current])

    budget = work_item["execution"]["budget"]
    counter = "reviewLoops" if outcome is TaskOutcome.CHANGES_REQUESTED else "validationLoops"
    budget[counter] = int(budget[counter]) + 1


def _accumulate(work_item: WorkItem, activity: TaskActivity) -> None:
    execution = work_item["execution"]
    _accumulate_totals(work_item, activity.get("metrics", {}))
    execution["budget"]["totalAgentRuns"] += 1


def _accumulate_totals(work_item: WorkItem, metrics: dict[str, Any]) -> None:
    totals = work_item["execution"]["totals"]
    totals["durationSeconds"] += metrics.get("durationSeconds", 0)
    totals["totalTokens"] += metrics.get("totalTokens", 0)
    totals["estimatedCostUsd"] += metrics.get("estimatedCostUsd", 0)
