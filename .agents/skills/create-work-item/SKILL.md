---
name: create-work-item
description: Use when turning a free-text request or Azure DevOps work item into independently deliverable User Story, Bug, Chore, or Documentation work items for the software-factory board.
---

# Work Item Writing

Use this workflow when the triage agent receives an initial request. The semantic and operation contract in `.agents/resources/work-items.md` is authoritative. Work-item persistence is owned by `python -m tools.work_items`; never inspect or modify its storage directly.

## 1. Normalize the request

- Treat free text as the initial request description.
- If the user supplies an Azure DevOps work item ID or URL, retrieve it through a connected Azure DevOps MCP work-item tool such as `wit_get_work_item`.
- Ask for the project name when it cannot be determined from the repository or MCP context.
- If MCP is unavailable or authentication has not been completed, stop and refer the user to `.agents/resources/azure-devops-mcp-setup.md`. Never bypass authentication.
- Extract the title, description, reproduction steps, expected and actual results, acceptance criteria, and the source HTML URL when present. Treat the result as the initial request and continue with this workflow.

## 2. Establish testable scope

Ask no more than three to five focused questions at a time. Continue until the request can be decomposed into work items that are independently understandable and verifiable. Ask about only information needed to decide scope, user value, defect behavior, documentation content constraints, or acceptance criteria.

Do not proceed to ticket creation while significant ambiguity remains. Preserve explicit user terminology and constraints in the proposed request summaries.

## 3. Finalize the decomposition

Classify each independently deliverable change as exactly one of the types in `work-items.md`:

- `user-story` for new functionality or enhancements with direct user value.
- `bug` for a defect in existing functionality.
- `chore` for maintenance, refactoring, infrastructure, or technical debt.
- `documentation` for repository documentation work.

Split mixed requests into separate work items, but only if the components are independently deliverable and have no risk of changes to the same files or functionality. Each work item should include the type, a short title, the intended outcome, and the acceptance or validation requirements appropriate to that type. Explain dependencies when one item must precede another, but do not merge independent items just to reflect ordering.

Once significant ambiguity has been resolved and the work items are independently understandable and verifiable, create them immediately. Do not seek or wait for human approval at work-item creation.

## 4. Create work items

1. Build a JSON array containing one object per work item in decomposition order.
2. Include `type`, `request`, and `description` on every object, plus `source` only when the request came from an external system.
3. For a user story or chore, include `acceptanceCriteria` as an array of independently testable description strings. For a bug, include `stepsToReproduce`, `expectedResult`, and `actualResult`. For documentation, include `content`.
4. Do not provide IDs, criterion IDs, creation dates, statuses, or specification content; the service owns those fields.
5. Pass the JSON array to `python -m tools.work_items create-request --input -` through standard input. Do not create a temporary, staging, or request file in the repository.
6. Treat a nonzero exit code as a blocker. Report the structured error and do not create records manually.

Do not modify existing work items or create any other files. Those are architect and orchestrator responsibilities.

## 5. Report the result

Report each created work-item ID, type, and request summary from the command result. Present every persisted file as a clickable workspace-relative link using `board/{request-id}/{work-item-id}.work-item.json` so the user can review or manually amend it offline. Do not start or delegate the design phase automatically.

State that the user may leave the work item in `new` status if it is not satisfactory. For **every** created work item, regardless of type, tell the user that once they are satisfied with the file they can manually run `.agents/prompts/satisfactory-design.prompt.md` against the work-item ID in a new chat session with a fresh context window. Bugs and documentation items go through design too: the architect authors their task plan, just without a specification.

If creation is blocked, report the exact missing input or failed operation and leave already-created records untouched. Do not claim that an item is ready unless the command returned its required fields and `new` status.

## Completion checklist

- [ ] Input source was normalized, including Azure DevOps source URL when applicable.
- [ ] Ambiguities needed for testable scope were resolved.
- [ ] Every change is represented by one independently deliverable work item.
- [ ] Every item has exactly one valid type.
- [ ] No human approval gate was introduced before work-item creation.
- [ ] Creation input was supplied through standard input without a repository staging file.
- [ ] The creation command succeeded and returned every work item.
- [ ] The final report presents every created work-item ID and persisted file link.
