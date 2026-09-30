"""Advisory checks for avoidable handoffs in a proposed work-item plan."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from .models import WorkItem


def lint_plan(work_item: WorkItem, payload: Mapping[str, Any]) -> dict[str, Any]:
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, Sequence) or isinstance(tasks, (str, bytes)):
        raise ValueError("Plan tasks must be an array")

    task_list = [task for task in tasks if isinstance(task, Mapping)]
    phases = Counter(str(task.get("phase", "unknown")) for task in task_list)
    policy = payload.get("planPolicy") or work_item.get("planPolicy")
    policy_values = policy if isinstance(policy, Mapping) else {}
    warnings: list[dict[str, str]] = []

    def warn(code: str, message: str) -> None:
        warnings.append({"code": code, "message": message})

    if not policy_values:
        warn("missing-plan-policy", "Classify plan risk and select lean, balanced, or strict mode.")
    else:
        risk = policy_values.get("risk")
        mode = policy_values.get("mode")
        if (
            not isinstance(risk, str)
            or risk not in {"low", "medium", "high"}
            or not isinstance(mode, str)
            or mode not in {"lean", "balanced", "strict"}
        ):
            warn("invalid-plan-policy", "Use a supported risk and planning mode value.")
        if risk == "high" and mode == "lean":
            warn("high-risk-lean", "High-risk work should use balanced or strict planning.")
        if risk == "low" and mode == "strict":
            warn("low-risk-strict", "Consider lean mode unless the extra handoffs address a stated risk.")
        if mode == "lean" and len(task_list) > 4:
            warn(
                "lean-handoff-budget",
                f"Lean plans normally need at most 4 task handoffs; this plan has {len(task_list)}.",
            )

    implementation_tasks = [task for task in task_list if task.get("phase") == "implementation"]
    test_tasks = [
        task for task in task_list if task.get("phase") in {"unit-test", "integration-test"}
    ]
    review_tasks = [task for task in task_list if task.get("phase") == "review"]
    if not any(task.get("phase") == "validation" for task in task_list):
        warn("missing-validation", "Every plan must include a final validation task.")
    if len(test_tasks) > 1 and policy_values.get("mode") in {"lean", "balanced"}:
        warn(
            "fragmented-testing",
            "Consider one QA task covering the cohesive change instead of separate test handoffs.",
        )
    if len(review_tasks) > 1 and policy_values.get("mode") in {"lean", "balanced"}:
        warn(
            "fragmented-review",
            "Consider one integrated review after tests unless intermediate review addresses a named risk.",
        )

    dependencies = {
        str(task.get("id")): [str(value) for value in task.get("dependencies", [])]
        for task in task_list
    }
    dependents = {str(task.get("id")): [] for task in task_list}
    for task in task_list:
        task_id = str(task.get("id"))
        for dependency in task.get("dependencies", []):
            dependents.setdefault(str(dependency), []).append(task_id)
    phase_by_id = {str(task.get("id")): task.get("phase") for task in task_list}
    for review in review_tasks:
        if test_tasks and not _depends_on_phase(
            str(review.get("id")), "unit-test", dependencies, phase_by_id
        ) and not _depends_on_phase(
            str(review.get("id")), "integration-test", dependencies, phase_by_id
        ):
            warn(
                "review-before-tests",
                f"Review task {review.get('id')} does not depend on a QA test task.",
            )
    for implementation in implementation_tasks:
        if (
            work_item.get("type") in {"user-story", "chore"}
            and not _reaches_phase(
                str(implementation.get("id")), "review", dependents, phase_by_id
            )
        ):
            warn(
                "implementation-without-review",
                f"Implementation task {implementation.get('id')} has no downstream review task.",
            )

    criteria = {
        str(criterion.get("id"))
        for criterion in work_item.get("acceptanceCriteria", [])
        if isinstance(criterion, Mapping) and criterion.get("id")
    }
    covered = {
        str(identifier)
        for task in task_list
        for identifier in task.get("acceptanceCriteriaCovered", [])
    }
    missing = sorted(criteria - covered)
    if missing:
        warn("uncovered-criteria", "No task maps to acceptance criteria: " + ", ".join(missing))

    return {
        "workItemId": work_item["id"],
        "estimatedAgentRuns": len(task_list),
        "phaseCounts": dict(sorted(phases.items())),
        "warnings": warnings,
    }


def _reaches_phase(
    task_id: str,
    target_phase: str,
    dependents: dict[str, list[str]],
    phase_by_id: dict[str, Any],
) -> bool:
    seen: set[str] = set()
    pending = list(dependents.get(task_id, []))
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        if phase_by_id.get(current) == target_phase:
            return True
        pending.extend(dependents.get(current, []))
    return False


def _depends_on_phase(
    task_id: str,
    target_phase: str,
    dependencies: dict[str, list[str]],
    phase_by_id: dict[str, Any],
) -> bool:
    seen: set[str] = set()
    pending = list(dependencies.get(task_id, []))
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        if phase_by_id.get(current) == target_phase:
            return True
        pending.extend(dependencies.get(current, []))
    return False