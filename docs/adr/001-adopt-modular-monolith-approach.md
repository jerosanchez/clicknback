# ADR-001: Adopt Modular Monolith Approach

## Status

Accepted

## Context

When designing the architecture for this project, we considered two main options: building a system as a set of independent microservices from the start, or adopting a modular monolith approach. Microservices offer strong isolation, independent deployment, and scalability, but introduce significant complexity in terms of infrastructure, deployment, and inter-service communication. For many early-stage or evolving projects, this overhead can outweigh the benefits.

The modular monolith approach, on the other hand, keeps the codebase within a single deployable unit but enforces clear boundaries between features/domains and layers.

This approach is common in FastAPI and other modern Python backends, and is a well-established pattern in the broader software engineering community.

## Decision

- The project will be structured using a layered architecture:
	- **API layer**: Handles HTTP requests and responses, input validation, and serialization.
	- **Service layer**: Contains business logic and orchestrates operations between the API and repository layers.
	- **Repository layer**: Manages data persistence and retrieval, abstracting the underlying database or storage mechanism.
- Code will be organized by feature/domain, with each feature (e.g., users, merchants) having its own module containing all relevant logic for that domain.
- This structure is intended to ease future refactoring, including the potential extraction of features into microservices.

## Consequences

- Improved separation of concerns and maintainability.
- Easier onboarding for new developers, as each feature is self-contained.
- Facilitates future migration to microservices if/when required.
- May introduce some duplication or indirection, but the benefits for scaling and maintainability outweigh these costs.

## Alternatives Considered

- Organizing code strictly by technical layer (e.g., all models, all services, all repositories in separate folders).
- Using a flat structure without clear separation of concerns.

## Rationale

This decision aligns with best practices for scalable Python backends and prepares the codebase for future growth.

It allows to balance maintainability, scalability, and simplicity, while keeping open the option to migrate to microservices as requirements evolve.

