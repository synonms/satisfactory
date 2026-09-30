"""Selects the next dispatchable task from a work item's task graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tools.work_items import phases
from tools.work_items.models import PlanStatus, TaskPhase, TaskState, WorkItem

DISPATCHABLE_STATES = frozenset(
    {
        TaskState.NOT_STARTED,
        TaskState.IN_PROGRESS,
        TaskState.REWORK_REQUIRED,
        TaskState.TESTS_FAILING,
        TaskState.CHANGES_REQUESTED,
        TaskState.REJECTED,
    }
)


@dataclass(frozen=True)
class Dispatch:
    work_item_id: str
    task_id: str
    phase: str
    owner: str
    state: str
    iteration: int
    scope: str
    technology: str | None = None
    deliverables: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    affected_paths: list[str] = field(default_factory=list)
    contracts: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    plan_policy: dict[str, Any] | None = None
    repository_context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "workItemId": self.work_item_id,
            "taskId": self.task_id,
            "phase": self.phase,
            "owner": self.owner,
            "state": self.state,
            "iteration": self.iteration,
            "scope": self.scope,
            "technology": self.technology,
            "deliverables": self.deliverables,
            "verification": self.verification,
            "affectedPaths": self.affected_paths,
            "contracts": self.contracts,
            "acceptanceCriteriaCovered": self.acceptance_criteria,
            "dependencies": self.dependencies,
            "planPolicy": self.plan_policy,
            "repositoryContext": self.repository_context,
        }


def plan_status(work_item: WorkItem) -> str | None:
    return work_item.get("planStatus")


def is_dispatchable(task: dict[str, Any], tasks_by_id: dict[str, dict[str, Any]]) -> bool:
    if TaskState(task["state"]) not in DISPATCHABLE_STATES:
        return False
    return all(
        phases.is_terminal_success(TaskState(tasks_by_id[dependency]["state"]))
        for dependency in task.get("dependencies", [])
    )


def next_task(work_item: WorkItem) -> Dispatch | None:
    """First task in plan order whose dependencies are all complete. None when nothing is ready."""
    if plan_status(work_item) != PlanStatus.APPROVED.value:
        return None

    tasks = work_item.get("tasks", [])
    tasks_by_id = {task["id"]: task for task in tasks}

    for task in tasks:
        if not is_dispatchable(task, tasks_by_id):
            continue
        return Dispatch(
            work_item_id=work_item["id"],
            task_id=task["id"],
            phase=task["phase"],
            owner=phases.owner_for(TaskPhase(task["phase"])),
            state=task["state"],
            iteration=len(task.get("history", [])) + 1,
            scope=task.get("scope", ""),
            technology=task.get("technology"),
            deliverables=list(task.get("deliverables", [])),
            verification=list(task.get("verification", [])),
            affected_paths=list(task.get("affectedPaths", [])),
            contracts=list(task.get("contracts", [])),
            acceptance_criteria=list(task.get("acceptanceCriteriaCovered", [])),
            dependencies=list(task.get("dependencies", [])),
            plan_policy=work_item.get("planPolicy"),
            repository_context=_repository_context_for_task(work_item, task),
        )
    return None


def is_complete(work_item: WorkItem) -> bool:
    tasks = work_item.get("tasks", [])
    return bool(tasks) and all(
        phases.is_terminal_success(TaskState(task["state"])) for task in tasks
    )


def blocked_tasks(work_item: WorkItem) -> list[dict[str, Any]]:
    return [task for task in work_item.get("tasks", []) if task["state"] == TaskState.BLOCKED.value]


def _repository_context_for_task(
    work_item: WorkItem, task: dict[str, Any]
) -> dict[str, Any] | None:
    context = work_item.get("repositoryContext")
    if not isinstance(context, dict):
        return None
    technology = task.get("technology")
    if not technology or context.get("technology", "").lower() != technology.lower():
        return None

    affected_paths = [_normalize_scope_path(path) for path in task.get("affectedPaths", [])]
    projects = [
        project
        for project in context.get("projects", [])
        if not affected_paths
        or any(
            _paths_overlap(_normalize_scope_path(project.get("path", "")), path)
            or _paths_overlap(_normalize_scope_path(project.get("path", "")).rsplit("/", 1)[0], path)
            for path in affected_paths
        )
    ]
    return {
        "technology": context["technology"],
        "scopePaths": context.get("scopePaths", []),
        "facts": context.get("facts", []),
        "projects": projects,
        "resources": context.get("resources", []),
    }


def _normalize_scope_path(path: str) -> str:
    return path.replace("\\", "/").removesuffix("/**").rstrip("/").lower()


def _paths_overlap(left: str, right: str) -> bool:
    return bool(left and right) and (
        left == right or left.startswith(right + "/") or right.startswith(left + "/")
    )
