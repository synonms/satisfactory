"""Domain values and errors for specification management."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeAlias

Specification: TypeAlias = dict[str, Any]


class SpecificationStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"


class SpecificationError(Exception):
    """Base class for errors that can be returned by the specification CLI."""

    code = "specification_error"


class SpecificationValidationError(SpecificationError):
    code = "validation_error"


class SpecificationNotFoundError(SpecificationError):
    code = "not_found"


class SpecificationConflictError(SpecificationError):
    code = "conflict"


class SpecificationStorageError(SpecificationError):
    code = "storage_error"