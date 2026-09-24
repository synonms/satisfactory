"""Storage contract for specification repositories."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .models import Specification

RequestFactory = Callable[[str], Specification]


class SpecificationRepository(Protocol):
    def create(self, specification: Specification) -> Specification: ...

    def update(self, specification: Specification) -> Specification: ...

    def get(self, work_item_id: str) -> Specification: ...

    def approve(self, work_item_id: str) -> Specification: ...