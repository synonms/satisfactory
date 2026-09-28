## Step 1 — create the work items (once per request)

Open a new chat, select the `triage` agent, and paste your request (free text, or an Azure DevOps work item id/URL). Answer its clarifying questions and approve the proposed breakdown. It creates stable work-item IDs through the repository's work-item service.

If the request is not carried out by the custom agent and instead the general agent tries to go ahead with implementation, try wrapping your prompt:

_Create work items for the following request: "{REQUEST}". Do not carry out implementation. Use the create-work-item workflow and work-item CLI._

## Step 2 — author and approve the task plan (once per work item)

Open a new chat, select the `software-architect` agent, and run:

`Follow .agents/prompts/satisfactory-design.prompt.md for work item 00001-1`

Every work-item type goes through this step. For a user story or chore the architect writes an architectural specification alongside the tasks. For a bug or documentation item it writes tasks only — those types have no specification by design.

Review the proposed plan and approve it explicitly. Approval sets `planStatus` to `approved`, and nothing can be dispatched until it is.

## Step 3 — advance one work item (repeat until terminal)

Open a new chat, select the `orchestrator` agent, and run:

`Follow .agents/prompts/satisfactory-implement.prompt.md for work item 00001-1`

The orchestrator asks `python .agents/run.py adlc next 00001-1` what happens next and reports the task, its owner, and the opening instruction. Then:

1. Open another new chat and select the agent it named.
2. Paste the opening instruction block verbatim.
3. Let that agent finish and record its outcome with `record_activity`.
4. Go back to step 3, and the orchestrator asks the router for the next task.

Every step gets its own session, which is what keeps the context window fresh. You stop when the router reports `ready-for-user` or `block`.

To see where a work item is at any time:

`python .agents/run.py adlc status 00001-1`

## Human gates

You are asked to intervene at exactly two points:

1. **Plan approval** — `planStatus` `draft → approved`, for every work-item type.
2. **Final acceptance** — at `ready-for-user`, after every task has succeeded.

Record plan approval with `python .agents/run.py work_items approve_plan {work_item_id}`.

On final approval, the work-item status changes to `done`. If there are issues with the implementation, the practical wording for a valid remediation request is:

```
Request remediation: [requirement text or acceptance-criterion identifier] is not met.
Evidence: [brief observed behavior].
Owning task: [task id]
```

Any remediation requested which is out of scope of the original work item or approved specification will be rejected - a new work item should be raised to address it.

## How the loop terminates

Routing is not a judgement call. `.agents/tools/adlc/routing.py` picks the first task whose dependencies have all succeeded, and `.agents/tools/adlc/policy.py` enforces the attempt caps, loop caps, run budget, no-progress detection, and ownership guard. Both are unit tested under `tests/adlc`, which is the actual guarantee that a remediation loop cannot run forever.

### Reuse in another repository

Copy the `.agents/` directory to the root of the target repository and install its Python runtime dependencies with `python -m pip install -r .agents/requirements.txt`. Run the bundled CLI from that root, for example `python .agents/run.py work_items list` or `python .agents/run.py adlc next 00001-1`. Work items are stored in `.agents/board/` by default; no root-level `tools/` or `board/` directory is required. Ignore `.agents/board/` in the target repository if work-item records should stay out of version control.

For VS Code/Copilot, merge `.agents/resources/vscode-settings.example.json` into the target repository's `.vscode/settings.json` (or your VS Code user settings). This registers the bundled agents and prompts and optionally auto-approves only the listed read-only commands. VS Code does not load the example from `.agents/` by itself; review the rules before enabling them. Commands that mutate work items, including the human `approve_plan` gate, are deliberately not in the example.

Other harnesses can reference the agent files by path but need their own configuration to discover agents and approve terminal commands.
