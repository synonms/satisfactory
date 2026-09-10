## Step 1 — create the work items (once per request)

Open a new chat, select the `request-writer` agent, and paste your request (free text, or an Azure DevOps work item id/URL). Answer its clarifying questions, approve the proposed breakdown, and it writes tickets to `board/new/` such as _00001-1.add-login-feature.user-story.md_.

## Step 2 — advance one work item (repeat until terminal)

Open a new chat and run the dispatcher against a work item id:

`/next 00001-1`

In a harness without slash-command support, paste this instead:

`Follow .agents/prompts/next.prompt.md for work item 00001-1`

It reports the current state, the failsafe check, which agent to run next, and a block of opening instruction text. Then:

1. Open another new chat and select the agent it named.
2. Paste the opening instruction block verbatim.
3. Let that agent finish and write its artifact.
4. Go back to step 2 with the dispatcher, which reads the new artifact, applies the transition, and tells you the next step.

Every step gets its own session, which is what keeps the context window fresh. You stop when the dispatcher reports `ready-for-user` or `blocked`.

You are asked to intervene at exactly two points: approving the specification (`specification-draft → specification-approved`), and final verification at `ready-for-user`.

### First run for a work item
The dispatcher notices there is no `handoffs/00001-1/state.json`, reads the ticket type, derives the flow, and creates the state file at the flow entry point — so for a user story your first real step will be `software-architect`. You do not need to create anything by hand.

### VS Code setup
`.agents` is not a location VS Code scans by default. `.vscode/settings.json` registers it, so the agents appear in the agent picker and the dispatcher is available as `/next`:

```json
{
  "chat.agentFilesLocations": { ".agents": true },
  "chat.promptFilesLocations": { ".agents/prompts": true }
}
```

Other harnesses reference the files by path and need no configuration.
