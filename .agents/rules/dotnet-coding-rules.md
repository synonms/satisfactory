# .NET Coding Rules

Use these rules for C#, .NET, ASP.NET, Blazor, MAUI, WPF, and related .NET implementation work in this repository.

## General C# Standards

- Follow the style, naming, nullable-reference-type, analyzer, and formatting conventions already present in the affected project.
- Prefer explicit, readable C# over clever or highly compressed code.
- Keep public contracts stable unless the approved specification requires a contract change.
- Do not introduce new NuGet packages when an existing repository dependency can satisfy the requirement.
- Avoid one-letter variable names and unrelated formatting churn.

## Architecture and Domain Boundaries

- Preserve Domain-Driven Design boundaries where they already exist.
- Keep domain logic in the domain layer and orchestration in the application layer.
- Keep API, UI, persistence, and infrastructure concerns out of domain models.
- Respect existing dependency injection, configuration, persistence, serialization, logging, validation, and error-handling conventions.
- Treat tenant isolation, authorization, validation, data integrity, and security requirements as mandatory.

## ASP.NET and API Work

- Follow existing endpoint, controller, minimal API, middleware, authentication, authorization, model-binding, validation, and response-shaping patterns.
- Preserve OpenAPI, serialization, versioning, and error-contract behavior unless the specification requires a change.
- Keep transport DTOs separate from domain models when that separation exists.

## Blazor, MAUI, and WPF Work

- Follow existing component, view-model, binding, state-management, navigation, validation, styling, and accessibility conventions.
- Keep UI logic and domain/application logic separated according to the affected project pattern.
- Validate user-facing behavior with the narrowest appropriate automated or manual check available in the repository.

## Tests

- Add focused unit, integration, API, contract, UI, or regression tests based on the behavior and boundary changed.
- Follow existing test framework, fixture, assertion, mocking, data-builder, and naming patterns.
- Prefer tests that verify observable behavior, persisted state, messages, or public contracts over private implementation details.
- Do not weaken, skip, or rewrite assertions just to make a failing implementation pass.