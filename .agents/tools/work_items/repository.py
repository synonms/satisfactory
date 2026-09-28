"""Storage contract for work-item repositories."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Protocol

from .models import WorkItem, IntakeActivity, Specification, Task, TaskActivity

RequestFactory = Callable[[str], Sequence[WorkItem]]


class WorkItemRepository(Protocol):
    def create(self, factory: RequestFactory) -> list[WorkItem]: ...

    def get(self, work_item_id: str) -> WorkItem: ...

    def list(self) -> list[WorkItem]: ...

    def update_status(self, work_item_id: str, expected_status: str, status: str) -> WorkItem: ...

    def set_plan(
        self,
        work_item_id: str,
        specification: Specification | None,
        tasks: list[Task],
    ) -> dict[str, Any]: ...

    def get_plan(self, work_item_id: str) -> dict[str, Any]: ...

    def approve_plan(self, work_item_id: str) -> dict[str, Any]: ...

    def get_spec(self, work_item_id: str) -> Specification: ...

    def get_task(self, work_item_id: str, task_id: str) -> Task: ...

    def record_activity(
        self,
        work_item_id: str,
        task_id: str,
        activity: TaskActivity,
        failure_signature: str | None = None,
    ) -> Task: ...

    def record_intake(self, work_item_id: str, activity: IntakeActivity) -> WorkItem: ...