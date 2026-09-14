---
name: request-writing
description: Use when turning a free-text request or Azure DevOps work item into approved, independently deliverable User Story, Bug, Chore, or Documentation tickets for the software-factory board.
---

# Request Writing

Use this workflow when the request-writer agent receives an initial request. The work-item contract in `.agents/resources/work-items.md` is authoritative for identities, types, fields, templates, storage, and lifecycle values. Do not copy those definitions into this skill or invent a second contract.

## 1. Normalize the request

- Treat free text as the initial request description.
- If the user supplies an Azure DevOps work item ID or URL, retrieve it through a connected Azure DevOps MCP work-item tool such as `wit_get_work_item`.
- Ask for the project name when it cannot be determined from the repository or MCP context.
- If MCP is unavailable or authentication has not been completed, stop and refer the user to `.agents/resources/azure-devops-mcp-setup.md`. Never bypass authentication.
- Extract the title, description, reproduction steps, expected and actual results, acceptance criteria, and the source HTML URL when present. Treat the result as the initial request and continue with this workflow.

## 2. Establish testable scope

Ask no more than three to five focused questions at a time. Continue until the request can be decomposed into work items that are independently understandable and verifiable. Ask about only information needed to decide scope, user value, defect behavior, documentation content constraints, or acceptance criteria.

Do not proceed to ticket creation while significant ambiguity remains. Preserve explicit user terminology and constraints in the proposed request summaries.

## 3. Propose the decomposition

Classify each independently deliverable change as exactly one of the types in `work-items.md`:

- `user-story` for new functionality or enhancements with direct user value.
- `bug` for a defect in existing functionality.
- `chore` for maintenance, refactoring, infrastructure, or technical debt.
- `documentation` for repository documentation work.

Split mixed requests into separate work items. Each proposal should include the type, a short title, the intended outcome, and the acceptance or validation requirements appropriate to that type. Explain dependencies when one item must precede another, but do not merge independent items just to reflect ordering.

Present the proposed breakdown and wait for explicit user approval or requested changes. Revise the proposal as needed; do not write files before approval.

## 4. Create approved work items

After approval:

1. Read `.agents/resources/work-items.md` again if needed and follow its current adapter rules.
2. Allocate the next sequential request ID and update the adapter's ID store.
3. Assign work-item sequence numbers starting at `1` for that request.
4. Ensure the required board directories exist.
5. Write one file per work item under `board/new/` using the exact template and filename rules from `work-items.md`.
6. Set every new item to `Status: New`.
7. Include `Source` only when the request came from an external system, using the retrieved Azure DevOps HTML URL.
8. Make acceptance criteria independently testable and preserve stable IDs.

Do not modify existing work items, move items between lifecycle folders, or create `handoffs/` and `state.json`. Those are driver responsibilities.

## 5. Report the result

Report each created file path, work-item ID, type, and title. State that the items are ready to enter the SDLC workflow. Tell the user to run
`.agents/prompts/next.prompt.md` against a selected work-item ID in a new chat session with a fresh context window.

If creation is blocked, report the exact missing input or failed operation and leave already-created records untouched. Do not claim that an item is ready if its file, required fields, or `Status: New` value could not be verified.

## Completion checklist

- [ ] Input source was normalized, including Azure DevOps source URL when applicable.
- [ ] Ambiguities needed for testable scope were resolved.
- [ ] Every change is represented by one independently deliverable work item.
- [ ] Every item has exactly one valid type.
- [ ] User approval was explicit before file creation.
- [ ] IDs, templates, filenames, storage, and status follow `work-items.md`.
- [ ] No `handoffs/` or `state.json` was created.
- [ ] The final report identifies the next SDLC dispatcher action.
