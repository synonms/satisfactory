---
name: create-plan
description: Use when authoring the task plan for a work item on the software-factory board, with an architectural specification for user stories and chores and tasks alone for bugs and documentation.
argument-hint: A work item ID from the board.
---

# Plan Authoring

Use this workflow when the software-architect agent receives a design request. The semantic and operation contracts in `.agents/resources/specifications.md` and `.agents/resources/tasks.md` are authoritative. Persistence is owned by `python .agents/run.py work_items`; never inspect or modify its storage directly.

Do not modify existing work-item fields directly or create any other files. Plan changes must only be made through `add_spec`, `revise_spec`, `add_tasks`, `revise_tasks`, and `approve_plan`.

## 1. Retrieve the work item

- Validate that the work item ID is in the format `{request_id}-{sequence}` where request-id is a 5 digit zero padded number and sequence is an incrementing integer.
- Retrieve the work item: `python .agents/run.py work_items get {work_item_id}`
- If the work item is not found, report the error and stop.
- Note the `type`. It determines the plan shape:

| Type | Specification | Review tasks | Authoring command |
| --- | --- | --- | --- |
| `user-story`, `chore` | Required | Mandatory | `add_spec` |
| `bug` | Forbidden | Forbidden | `add_tasks` |
| `documentation` | Forbidden | Forbidden | `add_tasks` |

## 2. Establish scope

Ask no more than three to five focused questions at a time. Continue until the request can be decomposed into tasks that are independently understandable and verifiable. Ask only about information needed to decide scope, user value, defect behaviour, documentation content constraints, or acceptance criteria.

Do not proceed while significant ambiguity remains. Preserve explicit user terminology and constraints.

## 3. Design the solution

For a `user-story` or `chore`, design the architectural approach: affected layers, components, data flow, integration points, and dependencies. Consider existing functionality, patterns, and constraints, and adhere to any architectural guidance in the repository. Keep the specification about **architecture**; the steps belong in the tasks.

For a `bug` or `documentation` item there is no specification. Go straight to the task plan.

Before authoring a plan, generate repository context with the repository-context command and run the plan linter on the proposed plan. Persist a concise, sourced context snapshot as `repositoryContext` with the plan. Record `planPolicy` with `risk` (`low`, `medium`, `high`) and `mode` (`lean`, `balanced`, `strict`); default bounded additive work to `low` / `lean`, and use `strict` only when the change has concrete high-risk characteristics. The context snapshot is informative and does not override the work item or specification.

## 4. Author the task graph

Decompose the work into single-owner phase tasks. The phase determines the owner, so do not invent owners.

| Phase | Owner |
| --- | --- |
| `bug-repro` | `quality-assurance-engineer` |
| `implementation` | `software-engineer` |
| `unit-test` | `quality-assurance-engineer` |
| `integration-test` | `quality-assurance-engineer` |
| `review` | `reviewer` |
| `validation` | `implementation-validator` |
| `documentation` | `documentation-writer` |

Standard shapes:

- `user-story` / `chore`: for low-risk cohesive work, `implementation` -> one QA-owned `unit-test` or `integration-test` task -> one shared `review` -> one `validation`. For balanced or strict work, split only at justified delivery or risk boundaries; multiple implementation tasks may share QA and review tasks.
- `bug`: `bug-repro` -> `implementation` -> `unit-test` -> `validation`.
- `documentation`: `documentation` -> `validation`.

Rules the service enforces, so get them right first time:

- Every plan must contain a `validation` task.
- For `user-story` and `chore`, every `implementation` task must have a `review` task downstream of it.
- A shared review task may cover multiple implementation tasks. For user stories and chores, make it depend on the QA task(s) so review observes tested changes.
- Keep QA as the independent owner of tests; do not ask the software engineer to modify test files.
- For `bug` and `documentation`, review tasks are rejected.
- Dependencies must resolve within the plan and must not form a cycle.
- Add an `integration-test` task **only** when cross-task behaviour genuinely needs proving. Do not add one by default.

