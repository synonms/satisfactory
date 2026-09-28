# Satisfactory AI Software Factory

## Overview
`Satisfactory` is an AI software factory intended to help enable an Agentic Development Lifecyle (ADLC).

## Purpose
This file is the entry point for agents working in this repository. Use it to find the right workflow, rule, skill, or reference doc instead of carrying all guidance in one place.

## Where to look
- **Prompts**: `.agents/prompts/`
- **Resources**: `.agents/resources/`
- **Rules**: `.agents/rules/`
- **Skills**: `.agents/skills/`
- **Workflows**: `.agents/workflows/`
- **Work-item domain and persistence**: `tools/work_items/`
- **Deterministic ADLC routing and failsafes**: `tools/adlc/`
- **Python Script Tests**: `tests/`

## Agent directory
- **documentation-writer** - Delivers `documentation` phase tasks against the repository's documentation.
- **implementation-validator** - Independently validates delivered work against the upstream requirement.
- **orchestrator** - Dispatches ADLC tasks using the deterministic routing in `tools/adlc`.
- **quality-assurance-engineer** - Delivers `bug-repro`, `unit-test`, and `integration-test` phase tasks, and handles ad hoc testing work.
- **reviewer** - Reviews delivered code and tests for user stories and chores.
- **software-architect** - Authors the task plan for every work item, plus an architectural specification for user stories and chores.
- **software-engineer** - Delivers `implementation` phase tasks using the applicable technology rules and resources.
- **triage** - Categorises incoming requests and creates approved work items.

## Skills
- **create-plan** - Turn a work item into an approved task plan on the ADLC board.
- **create-work-item** - Turn a free-text request or Azure DevOps ticket into a work item on the ADLC board.

## Reference resources
- Specification management: `.agents/resources/specifications.md`
- Task management: `.agents/resources/tasks.md`
- Work Item management: `.agents/resources/work-items.md`

- Build and test commands: `.agents/resources/developer-commands.md`
- .NET coding rules: `.agents/rules/dotnet-coding-rules.md`
- .NET implementation reference: `.agents/resources/dotnet-implementation-reference.md`
- Azure DevOps MCP setup: `.agents/resources/azure-devops-mcp-setup.md`

## Routing rule
Keep this file short. Put durable rules in rule docs, step-by-step procedures in skills or workflows, and descriptive background material in resources. Do not reference a file here until it exists.

## Playground
The `playground/` folder contains sample code projects for demonstrating the software factory and trying out new capabilities.  Any requests pertaining to the Playground relate to the projects in this folder.
- `playground/dotnet/` - A .NET solution with WebAPI backend, Blazor UI and Aspire orchestration