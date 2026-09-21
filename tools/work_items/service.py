"""Storage-independent work-item behavior."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import date
from typing import Any

from .models import (
    WorkItem,
    WorkItemConflictError,
    WorkItemStatus,
    WorkItemType,
    WorkItemValidationError,
)
from .repository import WorkItemRepository
from .validation import WorkItemValidator

COMMON_INPUT_FIELDS = {"type", "request", "description", "source"}
TYPE_INPUT_FIELDS = {
    WorkItemType.USER_STORY: {"acceptanceCriteria"},
    WorkItemType.CHORE: {"acceptanceCriteria"},
    WorkItemType.BUG: {"stepsToReproduce", "expectedResult", "actualResult"},
    WorkItemType.DOCUMENTATION: {"content"},
}
TRANSITIONS = {
    WorkItemStatus.NEW: {WorkItemStatus.IN_PROGRESS},
    WorkItemStatus.IN_PROGRESS: {WorkItemStatus.DONE, WorkItemStatus.BLOCKED},
    WorkItemStatus.DONE: set(),
    WorkItemStatus.BLOCKED: set(),
}


class WorkItemService:
    def __init__(
        self,
        repository: WorkItemRepository,
        validator: WorkItemValidator | None = None,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._repository = repository
        self._validator = validator or WorkItemValidator()
        self._today = today

    def create_request(self, inputs: Sequence[Mapping[str, Any]]) -> list[WorkItem]:
        if not inputs:
            raise WorkItemValidationError("A request must contain at least one work item")
        normalized = [deepcopy(dict(item)) for item in inputs]

        def build(request_id: str) -> list[WorkItem]:
            return [
                self._build_work_item(request_id, sequence, item)
                for sequence, item in enumerate(normalized, start=1)
            ]

        return self._repository.create_request(build)

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

    def change_status(self, work_item_id: str, new_status: WorkItemStatus) -> WorkItem:
        current = self.get(work_item_id)
        current_status = WorkItemStatus(current["status"])
        if current_status == new_status:
            return current
        if new_status not in TRANSITIONS[current_status]:
            raise WorkItemConflictError(
                f"Cannot transition {work_item_id} from {current_status.value} "
                f"to {new_status.value}"
            )
        return self._repository.update_status(
            work_item_id, current_status.value, new_status.value
        )

    def _build_work_item(
        self, request_id: str, sequence: int, item: dict[str, Any]
    ) -> WorkItem:
        try:
            item_type = WorkItemType(item.get("type"))
        except (TypeError, ValueError) as error:
            raise WorkItemValidationError(f"Invalid work-item type: {item.get('type')}") from error

        allowed = COMMON_INPUT_FIELDS | TYPE_INPUT_FIELDS[item_type]
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

        if item_type in {WorkItemType.USER_STORY, WorkItemType.CHORE}:
            criteria = item.get("acceptanceCriteria")
            if not isinstance(criteria, list):
                raise WorkItemValidationError("acceptanceCriteria must be an array of descriptions")
            record["acceptanceCriteria"] = [
                {"id": f"{work_item_id}.{index}", "description": description}
                for index, description in enumerate(criteria, start=1)
            ]
        else:
            for field in TYPE_INPUT_FIELDS[item_type]:
                if field in item:
                    record[field] = item[field]

        self._validator.validate(record)
        return record