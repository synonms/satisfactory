"""Storage contract for work-item repositories."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from .models import WorkItem

RequestFactory = Callable[[str], Sequence[WorkItem]]


class WorkItemRepository(Protocol):
    def create_request(self, factory: RequestFactory) -> list[WorkItem]: ...

    def get(self, work_item_id: str) -> WorkItem: ...

    def list(self) -> list[WorkItem]: ...

    def update_status(
        self, work_item_id: str, expected_status: str, status: str
    ) -> WorkItem: ...