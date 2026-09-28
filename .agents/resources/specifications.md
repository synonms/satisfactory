# Specifications

This document defines the specification semantics and agent-facing operations for the AI Software Factory. Agents must use `python -m tools.work_items`; persistence is an implementation detail and must never be read or modified directly.

## Purpose

A specification is the architectural design for a `user-story` or `chore` work item. It captures design decisions and integration points. Execution detail belongs on the tasks, not here.

**Only `user-story` and `chore` work items have a specification.** `bug` and `documentation` work items are planned with tasks alone; the service and the schema both reject a specification on those types.

Specifications are stored as the `specification` property nested inside a work-item document on the Kanban board. Agents should treat that as an adapter detail. The durable contract is the work-item identity, type, required fields, status values, and lifecycle transitions. A future store, such as SQLite, must preserve those semantics even if paths and filenames are replaced by queries and records.

## Identity

Specifications have a 1-1 relationship to a `user-story` or `chore` work item. As such, a specification can be uniquely identified by a work item id.

- Request IDs are sequential five-digit numbers starting at `00001`.
- Work-item IDs use `{request-id}-{work-item-sequence}`, where `work-item-sequence` starts at `1` for each request, for example `00001-1`.
- Acceptance criteria on user stories and chores use `{work-item-id}.{criterion-sequence}`, for example `00001-1.1`.
- IDs remain stable across storage migrations.

## Status Model

A specification does not have an independent lifecycle. It is part of the task plan and follows `planStatus`.

| `planStatus` | Meaning |
| --- | --- |
| `null` | No plan has been authored yet. |
| `draft` | The architect has authored the plan and it is ready for human review. |
| `approved` | A human approved the plan. Tasks may now be dispatched. |

The specification `status` field mirrors `planStatus` and is set by the service. Never set it by hand.

## State Management Process

1. The `software-architect` authors the specification and tasks with `add_spec`. `planStatus` becomes `draft`.
2. The agent presents the plan for human review.
3. If changes are requested the agent calls `revise_spec`. `planStatus` stays `draft`.
4. At explicit human approval the agent calls `approve_plan`.

The only allowed transition is `draft -> approved`. Once approved the plan and specification are immutable, and no task may record activity before approval.

## Tasks

Tasks are stored on the work item, not inside the specification document. Authoring rules, phases, owners, state machines, and operations are defined in `.agents/resources/tasks.md`.

## Operations

Commands emit a JSON success envelope to stdout. Failures emit a structured JSON error to stderr and return nonzero. A failed command is a blocker; never bypass it with direct storage access.

Install the repository tooling once with `python -m pip install -r requirements-dev.txt` before calling these operations.

```powershell
python -m tools.work_items add_spec 00001-1 --input request.json
python -m tools.work_items revise_spec 00001-1 --input request.json
python -m tools.work_items get_spec 00001-1
python -m tools.work_items get_plan 00001-1
python -m tools.work_items approve_plan 00001-1
```

Input for `add_spec` and `revise_spec` is a JSON object with two properties:

- `specification`: The specification JSON object. Every item requires `summary` and `architecturalSummary`. `keyDesignDecisions` should be provided where important trade-offs exist. The arrays `apiContracts`, `databaseSchema`, `uiComponents`, `crossTaskIntegrationPoints` and `openQuestionsAndRisks` should be populated where relevant, otherwise passed as an empty array. Do not provide `workItemId`, `created`, or `status`; those are service-owned fields.
- `tasks`: A non-empty array of task objects as defined in `.agents/schemas/task.schema.json`.

Testing expectations are not part of the specification. Put them in the `verification` field of the relevant `unit-test` or `integration-test` task.

Software Architect may call `add_spec`, `revise_spec`, `add_tasks`, `revise_tasks`, `get_spec`, `get_plan` and `approve_plan`. Other agents may call `get_spec` and `get_plan` only.

## Authoring Rules

- Describe the architecture, not the steps. The steps are the tasks.
- Reference existing architecture and conventions rather than restating them.
- Make cross-task contracts explicit so agents working on different tasks do not diverge.
- Do not change any specification details once the plan is approved.