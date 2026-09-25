# Work Items

This document defines the work-item semantics and agent-facing operations for the AI Software Factory. Agents must use `python -m tools.work_items`; persistence is an implementation detail and must never be read or modified directly.

## Purpose

A work item is the stakeholder-readable unit of requested change. It captures scope, type, acceptance or validation requirements, and lifecycle state before the ADLC workflow creates implementation handoffs. A single change request may be broken down into multiple work items, but only if the work items are entirely independent and can be implemented in isolation.

Tasks are first-class children of a work item and are stored directly on the work-item document. Task definitions, task state, and task activity history are all part of the same persisted contract.

Work items are currently stored as JSON files on the Kanban board, but agents should treat that as an adapter detail. The durable contract is the work-item identity, type, required fields, status values, and lifecycle transitions. A future store, such as SQLite, must preserve those semantics even if paths and filenames are replaced by queries and records.

## Types

Each work item has exactly one type:

| Type | Slug | Use when |
| --- | --- | --- |
| User Story | `user-story` | New functionality or enhancements that deliver direct user value |
| Bug | `bug` | A defect in existing functionality that needs correction |
| Chore | `chore` | Maintenance, refactoring, infrastructure, or technical debt without direct user-facing value |
| Documentation | `documentation` | Creating, correcting, or updating repository documentation |

 Order of importance is `User Story` > `Chore` > `Bug` > `Documentation`. If a request for change contains work that spans multiple types and the work cannot be cleanly split into independent work items, then create a singular work item using the category of higher importance. For example, if analysis shows that some elements are classified as `User Story` and some elements are `Bug`, then create a work item of type `User Story` which encapsulates both pieces of work.

## Identity

- Request IDs are sequential five-digit numbers starting at `00001`.
- Work-item IDs use `{request-id}-{work-item-sequence}`, where `work-item-sequence` starts at `1` for each request, for example `00001-1`.
- Acceptance criteria on user stories and chores use `{work-item-id}.{criterion-sequence}`, for example `00001-1.1`.
- The service assigns IDs, creation dates, and initial statuses. Callers must not supply them.
- IDs remain stable across storage migrations.

## Status Model

Each work item has one lifecycle status.

| Status field | Meaning |
| --- | --- |
| `new` | The work item has been accepted into the backlog and is ready for ADLC dispatch. |
| `in-progress` | The ADLC workflow has started and task execution is active. |
| `done` | Delivery has passed validation and received final human approval. |
| `blocked` | The workflow cannot proceed without human intervention. |

The `Status` field is the storage-independent lifecycle value. Future adapters must expose the same lifecycle states.

## State Management Process

1. The `triage` agent creates approved work items with status `new` through `create-request`.
2. The dispatcher starts the ADLC workflow and changes the status to `in-progress` through `change-status`.
3. Agents retrieve the work item through `get` and treat it as an immutable requirement source.
4. If a failsafe trips, the dispatcher changes the status to `blocked` and records escalations through task history activity.
5. At final human approval, the dispatcher changes the status to `done`.
6. During final-review remediation, the work item remains `in-progress`.
7. Scope additions are not added to an in-progress work item. Create a separate work item instead.

The only allowed transitions are `new -> in-progress`, `in-progress -> done`, and `in-progress -> blocked`. Repeating the current status is idempotent. The dispatcher is the only actor that changes lifecycle status after creation.

## Operations

Commands emit a JSON success envelope to stdout. Failures emit a structured JSON error to stderr and return nonzero. A failed command is a blocker; never bypass it with direct storage access.

Install the repository tooling once with `python -m pip install -r requirements-dev.txt` before calling these operations.

```powershell
python -m tools.work_items create-request --input request.json
python -m tools.work_items get 00001-1
python -m tools.work_items list --status new --type user-story --request-id 00001
python -m tools.work_items change-status 00001-1 in-progress
python -m tools.work_items get_task 00001-1 dotnet-api
python -m tools.work_items record_activity 00001-1 dotnet-api --input activity.json
```

Creation input is a JSON array in proposal order. Every item requires `type`, `request`, and `description`; `source` is optional. Do not provide `id`, `created`, or `status`.

- User stories and chores require `acceptanceCriteria`, an array of independently verifiable description strings.
- Every work item includes a service-managed `tasks` array. It is created as `[]` and later populated by task-authoring operations.
- User stories and chores include a `specification` field managed by the service. It is created as `null` and may later be set via `add_spec`, `revise_spec`, and `approve_spec`.
- Bugs require `stepsToReproduce`, `expectedResult`, and `actualResult`.
- Documentation items require `content` describing what must be produced or updated.

Triage may call `create-request`, `get`, and `list`. The dispatcher may call `get`, `list`, and `change-status`. Implementing agents may call `get`, `get_task`, and `record_activity`.

## Authoring Rules

- Write from the user's perspective and keep each work item independently understandable.
- Split a request into as many independently deliverable work items as needed.
- Acceptance criteria must be testable without relying on conversation history.
- Each work item has exactly one type.
- Do not change existing acceptance criteria or scope after ADLC work begins; create a new work item for new scope.