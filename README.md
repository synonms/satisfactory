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

The orchestrator asks `python -m tools.adlc next 00001-1` what happens next and reports the task, its owner, and the opening instruction. Then:

1. Open another new chat and select the agent it named.
2. Paste the opening instruction block verbatim.
3. Let that agent finish and record its outcome with `record_activity`.
4. Go back to step 3, and the orchestrator asks the router for the next task.

Every step gets its own session, which is what keeps the context window fresh. You stop when the router reports `ready-for-user` or `block`.

To see where a work item is at any time:

`python -m tools.adlc status 00001-1`

## Human gates

You are asked to intervene at exactly two points:

1. **Plan approval** — `planStatus` `draft → approved`, for every work-item type.
2. **Final acceptance** — at `ready-for-user`, after every task has succeeded.

On final approval, the work-item status changes to `done`. If there are issues with the implementation, the practical wording for a valid remediation request is:

```
Request remediation: [requirement text or acceptance-criterion identifier] is not met.
Evidence: [brief observed behavior].
Owning task: [task id]
```

Any remediation requested which is out of scope of the original work item or approved specification will be rejected - a new work item should be raised to address it.

## How the loop terminates

Routing is not a judgement call. `tools/adlc/routing.py` picks the first task whose dependencies have all succeeded, and `tools/adlc/policy.py` enforces the attempt caps, loop caps, run budget, no-progress detection, and ownership guard. Both are unit tested under `tests/adlc`, which is the actual guarantee that a remediation loop cannot run forever.

### VS Code setup
`.agents` is not a location VS Code scans by default. `.vscode/settings.json` registers it, so the agents appear in the agent picker and the prompts are available as slash commands:

```json
{
  "chat.agentFilesLocations": { ".agents": true },
  "chat.promptFilesLocations": { ".agents/prompts": true }
}
```

Other harnesses reference the files by path and need no configuration.
