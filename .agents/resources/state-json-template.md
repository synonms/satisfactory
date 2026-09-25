# `state.json` Template

`state.json` is the source of truth for high-level routing of a work item through the AI Software Factory ADLC workflow.

## Location

```
handoffs/{work-item-id}/state.json
```

## Schema and Validation

[The state JSON Schema](../schemas/state.schema.json) is authoritative for required fields, types, nullability, allowed values, and additional-property rules. Install the development tools with `python -m pip install -r requirements-dev.txt`, then validate every existing control file before consuming it:

```sh
python -m check_jsonschema --schemafile .agents/schemas/state.schema.json handoffs/{work-item-id}/state.json
```

Task-specific state and handoff history no longer live in `state.json`. They are stored in the work-item `tasks` array and validated by [task.schema.json](../schemas/task.schema.json).

## Entry-State Example

```json
{
  "workItemId": "00001-1",
  "type": "user-story",
  "flow": "flow-1",
  "state": "specification-draft",
  "specificationStatus": null,
  "branch": null,
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
    "totalAgentRuns": 0
  },
  "escalations": [],
}
```

## Operational Invariants

- Only the driver mutates `state.json`; agents write artifacts and report outcomes.
- State must be self-sufficient for a fresh agent session and must not depend on conversation history.
- Artifact iteration numbers are scoped to a task, so multiple tasks can have the same iteration number.
- Workflow transitions, failsafes, ownership boundaries, and state-to-agent routing are defined in [the ADLC workflow](../workflows/adlc.md).

## Version History

- v1.4: Moved task/chunk state and handoff history into work-item tasks and aligned references to ADLC (2026-09-25)
- v1.3: Streamlined this resource around the authoritative JSON Schema and SDLC workflow (2026-09-15)
- v1.2: Added the formal JSON Schema and mandatory load-time validation (2026-09-15)
- v1.1: Added basic metrics tracking (`metrics` in `history` and cumulative fields in `budget`) (2026-09-14)
- v1.0: Initial template definition (2026-09-13)