# Work Items

This document defines the work-item contract for the AI Software Factory. Agents must depend on the concepts and fields in this resource, not on the current storage implementation.

## Purpose

A work item is the stakeholder-readable unit of requested change. It captures scope, type, acceptance or validation requirements, and lifecycle state before the SDLC workflow creates implementation handoffs. A single change request may be broken down into multiple work items, but only if the work items are entirely independent and can be implemented in isolation.

Work items are currently stored as Markdown files on the Kanban board, but agents should treat that as an adapter detail. The durable contract is the work-item identity, type, required fields, status values, and lifecycle transitions. A future store, such as SQLite, must preserve those semantics even if paths and filenames are replaced by queries and records.

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
- The latest request ID is stored in `board/.id` while the Markdown-board adapter is in use.
- Work-item IDs use `{request-id}-{work-item-sequence}`, where `work-item-sequence` starts at `1` for each request, for example `00001-1`.
- Acceptance criteria on user stories and chores use `{work-item-id}.{criterion-sequence}`, for example `00001-1.1`.
- IDs must be stable across storage migrations. Do not derive identity from a filename once the work item has been created.

## Current Storage Adapter

The current implementation stores each work item as one Markdown file under `board/{request-id}/`:

```text
board/
  .id
  {request-id}/
    {work-item-id}.work-item.md
```

When creating work items, ensure `board/` and `board/{request-id}/` exist. If they do not then create them. Save new work items to `board/{request-id}/`.

Work item filenames use `{work-item-id}.work-item.md`, for example: `00001-1.work-item.md`.

Agents must locate a work item by ID, not by reconstructing its title. With the current adapter, search the board state folders for `board/{request-id}/{work-item-id}.work-item.md`.

## Status Model

The work-item file has a `Status` field. 

| Status field | Meaning |
| --- | --- |
| `New` | The work item has been accepted into the backlog and is ready for SDLC dispatch. |
| `In Progress` | The SDLC workflow has started and handoff state exists or is being created. |
| `Done` | Delivery has passed validation and received final human approval. |
| `Blocked` | The workflow cannot proceed without human intervention. |

The `Status` field is the storage-independent lifecycle value. Future adapters must expose the same lifecycle states.

## State Management Process

1. `triage` agent creates approved work-item tickets with `Status: New` in `board/{request-id}/`.
2. The orchestrator starts the SDLC workflow for a selected `New` item and creates `board/{request-id}/{work-item-id}/{work-item-id}.state.json` to track progress. The orchestrator updates `Status: In Progress`.
3. Agents read the work item as an immutable requirement source. They do not change the work-item status or move the work-item record.
4. If a failsafe trips or the workflow reaches a terminal blocker, the orchestrator sets `Status: Blocked` with the escalation recorded in `{work-item-id}.state.json`.
5. At the final human approval gate, the orchestrator sets `Status: Done`.
6. If final-review remediation is requested for an existing requirement, the work item remains `Status: In Progress` while the orchestrator routes remediation through `{work-item-id}.state.json`.
7. Scope additions are not added to an in-progress work item. Create a separate work item instead.

The orchestrator is the only actor that changes lifecycle state after creation. `/create-work-item` creates `New` work items; downstream agents treat work-item content as read-only.

## Schema and Validation

[The work item JSON Schema](../schemas/work-item.schema.json) is authoritative for required fields, types, nullability, allowed values, and additional-property rules. Install the development tools with `python -m pip install -r requirements-dev.txt`, then validate every existing control file before consuming it:

```sh
python -m check_jsonschema --schemafile .agents/schemas/work-item.schema.json board/{request-id}/{work-item-id}.work-item.json
```

The following fields are mandatory for all work items:

- **id**: {work-item-id}
- **type**: [user-story, chore, bug, documentation]
- **created**: {ISO-8601 timestamp or local date/time with timezone}
- **status**: [new, in-progress, done]
- **request**: {summary of the original request}

If the request originates from an Azure DevOps ticket then **source** must also be populated with the external work item URL.

The following fields are mandatory for `user story` and `chore` items:

- **acceptanceCriteria**: {Array of independently verifiable criterion written from the user's perspective}

The following fields are mandatory for `bug` items:

- **stepsToReproduce**: {Steps to reproduce issue}
- **expectedResult**: {what should happen}
- **actualResult**: {what actually happens}

The following fields are mandatory for `documentation` items:

- **content**: {the content requirements to create or update}

## Authoring Rules

- Write from the user's perspective and keep each work item independently understandable.
- Split a request into as many independently deliverable work items as needed.
- Acceptance criteria must be testable without relying on conversation history.
- Do not mix multiple work-item types in one file.
- Do not change existing acceptance criteria or scope after SDLC work begins; create a new work item for new scope.