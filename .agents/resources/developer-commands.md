# Developer Commands

Canonical build, test, and validation commands. Agents must use these rather than inventing their own, because command drift between runs produces spurious failures and triggers unnecessary remediation loops.

> **Status:** this repository currently contains only the software-factory framework under `.agents/`. There is no solution or project yet. The .NET commands below are the intended defaults and must be confirmed against the real solution file as soon as it is added. Any agent that has to deviate from this document must record the command it actually ran, and why, in its handoff artifact.

## Shell

PowerShell (`pwsh`) on Windows. Chain commands with `;`.

## .NET

Run from the repository root unless stated otherwise.

| Purpose | Command |
| --- | --- |
| Restore | `dotnet restore` |
| Build the solution | `dotnet build --no-restore` |
| Build a single project (narrowest first) | `dotnet build .\path\to\Project.csproj --no-restore` |
| Run all tests | `dotnet test --no-build` |
| Run one test project | `dotnet test .\path\to\Project.Tests.csproj --no-build` |
| Run a filtered set of tests | `dotnet test .\path\to\Project.Tests.csproj --no-build --filter "FullyQualifiedName~MyFeature"` |
| Format check | `dotnet format --verify-no-changes` |

## Command discipline

1. Run the **narrowest** relevant command first: the single project build, then the single test project, then wider scopes.
2. Widen to the full solution build and test run only when the change crosses project, public-contract, persistence, security, messaging, API, or UI boundaries.
3. Never claim a command passed unless it completed with a zero exit code. Record the exit code or the failure output.
4. Distinguish failures introduced by the current change from pre-existing failures. Capture the baseline before making changes when the suite is not already green.
5. Record every command run, and its result, in the handoff artifact.

## Test failure signatures

The `sdlc` no-progress failsafe depends on a stable failure signature. When reporting failing tests, list their fully qualified names, sorted, so that consecutive runs can be compared reliably. See `.agents/workflows/sdlc.md`.

## Other stacks

No frontend or other technology stack exists in this repository yet. When one is added, extend this document with its restore, build, lint, and test commands before running the `sdlc` workflow against it.
