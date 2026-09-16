# Satisfactory AI Software Factory

## Overview
`Satisfactory` is an AI software factory intended to help enable agentic engineering in the Software Development Lifecyle (SDLC).

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
- **software-architect** - Writes technical specifications in `handoffs/{work-item-id}/specification.md`, split into technology-specific chunks for the software engineers.
- **software-engineer** - Implements approved technical specification chunks across the repository using the applicable technology rules and resources.
- **quality-assurance-engineer** - Implements automated tests from approved specifications, writes failing reproduction tests for bugs, and handles ad hoc testing work.
- **documentation-writer** - Implements documentation work items against the repository's documentation.
- **implementation-validator** - Independently validates delivered implementation and test work against upstream requirements.

## Orchestration
`.agents/workflows/sdlc.md` is the orchestration contract. It defines the three flows, the `state.json` control file, the state machine, the loop failsafes, and the git and artifact conventions.

Each agent runs in its own session with a fresh context window and performs exactly one step. Routing is owned by the driver, not by the agents. To advance a work item, run the `.agents/prompts/next.prompt.md` dispatcher against its id (`/next 00001-1` in VS Code).

## When to use the main workflows
- For any work item taken from `board/new/`, start with `.agents/workflows/sdlc.md`.
- For implementation validation, use `implementation-validator` after each meaningful step.
- For documentation work items, route to `documentation-writer`.

## Skills
- **work-item-writing** - Turn a free-text request or Azure DevOps ticket into a work item on the software-factory board.

## Reference resources
- SDLC orchestration workflow: `.agents/workflows/sdlc.md`
- Next-step dispatcher prompt: `.agents/prompts/next.prompt.md`
- Build and test commands: `.agents/resources/developer-commands.md`
- .NET coding rules: `.agents/rules/dotnet-coding-rules.md`
- .NET implementation reference: `.agents/resources/dotnet-implementation-reference.md`
- Specification document template: `.agents/resources/specification-template.md`
- State.json file template and documentation: `.agents/resources/state-json-template.md`
- Azure DevOps MCP setup: `.agents/resources/azure-devops-mcp-setup.md`

## Routing rule
Keep this file short. Put durable rules in rule docs, step-by-step procedures in skills or workflows, and descriptive background material in resources. Do not reference a file here until it exists.

## Playground
The `playground/` folder contains sample code projects for demonstrating the software factory and trying out new capabilities.
- `playground/dotnet/` - A .NET solution with WebAPI backend, Blazor UI and Aspire orchestration