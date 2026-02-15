# ADR-003: API Module as Composition Root

## Status

Accepted

## Context

In FastAPI and similar Python web projects, dependencies such as services, policies, and repositories must be composed and injected. There are several ways to organize this wiring, and the choice impacts clarity, maintainability, and testability.

## Decision

We will use the API module (where the router and endpoints are defined) as the composition root for each feature or domain. This means that dependencies will be wired up and injected via provider functions (e.g., `get_user_service`) directly in the API module, close to where they are used.

## Consequences

- Dependency wiring is explicit and easy to follow, as it is colocated with the endpoints.
- Each feature/module can manage its own composition root, supporting modularity and separation of concerns.
- Testability is improved, as dependencies can be easily overridden using FastAPI's `dependency_overrides`.
- If the project grows significantly, we can refactor to a more centralized or container-based approach if needed.

## Alternatives Considered

- Centralizing all dependency wiring in a dedicated `composition_root.py` or `container.py` module.
- Using a dependency injection framework (e.g., `python-dependency-injector`) to manage all dependencies in a global container.
- Defining dependencies only at the global app level, not per-feature/module.

## Rationale

Keeping the composition root in the API module is the most idiomatic and maintainable approach for FastAPI projects of this size and structure. It leverages FastAPI's dependency injection system, keeps wiring close to usage, and supports modularity. More centralized or container-based approaches add complexity and are only justified for very large or highly dynamic projects. This decision balances clarity, maintainability, and flexibility for future growth.
