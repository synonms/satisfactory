# Specification: {Feature/Work Item Name}

- **Work item**: {link or identifier for the related user story or chore located according to `.agents/resources/work-items.md`}
- **Status**: Draft
- **Author**: software-architect
- **Approval override used**: {None | Yes - reason}

## Summary

{Brief description of the feature/chore and the problem it solves.}

## Acceptance Criteria

- {Criterion identifier and description, copied/refined from the work item}
- {Criterion identifier and description}

## Architectural Summary

{High-level description of the approach: affected layers, components, data flow, and how this specification will be satisfied. Reference existing architecture and conventions rather than restating them.}

## Key Design Decisions

- {Decision and rationale}
- {Decision and rationale}

## API Contracts

{Endpoint definitions with OpenAPI-style schemas for requests/responses.}

## Database Schema

{Tables/collections, relationships, constraints, and migrations required.}

## UI Components

{Components, user interactions, and view/state behaviour required.}

## Testing Requirements

{Testing scenarios and coverage expectations that quality-assurance-engineer must satisfy.}

## Chunk Breakdown

Repeat this section once per technology/programming-language chunk. Each chunk is handed to a specialised `software-engineer` agent.

### Chunk: {Technology/Language, e.g. ".NET Backend"}

- **Owner**: {e.g. .NET software-engineer}
- **Scope**: {what this chunk covers}
- **Affected projects/folders**: {paths}
- **Contracts produced/consumed**: {APIs, DTOs, events, schemas shared with other chunks}
- **Sequencing/dependencies**: {must run before/after which other chunk, if any}
- **Acceptance criteria covered**: {identifiers from above}

### Chunk: {Technology/Language, e.g. "React Frontend"}

- **Owner**: {e.g. React software-engineer}
- **Scope**: {what this chunk covers}
- **Affected projects/folders**: {paths}
- **Contracts produced/consumed**: {APIs, DTOs, events, schemas shared with other chunks}
- **Sequencing/dependencies**: {must run before/after which other chunk, if any}
- **Acceptance criteria covered**: {identifiers from above}

## Cross-Chunk Integration Points

- {e.g. "React frontend consumes the `/employees` endpoint contract produced by the .NET backend chunk"}

## Open Questions / Risks

- {Anything that needs resolution before or during implementation}
