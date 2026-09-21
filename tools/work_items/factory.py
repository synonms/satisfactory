"""Composition root for work-item services and storage backends."""

from __future__ import annotations

import os
from pathlib import Path

from .json_repository import JsonFileWorkItemRepository
from .models import WorkItemValidationError
from .service import WorkItemService


def create_service(
    board_root: Path = Path("board"), backend: str | None = None
) -> WorkItemService:
    selected_backend = backend or os.environ.get("SATISFACTORY_WORK_ITEM_BACKEND", "json")
    if selected_backend == "json":
        return WorkItemService(JsonFileWorkItemRepository(board_root))
    raise WorkItemValidationError(f"Unsupported work-item backend: {selected_backend}")