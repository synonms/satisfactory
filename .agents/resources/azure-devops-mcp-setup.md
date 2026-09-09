# Azure DevOps MCP Setup

The `request-writer` agent optionally pulls its input from an Azure DevOps work item instead of a free-text prompt. This requires an MCP server that exposes a work item retrieval tool (e.g. `wit_get_work_item` from the `@azure-devops/mcp` package) to be connected in whichever IDE/harness is running the agent.

This setup is harness-specific - there is no single config file that works everywhere. Configure the server using the mechanism provided by your own tooling, using the examples below as a starting point.

## VS Code

Create `.vscode/mcp.json` in the consuming project:

```json
{
	"inputs": [
		{
			"id": "ado_org",
			"type": "promptString",
			"description": "Azure DevOps organization name (e.g. the ORG in https://dev.azure.com/ORG)"
		}
	],
	"servers": {
		"azure-devops": {
			"type": "stdio",
			"command": "npx",
			"args": ["-y", "@azure-devops/mcp", "${input:ado_org}"]
		}
	}
}
```

## Claude Desktop / Cursor

These tools use a `mcpServers` key (rather than VS Code's `servers`) and do not support the `${input:...}` prompt syntax, so the organization must be supplied directly:

```json
{
	"mcpServers": {
		"azure-devops": {
			"command": "npx",
			"args": ["-y", "@azure-devops/mcp", "<your-organization>"]
		}
	}
}
```

Consult your harness's documentation for the exact config file name and location.

## Authentication

`@azure-devops/mcp` authenticates via Azure CLI credentials (`az login`) or an Entra ID token, depending on how it is invoked. If the request-writer agent reports it cannot reach Azure DevOps, verify the MCP server is connected and the user is signed in before retrying.