Each task should include:

- **id**: Succinct kebab-case identifier.
- **phase**: One of the phases above.
- **scope**: What this task covers.
- **deliverables**: The concrete outputs the owner must produce.
- **verification**: The evidence, scenarios, or commands that show the task is complete. Testing expectations live here, not in the specification.
- **technology**: The stack, for example `dotnet`, so the owner loads the right rules.
- **affectedPaths**: Paths expected to be modified.
- **contracts**: APIs, DTOs, events, or schemas shared with other tasks.
- **dependencies**: Task IDs that must complete first.
- **acceptanceCriteriaCovered**: Acceptance criteria IDs fulfilled by this task.

Write each task so its owner can do the work from the task alone. A task that requires reading the whole specification to understand is not finished.

Do not supply `owner`, `state`, `attempts`, or `history`; the service owns those.

## 5. Persist the draft plan

For a `user-story` or `chore`:

- Build the payload `{ "specification": { ... }, "planPolicy": { "risk": "low|medium|high", "mode": "lean|balanced|strict" }, "repositoryContext": { ... }, "tasks": [ ... ] }`.
- Write it to a temporary JSON file, call `python .agents/run.py work_items add_spec {work_item_id} --input {temporary-file}`, and remove the temporary file afterwards.

For a `bug` or `documentation` item:

- Build the payload `{ "planPolicy": { ... }, "repositoryContext": { ... }, "tasks": [ ... ] }`.
- Write it to a temporary JSON file, call `python .agents/run.py work_items add_tasks {work_item_id} --input {temporary-file}`, and remove the temporary file afterwards.

Treat a nonzero exit code as a blocker. Report the structured error and do not create records manually.

## 6. Refine the plan

- Present the draft plan to the user and request feedback or approval.
- If the user requests changes, revise and persist with `revise_spec` or `revise_tasks` using the same payload shape.
- Repeat until the user approves.

## 7. Approve the plan

After explicit human approval:

- `python .agents/run.py work_items approve_plan {work_item_id}`
- This is the single gate for every work-item type. Never approve without express user approval.
- Treat a nonzero exit code as a blocker.

## 8. Record the design metrics

Record this design run against the work item so the time and token cost of the whole lifecycle is tracked alongside the later implementation steps.

1. Build a JSON object with `agent: "software-architect"`, a `result` summarising the design run, and `metrics` containing `durationSeconds`, `inputTokens`, `outputTokens`, `totalTokens`, `model`, and `estimatedCostUsd` for the run, derived as described in [Run Metrics](../../resources/tasks.md#run-metrics). Placeholder values are rejected.
2. Pass it to `python .agents/run.py work_items record_intake {work_item_id} --input -` through standard input. Do not create a staging file.
3. Record it once per session, whether the plan was approved or left in `draft`.
4. Treat a nonzero exit code as a blocker. Report the structured error and do not edit stored records manually.

The service timestamps the entry, appends it to the work item's `intake` array, and rolls the metrics into `execution.totals`.

## 9. Report the result

Report the approved plan: the task ids, phases, owners, and dependency order. State that the work item is ready for `python .agents/run.py adlc next {work_item_id}`.

If approval could not be obtained, say so and leave the plan in `draft`.

## Completion checklist

- [ ] Work item retrieved and its type identified.
- [ ] Ambiguities resolved and full scope understood.
- [ ] Specification authored for a user story or chore, and omitted for a bug or documentation item.
- [ ] Task graph authored with correct phases, dependencies, and no cycles.
- [ ] Review tasks present for every implementation task on a user story or chore, and absent on bugs and documentation.
- [ ] A validation task is present.
- [ ] `integration-test` included only where genuinely needed.
- [ ] Every task carries the deliverables and verification its owner needs.
- [ ] Plan persisted in `draft` and approved only after explicit user approval.
- [ ] Design run metrics recorded against the work item with `record_intake`.
