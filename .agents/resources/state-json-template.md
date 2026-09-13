# `state.json` File Template and Documentation

The `state.json` file is the single source of truth for orchestrating work items through the AI Software Factory SDLC workflow. It defines the current state, chunk dependencies, attempt counters, and routing information.

## File Location
```
handoffs/{work-item-id}/state.json
```

## Template Structure

```json
{
  "workItemId": "00001-1",
  "type": "user-story",
  "flow": "flow-1",
  "state": "chunk-implementation",
  "specificationStatus": "Approved",
  "branch": "feature/00001-1-add-login-feature",
  "activeChunk": "dotnet-backend",
  "chunks": [
    {
      "id": "dotnet-backend",
      "technology": "dotnet",
      "dependsOn": [],
      "state": "tests-passing",
      "implementAttempts": 1,
      "testAttempts": 1,
      "lastFailureSignature": null,
      "latestChangelog": "handoffs/00001-1/chunks/dotnet-backend/changelog.1.md",
      "latestTestlog": "handoffs/00001-1/chunks/dotnet-backend/testlog.1.md"
    }
  ],
  "integration": {
    "state": "not-started",
    "attempts": 0,
    "lastFailureSignature": null
  },
  "validation": {
    "outcome": null,
    "attempts": 0
  },
  "budget": {
    "maxChunkRemediationLoops": 3,
    "maxIntegrationLoops": 3,
    "maxValidationLoops": 3,
    "maxTotalAgentRuns": 40,
    "totalAgentRuns": 17
  },
  "escalations": [],
  "history": [
    {
      "ts": "2026-09-10T09:14:00Z",
      "agent": "software-engineer",
      "chunk": "dotnet-backend",
      "result": "implemented",
      "artifact": "handoffs/00001-1/chunks/dotnet-backend/changelog.1.md"
    }
  ]
}
```

## Field Descriptions

### Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `workItemId` | string | Unique identifier for the work item (e.g., "00001-1") |
| `type` | string | Work item type: "user-story", "chore", "bug", or "documentation" |
| `flow` | string | Workflow type: "flow-1", "flow-2", or "flow-3" |
| `state` | string | Current workflow state (see below) |
| `specificationStatus` | string | Status of specification: null, "Draft", or "Approved" |
| `branch` | string | Git branch name for this work item |
| `activeChunk` | string | ID of the currently active chunk being worked on |

### Chunks Array

Each chunk represents a technology-specific implementation task.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the chunk (e.g., "dotnet-backend") |
| `technology` | string | Technology stack (e.g., "dotnet", "react") |
| `dependsOn` | array | List of chunk IDs that must complete before this one |
| `state` | string | Current state of this chunk: "not-started", "implemented", "tests-passing", "tests-failing", or "blocked" |
| `implementAttempts` | number | Number of implementation attempts for this chunk |
| `testAttempts` | number | Number of testing attempts for this chunk |
| `lastFailureSignature` | string | SHA256 hash of sorted failing test identifiers, or null |
| `latestChangelog` | string | Path to latest changelog file |
| `latestTestlog` | string | Path to latest testlog file |

### Integration Object

Represents the integration testing phase.

| Field | Type | Description |
|-------|------|-------------|
| `state` | string | Integration state: "not-started", "in-progress", "passed", or "failed" |
| `attempts` | number | Number of integration attempts |
| `lastFailureSignature` | string | SHA256 hash of sorted failing test identifiers, or null |

### Validation Object

Represents the validation phase.

| Field | Type | Description |
|-------|------|-------------|
| `outcome` | string | Validation outcome: null, "Passed", "Failed", or "Blocked" |
| `attempts` | number | Number of validation attempts |

### Budget Object

Contains failsafe limits to prevent infinite loops.

| Field | Type | Description |
|-------|------|-------------|
| `maxChunkRemediationLoops` | number | Max remediation attempts per chunk |
| `maxIntegrationLoops` | number | Max integration testing attempts |
| `maxValidationLoops` | number | Max validation attempts |
| `maxTotalAgentRuns` | number | Max total agent runs for the work item |
| `totalAgentRuns` | number | Current count of agent runs |

### Escalations Array

Records issues that require human intervention.

| Field | Type | Description |
|-------|------|-------------|
| `escalations` | array | List of escalation records with details about blocked items |

### History Array

Tracks the execution history for audit and rollback purposes.

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string | Timestamp (ISO 8601) |
| `agent` | string | Agent that performed the action |
| `chunk` | string | Chunk ID if applicable, or null |
| `result` | string | Outcome of the action |
| `artifact` | string | Path to the generated artifact |

## Workflow States

### Work Item States
- `specification-draft`: Specification is being created (human approval required)
- `specification-approved`: Specification has been approved (ready for implementation)
- `chunk-implementation`: Implementation is in progress for the active chunk
- `chunk-testing`: Testing is in progress for the active chunk
- `integration-testing`: Integration testing is in progress
- `validation`: Validation is in progress
- `bug-repro-test`: Bug reproduction test is in progress (flow 2)
- `bug-fix`: Bug fix is in progress (flow 2)
- `documentation`: Documentation is in progress (flow 3)
- `ready-for-user`: Ready for final human review
- `done`: Work item completed and approved
- `blocked`: Work item blocked by an issue requiring human intervention

### Chunk States
- `not-started`: Chunk has not been started
- `implemented`: Implementation has been completed
- `tests-passing`: Tests are passing for this chunk
- `tests-failing`: Tests are failing for this chunk
- `blocked`: Chunk is blocked and requires human intervention

## Key Principles

1. **Single Source of Truth**: Only the driver modifies `state.json`
2. **Self-Sufficient**: Agents only need work item, specification chunk, and artifact paths from state
3. **No Conversation Dependency**: Fresh agents must be able to operate without conversation history
4. **Monotonic Artifacts**: Each agent run must produce a new numbered artifact
5. **Failsafe Guards**: Multiple protection mechanisms prevent infinite loops

## Usage Guidelines

1. The driver is responsible for all state transitions and modifications
2. Agents only write artifacts and report outcomes, never update `state.json`
3. State changes are applied by comparing artifacts on disk with the current state
4. When a chunk's dependencies are all `tests-passing`, it becomes the new `activeChunk`
5. The system uses a sequential approach - parallel execution is not supported

## Version History

- v1.0: Initial template definition (2026-09-13)