"""JSON-file implementation of the specification repository."""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from filelock import FileLock, Timeout

from .models import (
    Specification,
    SpecificationConflictError,
    SpecificationNotFoundError,
    SpecificationStorageError,
    SpecificationValidationError,
)
from .validation import SpecificationValidator

WORK_ITEM_ID = re.compile(r"^(?P<request>[0-9]{5})-[1-9][0-9]*$")


class JsonFileSpecificationRepository:
    def __init__(self, board_root: Path, validator: SpecificationValidator | None = None) -> None:
        self._board_root = board_root
        self._validator = validator or SpecificationValidator()

    def create(self, specification: Specification) -> Specification:
        if not specification:
            raise SpecificationValidationError("A request must contain a specification")

        self._validator.validate(specification)

        status = specification["status"]        
        if status != "draft":
            raise SpecificationValidationError("New specification must have status 'draft'")

        work_item_id = specification["workItemId"]
        work_item_directory = self._dir_path_for(work_item_id)
        work_item_directory.mkdir(parents=True, exist_ok=True)
        specification_path = self._file_path_for(work_item_id)

        with self._lock():
            self._write_atomic(specification_path, specification)
            return specification

    def update(self, specification: Specification) -> Specification:
        if not specification:
            raise SpecificationValidationError("A request must contain a specification")

        self._validator.validate(specification)

        work_item_id = specification["workItemId"]

        existing_work_item = self.get(work_item_id)
        if existing_work_item["status"] != "draft":
            raise SpecificationConflictError(f"Specification for work item {work_item_id} status is not draft")

        specification_path = self._file_path_for(work_item_id)

        with self._lock():
            self._write_atomic(specification_path, specification)
            return specification

    def get(self, work_item_id: str) -> Specification:
        path = self._file_path_for(work_item_id)
        if not path.is_file():
            raise SpecificationNotFoundError(f"Specification for work item {work_item_id} was not found")
        return self._read(path)

    def approve(self, work_item_id: str) -> Specification:
        with self._lock():
            specification = self.get(work_item_id)
            if specification["status"] != "draft":
                raise SpecificationConflictError(f"Specification for work item {work_item_id} status is not draft")
            specification["status"] = "approved"
            self._validator.validate(specification)
            self._write_atomic(self._file_path_for(work_item_id), specification)
            return specification

    def _dir_path_for(self, work_item_id: str) -> Path:
        match = WORK_ITEM_ID.fullmatch(work_item_id)
        if not match:
            raise SpecificationValidationError(f"Invalid work-item ID: {work_item_id}")
        request_id = work_item_id.split("-", maxsplit=1)[0]
        return self._board_root / request_id / work_item_id

    def _file_path_for(self, work_item_id: str) -> Path:
        return self._dir_path_for(work_item_id) / f"{work_item_id}.specification.json"

    def _read(self, path: Path) -> Specification:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SpecificationStorageError(f"Cannot read {path}: {error}") from error
        if not isinstance(value, dict):
            raise SpecificationValidationError(f"Work item in {path} must be a JSON object")
        self._validator.validate(value)
        return value

    def _write_atomic(self, path: Path, value: Specification) -> None:
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
            raise SpecificationStorageError(f"Cannot write {path}: {error}") from error

    @contextmanager
    def _lock(self) -> Iterator[None]:
        lock_path = self._board_root / ".work-items.lock"
        try:
            with FileLock(lock_path, timeout=30):
                yield
        except (OSError, Timeout) as error:
            raise SpecificationStorageError(f"Cannot lock work-item store: {error}") from error
