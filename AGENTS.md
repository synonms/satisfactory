# Software Factory Framework

## Purpose
This file is the entry point for agents working in this repository. Use it to find the right workflow, rule, skill, or reference doc instead of carrying all guidance in one place.

## Where to look
- **Prompts**: `.agents/prompts/`
- **Resources**: `.agents/resources/`
- **Rules**: `.agents/rules/`
- **Skills**: `.agents/skills/`
- **Workflows**: `.agents/workflows/`

## Agent directory
- **request-writer** - Categorises incoming requests and creates Kanban tickets for work items.
- **spec-writer** - Writes technical specifications.
- **software-engineer** - Implements approved technical specifications across the repository using the applicable technology rules and resources.
- **quality-assurance-engineer** - Implements automated tests from approved specifications and handles ad hoc testing work.
- **implementation-validator** - Independently validates delivered implementation and test work against upstream requirements.

## When to use the main workflows
- For new feature work, start with `.agents/workflows/feature-implementation.md`.
- For implementation validation, use `implementation-validator` after each meaningful step.
- For documentation tasks, route to `readme-specialist`.

## Skills
Use the skill docs when the task matches a reusable implementation pattern:
- `new-aggregate-root`
- `new-aggregate-member`
- `new-domain-event-handlers`
- `new-integration-tests`
- `new-projection`
- `new-sample-feature`
- `new-value-object`

## Reference resources
- Architecture and request flow: `.agents/resources/structur-overview.md`
- Build and test commands: `.agents/resources/developer-commands.md`
- Coding and domain rules: `.agents/rules/structur-coding-rules.md`
- .NET coding rules: `.agents/rules/dotnet-coding-rules.md`
- .NET implementation reference: `.agents/resources/dotnet-implementation-reference.md`

## Routing rule
Keep this file short. Put durable rules in rule docs, step-by-step procedures in skills or workflows, and descriptive background material in resources.
