---
name: create-specification
description: Use when creating an implementation specification for a User Story or Chore work item on the software-factory board.
argument-hint: A user story or chore work item ID from the board.
---

# Specification Writing

Use this workflow when the software-architect agent receives a specification request. The semantic and operation contract in `.agents/resources/specifications.md` is authoritative. Specification persistence is owned by `python -m tools.work_items`; never inspect or modify its storage directly.

Do not modify existing work-item fields directly, move items between lifecycle folders, or create any other files. Specification and task changes must only be made through `add_spec`, `revise_spec`, and `approve_spec`.

## 1. Retrieve the work item

- Validate that the work item ID is in the format `{request_id}-{sequence}` where request-id is a 5 digit zero padded number and sequence is an incrementing integer.
- Retrieve the work item corresponding to the provided work item ID: `python -m tools.work_items get {work_item_id}`
- If the work item is not found, report the error and stop.
- Verify the work item type is `user-story` or `chore`. If it is any other type, report the error and stop.

## 2. Establish scope

Ask no more than three to five focused questions at a time. Continue until the request can be decomposed into implementation tasks that are independently understandable and verifiable. Ask about only information needed to decide scope, user value, defect behavior, documentation content constraints, or acceptance criteria.

Do not proceed to specification creation while significant ambiguity remains. Preserve explicit user terminology and constraints in the proposed request summaries.

## 3. Design the solution

Based on the established scope, design the solution and plan the implementation. Consider existing functionality, patterns, and constraints. Adhere to any architectural guidance provided in the repository.
Decompose the implementation plan into atomic tasks. Ensure the tasks are independently deliverable and have clearly defined dependencies. Create the tasks in order of delivery. 

Each task should include:
- **id**: Succinct kebab-case descriptive title of the task
- **owner**: Owning agent of the task, typically `software-engineer` for coding tasks
- **scope**: What this task covers
- **affectedPaths**: Paths to projects/folders/files affected by the intended change
- **contracts**: Contracts produced/consumed - APIs, DTOs, events, schemas shared with other tasks.
- **dependencies**: Sequencing/dependencies - must run before/after which other task, if any.
- **acceptanceCriteriaCovered**: Acceptance criteria from the work item fulfilled by the task.

## 4. Create draft specification

- Generate the specification JSON as per schema `.agents/schemas/specification.schema.json` and tasks JSON array as per `.agents/schemas/task.schema.json`.
- Build the request payload as `{ "specification": { ... }, "tasks": [ ... ] }`.
- Write the input to a temporary JSON file, call `python -m tools.work_items add_spec {work_item_id} --input {temporary-file}`, and remove the temporary file after the command finishes.
- Treat a nonzero exit code as a blocker. Report the structured error and do not create records manually.

## 5. Refine specification

- Present the draft specification to the user for review and request feedback or approval from the user.
- If the user requests changes:
  - Revise the specification and tasks as needed based on the user input.
  - Persist any changes to the ADLC board with `python -m tools.work_items revise_spec {work_item_id} --input {temporary-file}` after writing payload `{ "specification": { ... }, "tasks": [ ... ] }` to a temporary JSON file and removing the temporary file after the command finishes.
  - Treat a nonzero exit code as a blocker. Report the structured error and do not update records manually.
  - Once the updated draft is ready, present it to the user for review.
  - Repeat the review/revise loop until the user approves the specification.

## 6. Approve specification

After human approval:

- Mark the specification as approved with `python -m tools.work_items approve_spec {work_item_id}`
- Treat a nonzero exit code as a blocker. Report the structured error and do not update records manually.
    
## 7. Report the result

Report the final specification from the command result. State that the tasks are ready to enter the ADLC workflow.
If creation is blocked, report the exact missing input or failed operation and leave already-created records untouched. Do not claim that an item is ready unless the command returned its required fields and `approved` status.

## Completion checklist

- [ ] Work item was successfully retrieved, read and understood.
- [ ] Ambiguities were resolved and full scope of change is understood.
- [ ] Solution designed in accordance with existing architecture and design guidelines.
- [ ] Required implementation decomposed into independently deliverable tasks.
- [ ] All dependencies between tasks are correctly identified and documented.
- [ ] Specification created and persisted to the ADLC board in `draft` state.
- [ ] User approval was explicit before specification marked as `approved`.
- [ ] The final report presents either the approved specification or the reason why approval could not be obtained (e.g., missing input, failed operation).
