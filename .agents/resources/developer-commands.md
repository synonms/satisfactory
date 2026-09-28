# Developer Commands

Canonical build, test, and validation commands. Agents must use these rather than inventing their own, because command drift between runs produces spurious failures and triggers unnecessary remediation loops.

> **Status:** the software-factory framework lives under `.agents/` and `tools/`, with sample projects under `playground/`. The .NET commands below target the playground solution and must be confirmed against the real solution file for any other work. Any agent that has to deviate from this document must record the command it actually ran, and why, in its activity `result`.

## Shell

PowerShell (`pwsh`) on Windows. Chain commands with `;`.

## Work Items

Run from the repository root. Commands return compact JSON for agent consumption.

| Purpose | Command |
| --- | --- |
| Create an approved request | `python -m tools.work_items create-request --input request.json` |
| Retrieve a work item | `python -m tools.work_items get {work-item-id}` |
| List work items | `python -m tools.work_items list` |
| Change lifecycle status | `python -m tools.work_items change-status {work-item-id} {status}` |
| Author a plan with a specification | `python -m tools.work_items add_spec {work-item-id} --input plan.json` |
| Author a plan without a specification | `python -m tools.work_items add_tasks {work-item-id} --input tasks.json` |
| Revise a draft plan | `python -m tools.work_items revise_spec {work-item-id} --input plan.json` or `revise_tasks` |
| Read the plan | `python -m tools.work_items get_plan {work-item-id}` |
| Approve the plan (human gate) | `python -m tools.work_items approve_plan {work-item-id}` |
| Read a task | `python -m tools.work_items get_task {work-item-id} {task-id}` |
| Record an outcome | `python -m tools.work_items record_activity {work-item-id} {task-id} --input activity.json` |
| Run work-item tests | `python -m pytest tests/work_items -q` |

## ADLC Routing

| Purpose | Command |
| --- | --- |
| Ask what happens next | `python -m tools.adlc next {work-item-id}` |
| Report work-item progress and metrics | `python -m tools.adlc status {work-item-id}` |
| Check an agent's changed files against the ownership guard | `python -m tools.adlc guard {agent} {files...}` |
| Run routing and failsafe tests | `python -m pytest tests/adlc -q` |

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
5. Record every command run, and its result, in the activity `result`.

## Test failure signatures

The no-progress failsafe depends on a stable failure signature. When tests fail, list their fully qualified names sorted, derive a stable signature from that set, and pass it as `failureSignature` on the activity payload. Two consecutive identical signatures block the task. See `.agents/workflows/adlc.md`.

## Other stacks

The `playground/dotnet` solution is the only stack currently wired up. When another is added, extend this document with its restore, build, lint, and test commands before running the ADLC workflow against it.
