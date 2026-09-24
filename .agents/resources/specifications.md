# Specifications

This document defines the specification semantics and agent-facing operations for the AI Software Factory. Agents must use `python -m tools.work_items`; persistence is an implementation detail and must never be read or modified directly.

## Purpose

A specification is the architectural design and implementation plan for a user story or chore work item. It captures design decisions and a discrete set of scoped tasks before the ADLC workflow creates implementation handoffs. Integration points denote how the tasks are then brought together into a coherent changeset.

Specifications are stored as the `specification` property nested inside a work-item document on the Kanban board. Agents should treat that as an adapter detail. The durable contract is the work-item identity, type, required fields, status values, and lifecycle transitions. A future store, such as SQLite, must preserve those semantics even if paths and filenames are replaced by queries and records.

## Identity

Specifications have a 1-1 relationship to a `user-story` or `chore` work item. As such, a specification can be uniquely identified by a work item id.

- Request IDs are sequential five-digit numbers starting at `00001`.
- Work-item IDs use `{request-id}-{work-item-sequence}`, where `work-item-sequence` starts at `1` for each request, for example `00001-1`.
- Acceptance criteria on user stories and chores use `{work-item-id}.{criterion-sequence}`, for example `00001-1.1`.
- IDs remain stable across storage migrations.

## Status Model

Each specification has one lifecycle status.

| Status field | Meaning |
| --- | --- |
| `draft` | The specification has been drawn up by the architect and is ready for human review. |
| `approved` | The specification has been reviewed and approved and is ready for implementation. |

The `Status` field is the storage-independent lifecycle value. Future adapters must expose the same lifecycle states.

## State Management Process

1. The `software-architect` agent creates the new specification with status `draft` and adds it to the work item document.
2. The agent presents the specification for human review.
3. If any changes are requested the agent modifies the specification content accordingly (the status must remain at `draft`) and returns to step 2.
4. At human approval, the agent changes the status to `approved`.

The only allowed transition is `draft -> approved`. Once the specification is approved it becomes immutable.

## Tasks

Tasks define the units of work required to implement the specification. A specification can be broken down into one or more tasks. Tasks can be split by technology stack/service layer (e.g. `dotnet-backend`, `react-frontend`) or vertical feature slice (e.g. `employees` and `contracts`). Multiple tasks should only be created if they are independent and can be implemented and unit tested in isolation from the other tasks (assuming dependencies completed). Tasks should be recorded in order of intended implementation and any dependencies recorded, for example `api-contract`, `web-api` (depends on `api-contract`), `ui` (depends on `api-contract`). Integration tests are implemented once all tasks are complete.

## Operations

Commands emit a JSON success envelope to stdout. Failures emit a structured JSON error to stderr and return nonzero. A failed command is a blocker; never bypass it with direct storage access.

Install the repository tooling once with `python -m pip install -r requirements-dev.txt` before calling these operations.

```powershell
python -m tools.work_items add_spec 00001-1 --input request.json
python -m tools.work_items revise_spec 00001-1 --input request.json
python -m tools.work_items get_spec 00001-1
python -m tools.work_items approve_spec 00001-1
```

Creation input is a specification JSON object. Every item requires `summary`, `architecturalSummary` and `tasks`; `keyDesignDecisions` should be provided where important trade-offs exist. The arrays `apiContracts`, `databaseSchema`, `uiComponents`, `testingRequirements`, `crossTaskIntegrationPoints` and `openQuestionsAndRisks` should be populated where relevant to the implementation, otherwise passed as an empty array. `tasks` is required and is a list of all implementation work to be carried out. Each task must be given a unique kebab case identifier which succinctly describes the task, e.g. `dotnet-api`. Do not provide `workItemId`, `created`, or `status`; those are service-owned fields.

Software Architect may call `add_spec`, `revise_spec`, `get-spec` and `approve-spec`. Other agents may call `get_spec` only.

## Authoring Rules

- Write from the implementor's perspective and keep each task independently understandable.
- Split a specification into as many independently deliverable tasks as needed.
- Acceptance criteria must be testable without relying on conversation history.
- Do not change any specification details once approved.