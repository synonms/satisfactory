# ADLC Workflow

The `adlc` workflow is the orchestration contract for the AI Software Factory. It defines how a work item moves from intake to a delivered, validated change. Work-item semantics and operations are defined in `.agents/resources/work-items.md`; persistence is encapsulated by `python -m tools.work_items`.

## Core principle

Each agent session is a pure function:

> read state -> perform exactly one step -> write artifacts and append history -> stop.

The **orchestrator** agent manages work item state and decides what is to be run next by which agent. Implementation agents perform the work, write artifacts and report outome.

This separation is what makes loop termination guaranteed rather than hoped for: an agent cannot reset its own attempt counter or route itself past a guard.

## Artifact layout

```
board/
  {request-id}/
    {work-item-id}/
      {work-item-id}.state.json
      specification.md
      tasks/
        {task-id}/
          changelog.{n}.md
          testlog.{n}.md
      integration/
        testlog.{n}.md
      validationlog.{n}.md
```

`state.json` is the source of truth for high-level routing only. Work-item records are the requirement payload and include first-class task state/history via the `tasks` array, retrieved through the work-item CLI. Agents must not depend on persistence paths or formats.

Iteration numbers are scoped to the task, not to the work item. Two tasks may both be on `changelog.2.md` without collision.

## Control file: `state.json`

```jsonc
{
  "workItemId": "00001-1",
  "type": "user-story",              // user-story | chore | bug | documentation
  "flow": "flow-1",                  // flow-1 | flow-2 | flow-3
  "state": "chunk-implementation",
  "specificationStatus": "Approved", // null | Draft | Approved
  "branch": "feature/00001-1-add-login-feature",
  "integration": { "state": "not-started", "attempts": 0, "lastFailureSignature": null },
  "validation": { "outcome": null, "attempts": 0 },
  "budget": {
    "maxChunkRemediationLoops": 3,
    "maxIntegrationLoops": 3,
    "maxValidationLoops": 3,
    "maxTotalAgentRuns": 40,
    "totalAgentRuns": 17,
    "totalDurationSeconds": 620,
    "totalTokens": 145000,
    "totalEstimatedCostUsd": 0.58
  },
  "escalations": []
}
```

### Ownership rules

- Only the driver mutates `state.json`. That includes `state`, integration/validation/budget counters, and `escalations`.
- Task state, task attempts, and task history are mutated through `python -m tools.work_items record_activity` and stored on the work-item `tasks` array.
- Before any driver or agent consumes an existing `state.json`, validate it with `python -m check_jsonschema --schemafile .agents/schemas/state.schema.json handoffs/{work-item-id}/state.json`. Install the validator first with `python -m pip install -r requirements-dev.txt`. On validation failure, do not consume or modify the file; report the validation errors and treat the work item as blocked pending correction.
- Only the driver changes an existing work item's lifecycle status after triage creates it. Use `python -m tools.work_items change-status`; never modify work-item persistence directly.
- Agents write their numbered artifact and report an outcome. They propose; they do not route, and they do not touch `state.json`.
- The driver applies the previous run's transition at the start of the next dispatch, by comparing `state.json` against the artifacts on disk. A missing expected artifact is a failed run under the monotonic artifact rule.
- `state.json` must be **self-sufficient**. A fresh agent needs only its work item, its specification chunk, and the artifact paths named in state. It must never depend on conversation history.

### Work item states

| State | Next agent |
| --- | --- |
| `specification-draft` | none - human approval gate; the driver records the outcome |
| `specification-approved` | task owner from the next `tasks` entry (typically `software-engineer` or `documentation-writer`) |
| `chunk-implementation` | `software-engineer` for the active task |
| `chunk-testing` | `quality-assurance-engineer` for the active task |
| `integration-testing` | `quality-assurance-engineer` (integration scope) |
| `validation` | `implementation-validator` |
| `bug-repro-test` | `quality-assurance-engineer` (optional bug-specific task state when explicitly planned) |
| `bug-fix` | `software-engineer` (optional bug-specific task state when explicitly planned) |
| `documentation` | `documentation-writer` (optional documentation-specific task state when explicitly planned) |
| `ready-for-user` | none - final human review gate; the driver records the decision |
| `done` | terminal - delivered and approved |
| `blocked` | terminal - awaiting human intervention |

### Task states

`not-started` -> `implemented` -> `tests-passing` | `tests-failing` -> `blocked`

All work item types should enter ADLC only after a software-architect design pass has produced a specification and task list for the item.

## Flow 1: user story or chore

