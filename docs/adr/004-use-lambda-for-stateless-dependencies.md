# ADR-004: Use Lambda Injection for Stateless Dependencies

## Status

Accepted

## Context

In our codebase, we frequently need to inject dependencies into services, such as password hashers, password complexity policies, and similar stateless utilities. There are multiple ways to provide these dependencies. We want to clarify our approach to ensure consistency and testability.

## Decision

For stateless dependencies—such as password hashers, password complexity enforcers, and other policies and similar utilities—we will inject them as callables (functions or lambdas), not as objects or classes. This approach is:

- **Pythonic:** It aligns with Python's preference for simple, explicit, and functional code when state is not required.
- **Testable:** It makes it easy to swap implementations (e.g., with mocks or no-ops) in tests.
- **Decoupled:** It keeps our service layer isolated from infrastructure and implementation details.
- **Consistent with FastAPI:** FastAPI's dependency injection system works naturally with callables.

For dependencies that require state or configuration (e.g., repositories with a DB session), we will inject objects or classes as needed.

## Consequences

- Stateless utilities will be provided as callables, making code simpler and more flexible.
- Tests can easily override these dependencies.
- If a dependency evolves to require state, we will refactor to use an object or class.

## Alternatives Considered

- Injecting objects or classes for all dependencies, regardless of statefulness.
- Using only module-level imports and not injecting dependencies at all.
- Creating dedicated classes for each policy or utility, even when stateless.

## Rationale

Injecting callables for stateless dependencies is a Pythonic and pragmatic approach. It keeps the codebase simple, explicit, and easy to test, while aligning with FastAPI's dependency injection system. This decision avoids unnecessary abstraction and boilerplate for stateless utilities, but leaves the door open to refactor to objects or classes if state or configuration becomes necessary in the future.

