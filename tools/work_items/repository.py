"""Storage contract for work-item repositories."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from .models import WorkItem, Specification

RequestFactory = Callable[[str], Sequence[WorkItem]]


class WorkItemRepository(Protocol):
    def create(self, factory: RequestFactory) -> list[WorkItem]: ...

    def get(self, work_item_id: str) -> WorkItem: ...

    def list(self) -> list[WorkItem]: ...

    def update_status(self, work_item_id: str, expected_status: str, status: str) -> WorkItem: ...

    def add_spec(self, work_item_id: str, specification: Specification) -> Specification: ...

    def revise_spec(self, work_item_id: str, specification: Specification) -> Specification: ...

    def get_spec(self, work_item_id: str) -> Specification: ...

    def approve_spec(self, work_item_id: str) -> Specification: ...