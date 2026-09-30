"""Aggregate work-item metrics while flagging invalid historical measurements."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from .models import WorkItem


PLACEHOLDER_MODELS = {"", "unknown", "n/a", "na", "none", "null", "model", "tbd"}


def build_metrics_report(work_items: Sequence[WorkItem]) -> dict[str, Any]:
    phase_totals: dict[str, dict[str, Any]] = defaultdict(_new_totals)
    agent_totals: dict[str, dict[str, Any]] = defaultdict(_new_totals)
    work_item_rows: list[dict[str, Any]] = []
    invalid_runs: list[dict[str, Any]] = []
    totals = _new_totals()

    for work_item in work_items:
        valid_item = _new_totals()
        run_count = 0
        for intake in work_item.get("intake", []):
            run_count += 1
            _accumulate_run(
                intake,
                work_item["id"],
                "intake",
                valid_item,
                phase_totals["intake"],
                agent_totals,
                totals,
                invalid_runs,
            )

        for task in work_item.get("tasks", []):
            for activity in task.get("history", []):
                run_count += 1
                _accumulate_run(
                    activity,
                    work_item["id"],
                    task.get("phase", "unknown"),
                    valid_item,
                    phase_totals[str(task.get("phase", "unknown"))],
                    agent_totals,
                    totals,
                    invalid_runs,
                )

        work_item_rows.append(
            {
                "workItemId": work_item["id"],
                "type": work_item["type"],
                "status": work_item["status"],
                "agentRuns": run_count,
                "validMetricRuns": valid_item["runs"],
                "invalidMetricRuns": run_count - valid_item["runs"],
                "measured": valid_item,
                "recordedTotals": work_item.get("execution", {}).get("totals"),
            }
        )

    return {
        "workItemCount": len(work_items),
        "agentRuns": sum(row["agentRuns"] for row in work_item_rows),
        "measured": totals,
        "byPhase": dict(sorted(phase_totals.items())),
        "byAgent": dict(sorted(agent_totals.items())),
        "workItems": work_item_rows,
        "invalidRuns": invalid_runs,
    }


def _new_totals() -> dict[str, int | float]:
    return {"runs": 0, "durationSeconds": 0.0, "totalTokens": 0, "estimatedCostUsd": 0.0}


def _accumulate_run(
    activity: Mapping[str, Any],
    work_item_id: str,
    phase: str,
    work_item_totals: dict[str, int | float],
    phase_totals: dict[str, int | float],
    agent_totals: dict[str, dict[str, Any]],
    overall_totals: dict[str, int | float],
    invalid_runs: list[dict[str, Any]],
) -> None:
    metrics = activity.get("metrics", {})
    reason = _invalid_metrics_reason(metrics)
    if reason:
        invalid_runs.append(
            {
                "workItemId": work_item_id,
                "phase": phase,
                "agent": activity.get("agent", "unknown"),
                "iteration": activity.get("iteration"),
                "reason": reason,
            }
        )
        return

    agent = str(activity.get("agent", "unknown"))
    for target in (work_item_totals, phase_totals, agent_totals[agent], overall_totals):
        target["runs"] += 1
        target["durationSeconds"] += float(metrics["durationSeconds"])
        target["totalTokens"] += int(metrics["totalTokens"])
        target["estimatedCostUsd"] += float(metrics["estimatedCostUsd"])


def _invalid_metrics_reason(metrics: Any) -> str | None:
    if not isinstance(metrics, Mapping):
        return "metrics object is missing"
    try:
        input_tokens = metrics["inputTokens"]
        output_tokens = metrics["outputTokens"]
        total_tokens = metrics["totalTokens"]
        duration = metrics["durationSeconds"]
        cost = metrics["estimatedCostUsd"]
        model = metrics["model"]
    except KeyError as error:
        return f"missing field {error.args[0]}"

    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in (input_tokens, output_tokens, total_tokens)):
        return "token counts must be positive integers"
    if total_tokens != input_tokens + output_tokens:
        return "totalTokens does not equal inputTokens + outputTokens"
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
        return "durationSeconds must be positive"
    if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
        return "estimatedCostUsd must be non-negative"
    if not isinstance(model, str) or model.strip().lower() in PLACEHOLDER_MODELS:
        return "model is missing or a placeholder"
    return None