# .NET Implementation Reference

Use this reference when a specification affects C#, .NET, ASP.NET, Blazor, MAUI, WPF, or related .NET projects.

## Discovery Checklist

Before editing, identify:

1. The affected solution, project, and test project.
2. The nearest equivalent implementation and test.
3. The owning architectural layer: domain, application, infrastructure, API, UI, persistence, or test support.
4. Public contracts affected by the change: endpoints, DTOs, events, messages, database schema, configuration, UI routes, or component parameters.
5. Dependency injection, configuration, persistence, serialization, and validation patterns used by the affected project.

## Implementation Checklist

1. Restore dependencies if required by the repository commands.
2. Make the smallest coherent production-code change that satisfies the approved specification.
3. Add or update focused tests in the nearest appropriate test project.
4. Run the narrowest relevant test command first.
5. Build the affected project or solution.
6. Run broader integration, API, contract, persistence, or UI checks when the change crosses those boundaries.

## Validation Guidance

- Prefer documented commands from `.agents/resources/developer-commands.md` when present.
- If no command is documented, use the nearest existing solution or project command such as `dotnet test`, `dotnet build`, or the affected test-project command.
- Do not report validation as passed unless the command completed successfully.
- If a command fails for an unrelated, pre-existing, or environmental reason, record the failure and continue only when the requested work can still be assessed safely.

## Common .NET Surfaces

- Domain model or value-object changes usually require domain unit tests.
- Application command/query handler changes usually require handler tests or integration tests depending on repository conventions.
- API endpoint changes usually require API, integration, serialization, validation, authorization, and OpenAPI checks where available.
- Persistence changes usually require migration/schema checks and integration tests.
- UI changes usually require component, view-model, interaction, accessibility, or snapshot/visual checks where available.