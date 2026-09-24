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
    Specification,
    SpecificationConflictError,
    SpecificationStatus,
    SpecificationValidationError
)
from .repository import WorkItemRepository
from .validation import WorkItemValidator, SpecificationValidator

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
    "tasks",
    "crossTaskIntegrationPoints",
    "openQuestionsAndRisks",
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
        today: Callable[[], date] = date.today,
    ) -> None:
        self._repository = repository
        self._work_item_validator = work_item_validator or WorkItemValidator()
        self._specification_validator = specification_validator or SpecificationValidator()
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


    def add_spec(self, work_item_id: str, input: Mapping[str, Any]) -> Specification:
        if not input:
            raise SpecificationValidationError("'add_spec' request must contain a specification")
        normalized = deepcopy(dict(input))  # type: ignore

        work_item = self.get(work_item_id)
        if work_item["type"] not in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            raise SpecificationValidationError(
                f"Specifications are only supported for user-story and chore work items: {work_item_id}"
            )

        specification = self._build_specification(work_item_id, normalized)

        return self._repository.add_spec(work_item_id, specification)


    def revise_spec(self, work_item_id: str, input: Mapping[str, Any]) -> Specification:
        if not input:
            raise SpecificationValidationError("'revise_spec' request must contain a specification")
        normalized = deepcopy(dict(input))  # type: ignore

        work_item = self.get(work_item_id)
        if work_item["type"] not in {WorkItemType.USER_STORY.value, WorkItemType.CHORE.value}:
            raise SpecificationValidationError(
                f"Specifications are only supported for user-story and chore work items: {work_item_id}"
            )

        specification = self._build_specification(work_item_id, normalized)

        return self._repository.revise_spec(work_item_id, specification)


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
        for field in ("summary", "architecturalSummary", "keyDesignDecisions", "apiContracts", "databaseSchema", "uiComponents", "testingRequirements", "tasks", "crossTaskIntegrationPoints", "openQuestionsAndRisks"):
            if field in item:
                record[field] = item[field]

        self._specification_validator.validate(record)
        return record