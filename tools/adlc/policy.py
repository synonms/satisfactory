"""Failsafes that stop a task graph looping without progress."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from tools.work_items.models import WorkItem

TEST_PATH = re.compile(r"(^|[\\/])tests?[\\/]|\.tests?\.|(^|[\\/])[^\\/]*[._-]tests?\.", re.IGNORECASE)

READ_ONLY_AGENTS = frozenset({"reviewer", "implementation-validator"})


@dataclass(frozen=True)
class FailsafeViolation:
    code: str
    message: str
    task_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "taskId": self.task_id}


def check_failsafes(work_item: WorkItem, task: dict[str, Any] | None = None) -> list[FailsafeViolation]:
    budget = work_item["execution"]["budget"]
    violations: list[FailsafeViolation] = []

    if budget["totalAgentRuns"] >= budget["maxTotalAgentRuns"]:
        violations.append(
            FailsafeViolation(
                "run-budget-exhausted",
                f"Total agent runs {budget['totalAgentRuns']} reached the cap of "
                f"{budget['maxTotalAgentRuns']}",
            )
        )
    if budget["reviewLoops"] >= budget["maxReviewLoops"]:
        violations.append(
            FailsafeViolation(
                "review-loops-exhausted",
                f"Review remediation loops reached the cap of {budget['maxReviewLoops']}",
            )
        )
    if budget["validationLoops"] >= budget["maxValidationLoops"]:
        violations.append(
            FailsafeViolation(
                "validation-loops-exhausted",
                f"Validation remediation loops reached the cap of {budget['maxValidationLoops']}",
            )
        )

    if task is None:
        return violations

    if task["attempts"] >= budget["maxTaskAttempts"]:
        violations.append(
            FailsafeViolation(
                "task-attempts-exhausted",
                f"Task {task['id']} reached the attempt cap of {budget['maxTaskAttempts']}",
                task["id"],
            )
        )
    if _has_no_progress(task):
        violations.append(
            FailsafeViolation(
                "no-progress",
                f"Task {task['id']} produced an identical failure signature twice in a row",
                task["id"],
            )
        )
    return violations


def check_ownership(agent: str, files_changed: list[str]) -> list[FailsafeViolation]:
    """Stops an engineer fixing a test, or QA fixing production code, to force a pass."""
    if agent in READ_ONLY_AGENTS and files_changed:
        return [
            FailsafeViolation(
                "ownership-violation",
                f"{agent} must not modify files but changed: {', '.join(sorted(files_changed))}",
            )
        ]

    if agent == "software-engineer":
        offending = [path for path in files_changed if TEST_PATH.search(path)]
        if offending:
            return [
                FailsafeViolation(
                    "ownership-violation",
                    "software-engineer must not modify tests but changed: "
                    + ", ".join(sorted(offending)),
                )
            ]

    if agent == "quality-assurance-engineer":
        offending = [path for path in files_changed if not TEST_PATH.search(path)]
        if offending:
            return [
                FailsafeViolation(
                    "ownership-violation",
                    "quality-assurance-engineer must not modify production code but changed: "
                    + ", ".join(sorted(offending)),
                )
            ]

    return []


def _has_no_progress(task: dict[str, Any]) -> bool:
    signature = task.get("lastFailureSignature")
    return signature is not None and signature == task.get("previousFailureSignature")
