# Git Conventions

## Branch Naming

One branch per work item, created by the orchestrator before the first agent runs:

- `feature/{work-item-id}/{title}` for user stories and chores
- `fix/{work-item-id}/{title}` for bugs
- `docs/{work-item-id}/{title}` for documentation

## Commit Messages

Conventional commits style message format:
```
{type}({work-item-id} [{task-id}]): {agent-short-name} - iteration {n}
```

Where `type` is:
- "feat" for user stories
- "chore" for chores  
- "fix" for bug fixes
- "docs" for documentation

Example: `feat(00001-1 [impl-agent-resource]): engineer - iteration 2`

## Commit Process

- One commit per agent run, made by the **orchestrator** after the run is accepted. Agents do not create branches or commits.
- The commit trail is the execution trace, and it makes rollback to the last good state trivial when a loop goes bad.