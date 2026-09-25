"""JSON-file implementation of the work-item repository."""

from __future__ import annotations

import json
import os
import re
import shutil
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Iterator

from filelock import FileLock, Timeout

from .models import (
    WorkItem,
    WorkItemConflictError,
    WorkItemNotFoundError,
    WorkItemStorageError,
    WorkItemValidationError,
    Specification,
    SpecificationConflictError,
    SpecificationNotFoundError,
    SpecificationValidationError,
    Task,
    TaskActivity,
    TaskNotFoundError,
    TaskState,
)
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

    def add_spec(self, work_item_id: str, specification: Specification, tasks: list[Task]) -> Specification:
        if not specification:
            raise SpecificationValidationError("'add_spec' requests must supply a specification")
        if not tasks:
            raise SpecificationValidationError("'add_spec' requests must supply at least one task")
        with self._lock():
            work_item = self.get(work_item_id)
            if work_item.get("specification"):
                raise WorkItemConflictError(f"Work item {work_item_id} already has a specification")

            self._specification_validator.validate(specification)
            if specification["status"] != "draft":
                raise SpecificationValidationError("New specifications must have status 'draft'")

            work_item["specification"] = specification
            work_item["tasks"] = tasks
            self._work_item_validator.validate(work_item)
            self._write_atomic(self._path_for(work_item_id), work_item)
            return specification

    def revise_spec(self, work_item_id: str, specification: Specification, tasks: list[Task]) -> Specification:
        if not specification:
            raise SpecificationValidationError("'revise_spec' requests must supply a specification")
        if not tasks:
            raise SpecificationValidationError("'revise_spec' requests must supply at least one task")
        with self._lock():
            work_item = self.get(work_item_id)
            if not work_item.get("specification"):
                raise WorkItemConflictError(f"Work item {work_item_id} does not have a specification to revise")
            if work_item["specification"]["status"] == "approved":
                raise WorkItemConflictError(f"Work item {work_item_id} already has an approved specification")

            self._specification_validator.validate(specification)
            if specification["status"] != "draft":
                raise SpecificationValidationError("Revised specifications must have status 'draft'")

            work_item["specification"] = specification
            work_item["tasks"] = tasks
            self._work_item_validator.validate(work_item)
            self._write_atomic(self._path_for(work_item_id), work_item)
            return specification

    def get_spec(self, work_item_id: str) -> Specification:
        work_item = self.get(work_item_id)
        specification = work_item.get("specification")

        if not specification:
            raise SpecificationNotFoundError(f"No specification found for work item {work_item_id}")

        self._specification_validator.validate(specification)

        return specification

    def approve_spec(self, work_item_id: str) -> Specification:
        with self._lock():
            work_item = self.get(work_item_id)
            specification = work_item.get("specification")
            if not specification:
                raise SpecificationNotFoundError(f"No specification found for work item {work_item_id}")
            if specification["status"] != "draft":
                raise SpecificationConflictError(
                    f"Specification for work item {work_item_id} status is not draft"
                )

            specification["status"] = "approved"
            self._specification_validator.validate(specification)
            self._write_atomic(self._path_for(work_item_id), work_item)
            return specification


    def get_task(self, work_item_id: str, task_id: str) -> Task:
        work_item = self.get(work_item_id)
        for task in work_item.get("tasks", []):
            if task.get("id") == task_id:
                return task
        raise TaskNotFoundError(f"Task {task_id} was not found for work item {work_item_id}")


    def record_activity(self, work_item_id: str, task_id: str, activity: TaskActivity) -> Task:
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

                outcome = activity_entry["outcome"]
                if outcome == "implemented":
                    task["state"] = TaskState.IMPLEMENTED.value
                    task["implementAttempts"] = int(task.get("implementAttempts", 0)) + 1
                elif outcome == "passed":
                    task["state"] = TaskState.TESTS_PASSING.value
                    task["testAttempts"] = int(task.get("testAttempts", 0)) + 1
                elif outcome == "failed":
                    task["state"] = TaskState.TESTS_FAILING.value
                    task["testAttempts"] = int(task.get("testAttempts", 0)) + 1
                elif outcome in {"blocked", "Blocked"}:
                    task["state"] = TaskState.BLOCKED.value

                artifact = activity_entry.get("artifact")
                if artifact:
                    task["latestArtifact"] = artifact

                self._work_item_validator.validate(work_item)
                self._write_atomic(self._path_for(work_item_id), work_item)
                return task

        raise TaskNotFoundError(f"Task {task_id} was not found for work item {work_item_id}")


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
