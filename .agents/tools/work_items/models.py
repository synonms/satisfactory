"""Domain values and errors for work-item management."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeAlias

WorkItem: TypeAlias = dict[str, Any]
Specification: TypeAlias = dict[str, Any]
Task: TypeAlias = dict[str, Any]
TaskActivity: TypeAlias = dict[str, Any]
IntakeActivity: TypeAlias = dict[str, Any]

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

class SpecificationStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class PlanStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class TaskPhase(str, Enum):
    BUG_REPRO = "bug-repro"
    IMPLEMENTATION = "implementation"
    UNIT_TEST = "unit-test"
    INTEGRATION_TEST = "integration-test"
    REVIEW = "review"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"


class TaskState(str, Enum):
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    IMPLEMENTED = "implemented"
    REWORK_REQUIRED = "rework-required"
    TESTS_PASSING = "tests-passing"
    TESTS_FAILING = "tests-failing"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes-requested"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DOCUMENTED = "documented"
    BLOCKED = "blocked"


class TaskOutcome(str, Enum):
    IMPLEMENTED = "implemented"
    DOCUMENTED = "documented"
    PASSED = "passed"
    FAILED = "failed"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes-requested"
    VALIDATED = "validated"
    REJECTED = "rejected"
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



class SpecificationValidationError(WorkItemError):
    code = "validation_error"

class SpecificationNotFoundError(WorkItemError):
    code = "not_found"

class SpecificationConflictError(WorkItemError):
    code = "conflict"


class PlanValidationError(WorkItemError):
    code = "validation_error"


class PlanConflictError(WorkItemError):
    code = "conflict"


class PlanNotFoundError(WorkItemError):
    code = "not_found"


class TaskValidationError(WorkItemError):
    code = "validation_error"


class TaskNotFoundError(WorkItemError):
    code = "not_found"
