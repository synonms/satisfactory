"""Composition root for specification services and storage backends."""

from __future__ import annotations

import os
from pathlib import Path

from .json_repository import JsonFileSpecificationRepository
from .models import SpecificationValidationError
from .service import SpecificationService


def create_service(
    board_root: Path = Path("board"), backend: str | None = None
) -> SpecificationService:
    selected_backend = backend or os.environ.get("SATISFACTORY_SPECIFICATION_BACKEND", "json")
    if selected_backend == "json":
        return SpecificationService(JsonFileSpecificationRepository(board_root))
    raise SpecificationValidationError(f"Unsupported specification backend: {selected_backend}")