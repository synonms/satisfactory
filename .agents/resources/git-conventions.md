# Git Conventions

## Branch Naming

One branch per work item, created by the driver before the first implementing agent runs:

- `feature/{work-item-id}/{title}` for user stories and chores
- `fix/{work-item-id}/{title}` for bugs
- `docs/{work-item-id}/{title}` for documentation

## Commit Messages

Conventional commits style message format:
```
{type}({work-item-id} [{chunk-id}]): {agent-short-name} - iteration {n}
```

Where `type` is:
- "feat" for user stories
- "chore" for chores  
- "fix" for bug fixes
- "docs" for documentation

Example: `feat(00001-1 [dotnet-backend]): engineer - iteration 2`

## Commit Process

- One commit per agent run, made by the **driver** after the run is accepted. Agents do not create branches or commits.
- The commit trail is the execution trace, and it makes rollback to the last good state trivial when a loop goes bad.