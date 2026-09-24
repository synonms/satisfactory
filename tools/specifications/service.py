"""Storage-independent specification behavior."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from datetime import date
from typing import Any

from .models import (
    Specification,
    SpecificationConflictError,
    SpecificationStatus,
    SpecificationValidationError,
)
from .repository import SpecificationRepository
from .validation import SpecificationValidator

COMMON_INPUT_FIELDS = {"workItemId", "created", "status", "summary", "acceptanceCriteria", "architecturalSummary", "keyDesignDecisions", "apiContracts", "databaseSchema", "uiComponents", "testingRequirements", "tasks", "crossTaskIntegrationPoints", "openQuestionsAndRisks"}
TRANSITIONS = {
    SpecificationStatus.DRAFT: {SpecificationStatus.APPROVED},
    SpecificationStatus.APPROVED: set()
}


class SpecificationService:
    def __init__(
        self,
        repository: SpecificationRepository,
        validator: SpecificationValidator | None = None,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._repository = repository
        self._validator = validator or SpecificationValidator()
        self._today = today

    def create(self, input: Mapping[str, Any]) -> Specification:
        if not input:
            raise SpecificationValidationError("A request must contain a specification")
        normalized = deepcopy(dict(input))  # type: ignore

        specification = self._build_specification(normalized)

        return self._repository.create(specification)

    def update(self, input: Mapping[str, Any]) -> Specification:
        if not input:
            raise SpecificationValidationError("A request must contain a specification")
        normalized = deepcopy(dict(input))  # type: ignore

        specification = self._build_specification(normalized)

        return self._repository.update(specification)

    def get(self, work_item_id: str) -> Specification:
        return self._repository.get(work_item_id)


    def approve(self, work_item_id: str) -> Specification:
        current = self.get(work_item_id)
        current_status = SpecificationStatus(current["status"])
        if current_status == SpecificationStatus.DRAFT:
            return current
        if SpecificationStatus.APPROVED not in TRANSITIONS[current_status]:
            raise SpecificationConflictError(f"Cannot transition specification for work item {work_item_id} from {current_status.value} to {SpecificationStatus.APPROVED.value}")
        return self._repository.approve(work_item_id)


    def _build_specification(self, item: dict[str, Any]) -> Specification:
        try:
            work_item_id = item["workItemId"]
        except KeyError:
            raise SpecificationValidationError("Missing required field: workItemId")

        allowed = COMMON_INPUT_FIELDS
        unexpected = sorted(set(item) - allowed)
        if unexpected:
            raise SpecificationValidationError(
                f"Creation input contains unsupported fields: {', '.join(unexpected)}"
            )

        record: Specification = {
            "workItemId": work_item_id,
            "created": self._today().isoformat(),
            "status": SpecificationStatus.DRAFT.value
        }
        for field in ("summary", "acceptanceCriteria", "architecturalSummary", "keyDesignDecisions", "apiContracts", "databaseSchema", "uiComponents", "testingRequirements", "tasks", "crossTaskIntegrationPoints", "openQuestionsAndRisks"):
            if field in item:
                record[field] = item[field]

        return record