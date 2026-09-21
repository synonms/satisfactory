"""Domain values and errors for work-item management."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeAlias

WorkItem: TypeAlias = dict[str, Any]


class WorkItemType(str, Enum):
    USER_STORY = "user-story"
    CHORE = "chore"
    BUG = "bug"
    DOCUMENTATION = "documentation"


class WorkItemStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    BLOCKED = "blocked"


class WorkItemError(Exception):
    """Base class for errors that can be returned by the work-item CLI."""

    code = "work_item_error"


class WorkItemValidationError(WorkItemError):
    code = "validation_error"


class WorkItemNotFoundError(WorkItemError):
    code = "not_found"


class WorkItemConflictError(WorkItemError):
    code = "conflict"


class WorkItemStorageError(WorkItemError):
    code = "storage_error"