This workflow is defined in [feature.md](feature.md).

## Flow 2: bug

This workflow is defined in [bugfix.md](bugfix.md).

## Flow 3: documentation

This workflow is defined in [documentation.md](documentation.md).

## Failsafes

Attempt caps alone permit an agent to thrash identically three times. All of the following apply together.

1. **Per-edge attempt caps.** `maxChunkRemediationLoops`, `maxIntegrationLoops`, `maxValidationLoops`. Counters live in `state.json` and are incremented by the driver only.
2. **No-progress detection.** After each test run, compute `lastFailureSignature` as a hash of the sorted set of failing test identifiers. Two consecutive identical signatures for the same task escalate to `blocked` immediately, regardless of remaining budget. This is the highest-value failsafe: it catches the loop where the same mistake is repeated with cosmetic variation.
3. **Global run budget.** `maxTotalAgentRuns` is a hard circuit breaker across the entire work item. Exceeding it forces `blocked`.
4. **Monotonic artifact rule.** Every agent run must produce a new numbered artifact and corresponding task activity entry. A run producing none is a failed run and still counts against `totalAgentRuns`.
5. **Test-integrity guard.** Reject a `testlog` iteration in which the total test count decreased unless the testlog states an explicit justification. Prevents progress by deletion.
6. **Ownership guard.** Check the diff before accepting a run:
   - `software-engineer` must not modify test files or test projects.
   - `quality-assurance-engineer` must not modify production code.
   - `implementation-validator` must not modify any file.
   A violation invalidates the run. This prevents the classic failure where an engineer makes a test pass by editing the test.
7. **Blocked is a clean terminal state**, not a failure to retry around. On `blocked`, append an entry to `escalations` describing the requirement, the evidence, the attempts made, and the recommended human action, then stop.

## Git conventions

- One branch per work item, created by the driver before the first implementing agent runs:
  - `feature/{work-item-id}/{title}` for user stories and chores
  - `fix/{work-item-id}/{title}` for bugs
  - `docs/{work-item-id}/{title}` for documentation
- One commit per agent run, made by the **driver** after the run is accepted. Agents do not create branches or commits.
- Conventional commits style message format:
  ```
  {type}({work-item-id} [{chunk-id}]): {agent-short-name} - iteration {n}
  ```
  where `type` is "feat" for user stories, "chore" for chores, "fix" for bug fixes and "docs" for documentation. For example `feat(00001-1 [dotnet-backend]): engineer - iteration 2`. Use `-` as the chunk id for work-item-scoped runs such as validation.
- The commit trail is the execution trace, and it makes rollback to the last good state trivial when a loop goes bad.

## Artifact frontmatter

Every handoff artifact begins with this YAML block so a downstream agent can orient from the frontmatter alone and open the body only when detail is needed. Context economy matters most once a work item is many iterations deep.

```yaml
---
workItem: 00001-1
chunk: dotnet-backend        # '-' for work-item-scoped artifacts
iteration: 2
agent: software-engineer
technology: dotnet           # omit when not technology-specific
outcome: implemented         # implemented | passed | failed | blocked | Passed | Failed | Blocked
filesChanged:
  - src/Api/LoginEndpoint.cs
nextOwner: quality-assurance-engineer
---
```

### Handoff contract

For detailed definitions of task history and handoff metadata, see [.agents/resources/tasks.md](../resources/tasks.md).

## Technology specialisation

There is one `software-engineer` agent and one `quality-assurance-engineer` agent. Specialisation is a **parameter**, not a separate agent file: the driver passes the chunk's `technology` value, and the agent loads the matching rules from `.agents/rules/` and resources from `.agents/resources/`. Adding a stack means adding a rules file, not cloning an agent.

## Running the workflow

### Stage 1: driver-assisted (current)

Use the `.agents/prompts/next.prompt.md` dispatcher. Given a work item id, it reads `state.json`, reports the next agent and the exact opening instruction, and states the transition to apply afterwards. Run each step in a new chat session to guarantee a fresh context window.

Human gates remain at `specification-draft -> specification-approved` and at `ready-for-user -> done`. Final-review remediation is limited to unmet requirements already recorded in the work item or approved specification; scope additions become separate work items.

### Stage 2: automated (planned)

Once the state machine is stable, a driver under `tools/factory/` reads `state.json`, invokes the CLI non-interactively with the selected agent, applies the transition, and commits. Each invocation is a separate process, so fresh context comes for free. The transition logic must be unit tested, because it is the actual guarantee that loops terminate.
