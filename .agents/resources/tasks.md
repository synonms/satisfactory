# Tasks

This document defines task semantics and task operations for the AI Software Factory. Tasks are first-class entities nested within a work item and are persisted through `python .agents/run.py work_items`.

## Purpose

A task is one unit of work, owned by exactly one agent, in exactly one ADLC phase. It captures:

- The phase, owner, scope, and deliverables
- Delivery dependencies and touched paths
- Task runtime state and the attempt counter
- Activity history for every iteration
- Execution metrics for observability and no-progress detection

Tasks are stored in the work-item `tasks` array and validated by `.agents/schemas/task.schema.json`.

Retries never create tasks. When work is sent back, the existing task is reopened and its history continues, so the audit trail and metrics survive the loop.

## Relationship to Work Items and Specifications

- A work item has no tasks until the `software-architect` authors a plan.
- The task plan is authored for **every** work-item type. `user-story` and `chore` plans are authored alongside a specification with `add_spec`; `bug` and `documentation` plans are authored with `add_tasks` and have no specification.
- `planStatus` is the single human approval gate. No task may be dispatched or record activity until it is `approved`.

## Phases and Owners

The phase determines the owner. The service rejects any other pairing.

| Phase | Owner | Purpose |
| --- | --- | --- |
| `bug-repro` | `quality-assurance-engineer` | Write a test that fails for the reported defect |
| `implementation` | `software-engineer` | Write production code |
| `unit-test` | `quality-assurance-engineer` | Write and run automated tests for one implementation task |
| `integration-test` | `quality-assurance-engineer` | Verify behaviour across task boundaries |
| `review` | `reviewer` | Review delivered code and tests |
| `validation` | `implementation-validator` | Verify delivery against the upstream requirement |
| `documentation` | `documentation-writer` | Write or update repository documentation |

Plan shape rules enforced by the service:

- Every plan must contain a `validation` task.
- `user-story` and `chore` plans must cover every `implementation` task with a downstream `review` task.
- `bug` and `documentation` plans must not contain `review` tasks.
- `integration-test` tasks are optional and appear only when the architect plans one.
- Dependencies must resolve within the plan and must not form a cycle.

## Task Contract

Planning fields:
- `id`: Unique kebab-case task identifier.
- `phase`: The ADLC phase.
- `owner`: Responsible agent. Derived from the phase.
- `scope`: What this task covers.
- `deliverables`: Concrete outputs the owner must produce.
- `verification`: Evidence, scenarios, or commands that show the task is complete.
- `technology`: Optional technology context used to select rules and resources.
- `affectedPaths`: Paths expected to be modified.
- `contracts`: Cross-task contract touchpoints.
- `dependencies`: Task IDs that must reach a terminal success state first.
- `acceptanceCriteriaCovered`: Requirement IDs this task satisfies.

Lifecycle fields, all service-owned:
- `state`: Constrained by the phase, see below.
- `attempts`: Number of owner attempts.
- `lastFailureSignature` and `previousFailureSignature`: Two identical values mean no progress.
- `latestArtifact`: Most recent artifact path.
- `remediationTargetTaskId`: Task that must be reworked because of this task's latest outcome.
- `blockedReason`: Why the task is blocked.
- `history`: Chronological activity list.

## State Machines

Each phase has its own states. `.agents/schemas/task.schema.json` enforces the legal set and `.agents/tools/work_items/phases.py` is the transition authority.

| Phase | States | Terminal success |
| --- | --- | --- |
| `implementation` | `not-started`, `in-progress`, `implemented`, `rework-required`, `blocked` | `implemented` |
| `documentation` | `not-started`, `in-progress`, `documented`, `rework-required`, `blocked` | `documented` |
| `bug-repro`, `unit-test`, `integration-test` | `not-started`, `in-progress`, `tests-passing`, `tests-failing`, `blocked` | `tests-passing` |
| `review` | `not-started`, `in-progress`, `approved`, `changes-requested`, `blocked` | `approved` |
| `validation` | `not-started`, `in-progress`, `validated`, `rejected`, `blocked` | `validated` |

## Activity Contract

Each history entry records one attempt at the task:

- `ts`: Timestamp in UTC.
- `iteration`: Task-scoped iteration number.
- `agent`: Agent producing the handoff. Must equal the task owner.
- `technology`: Optional technology context.
- `outcome`: One of `implemented`, `documented`, `passed`, `failed`, `approved`, `changes-requested`, `validated`, `rejected`, `blocked`. The outcome must be legal for the task phase.
- `result`: Free-text outcome summary.
- `artifact`: Optional artifact path.
- `filesChanged`: Changed files for that iteration.
- `remediationTargetTaskId`: Required when the outcome is `changes-requested` or `rejected`.
- `metrics`: Required run metrics:
  - `durationSeconds`
  - `inputTokens`
  - `outputTokens`
  - `totalTokens`
  - `model`
  - `estimatedCostUsd`

Outcome to state mapping:

| Outcome | Resulting state |
| --- | --- |
| `implemented` | `implemented` |
| `documented` | `documented` |
| `passed` | `tests-passing` |
| `failed` | `tests-failing` |
| `approved` | `approved` |
| `changes-requested` | `changes-requested` |
| `validated` | `validated` |
| `rejected` | `rejected` |
| `blocked` | `blocked` |

## Remediation

`changes-requested` and `rejected` require `remediationTargetTaskId`. The service then:

1. Returns the named task to `rework-required` or `tests-failing`, depending on its phase.
2. Returns every task downstream of it to `not-started`.
3. Increments `reviewLoops` or `validationLoops` in `execution.budget`.

History is never rewritten.

## Operations

Commands emit a JSON success envelope to stdout. Failures emit structured JSON to stderr and return nonzero.

Install tools once:

```powershell
python -m pip install -r requirements-dev.txt
```

Read a task:

```powershell
python .agents/run.py work_items get_task 00001-1 impl-agent-resource
```

Record activity:

```powershell
python .agents/run.py work_items record_activity 00001-1 impl-agent-resource --input activity.json
```

`activity.json` must be a task activity payload. The service validates the outcome against the task phase, appends it to history, updates the task state and attempt counter, applies any remediation, and rolls the metrics into `execution.totals`. Supply `failureSignature` alongside a `failed` outcome so no-progress detection works.

## Authoring Rules

- Keep task scope independently understandable.
- One owner, one phase, one task. Do not create a task that spans two agents.
- Keep IDs stable after work begins.
- Record every attempt through `record_activity`.
- Do not edit persisted task JSON directly.
