# Tasks

This document defines task semantics and task operations for the AI Software Factory. Tasks are first-class entities nested within a work item and are persisted through `python -m tools.work_items`.

## Purpose

A task is the smallest independently handoffable ADLC unit. It captures:

- Implementation scope and ownership
- Delivery dependencies and touched paths
- Task runtime state and attempt counters
- Activity history for every handoff iteration
- Execution metrics for observability and no-progress detection

Tasks are stored in the work-item `tasks` array and validated by `.agents/schemas/task.schema.json`.

## Relationship to Work Items and Specifications

- A work item may contain zero or more tasks while `new`.
- For all work item types, `add_spec` and `revise_spec` require a non-empty `tasks` array alongside the specification payload.

## Task Contract

Each task contains planning and lifecycle fields.

Planning fields:
- `id`: Unique kebab-case task identifier.
- `owner`: Responsible implementing agent.
- `scope`: What this task covers.
- `affectedPaths`: Paths expected to be modified.
- `contracts`: Cross-task contract touchpoints.
- `dependencies`: Task IDs that must complete first.
- `acceptanceCriteriaCovered`: Requirement IDs this task satisfies.

Lifecycle fields:
- `state`: `not-started`, `implemented`, `tests-passing`, `tests-failing`, `blocked`.
- `implementAttempts`: Number of implementation attempts.
- `testAttempts`: Number of test attempts.
- `lastFailureSignature`: Stable signature of latest failing test set.
- `latestArtifact`: Most recent artifact path.
- `history`: Chronological activity list.

## Activity Contract

Each history entry records one handoff/action for the task:

- `ts`: Timestamp in UTC.
- `iteration`: Task-scoped iteration number.
- `agent`: Agent producing the handoff.
- `technology`: Optional technology context.
- `outcome`: One of `implemented`, `passed`, `failed`, `blocked`, `Passed`, `Failed`, `Blocked`.
- `result`: Free-text outcome summary.
- `artifact`: Optional artifact path.
- `filesChanged`: Changed files for that iteration.
- `nextOwner`: Next owning agent.
- `metrics`: Optional run metrics:
  - `durationSeconds`
  - `inputTokens`
  - `outputTokens`
  - `totalTokens`
  - `model`
  - `estimatedCostUsd`

## Operations

Commands emit a JSON success envelope to stdout. Failures emit structured JSON to stderr and return nonzero.

Install tools once:

```powershell
python -m pip install -r requirements-dev.txt
```

Read a task:

```powershell
python -m tools.work_items get_task 00001-1 dotnet-api
```

Record activity:

```powershell
python -m tools.work_items record_activity 00001-1 dotnet-api --input activity.json
```

`activity.json` must be a task activity payload. The service appends it to task history and updates task state/attempt counters.

## Authoring Rules

- Keep task scope independently understandable.
- Keep IDs stable after work begins.
- Record every implementing-agent handoff through `record_activity`.
- Do not edit persisted task JSON directly.
