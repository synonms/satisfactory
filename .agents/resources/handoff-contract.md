# AI Software Factory Handoff Contract

This document defines the strict contract for information passed between agents in the AI Software Factory pipeline. All handoff artifacts must follow this specification to ensure consistency and prevent errors.

## Overview

Each agent interaction produces a numbered artifact (changelog, testlog, specification.md, documentation.md) that is structured according to this contract. The information conveyed by each artifact can be determined entirely from the frontmatter section, with the body containing full detail when needed.

## Artifact Structure

All handoff artifacts must begin with a YAML frontmatter block containing required metadata:

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

### Frontmatter Fields

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `workItem` | string | Yes | Unique identifier for the work item (e.g., "00001-1") |
| `chunk` | string | Yes | Chunk ID if the artifact is chunk-specific, "-" for work-item-scoped artifacts |
| `iteration` | number | Yes | Iteration count (starting at 1) |
| `agent` | string | Yes | Agent that produced this artifact (e.g., "software-engineer") |
| `technology` | string | No | Technology stack (e.g., "dotnet", "react") |
| `outcome` | string | Yes | Outcome of the agent's work (must match state machine definitions) |
| `filesChanged` | array of strings | No | List of files modified by this iteration |
| `nextOwner` | string | Yes | Next agent responsible for this work item/iteration (can be null for final state) |

### Artifact Types

Different artifacts in the pipeline have different requirements:

#### Specification Files (.md)
- Must contain all information needed to understand what needs to be implemented
- Should not contain implementation details, only requirements
- Use the specification template and ensure all sections are populated where appropriate

#### Implementation Changelogs (changelog.{n}.md)
- Include code changes made by the software engineer
- Must reference specific files modified
- Should describe changes in clear, technical terms
- Include commit messages and associated work item IDs
- May include test cases or integration points

#### Testing Logs (testlog.{n}.md)
- Document tests written or run by quality-assurance-engineer
- Include results of automated test runs
- List specific test cases and their outcomes
- Note any failing tests with error details and reproduction steps
- Should include a summary of passed/failed tests

#### Validation Reports (validationlog.{n}.md)
- Detail the validation process undertaken
- Include results from verification
- Document compliance with requirements 
- Indicate whether artifact passed or failed validation
- For documentation items, compare changes against original request

## Handoff Protocols

### Information Flow

1. **Information Transfer**: When an agent completes work, it must produce a new numbered artifact following the format above
2. **No Conversation Dependency**: Fresh agents must be able to operate without conversation history - all required information is in the frontmatter and content
3. **Context Economy**: Artifacts are written with minimal detail in frontmatter for quick orientation, full details in body when needed

### State Management

Each handoff must contain sufficient metadata to enable the next agent to perform its function correctly:
- For software engineers: specification details including technology, chunk scope, and dependencies
- For quality assurance engineers: test execution details and any implementation issues
- For documentation writers: requirements from request-writer work items
- For validators: comparison of artifact against established criteria

### Data Integrity

1. **Consistent Formatting**: All artifacts must use the same YAML frontmatter format and Markdown structure
2. **Version Control Ready**: Artifacts should be clean, diff-friendly, and not include generated content that changes between runs
3. **Clear Ownership**: Always indicate ownership by `nextOwner` to allow automated routing
4. **Comprehensive Metadata**: Include all relevant context in the frontmatter to support any subsequent agent

## Validation Requirements

Before an artifact is considered complete:
1. The file must be properly formatted with required frontmatter fields
2. The frontmatter must provide sufficient information for the next agent to proceed
3. Content must be aligned with specified outcome (e.g., "implemented" should contain code changes)
4. All fields should be populated appropriately (null values are permitted only when indicated in requirements)

## Version History

- v1.0: Initial handoff contract definition (2026-09-13)