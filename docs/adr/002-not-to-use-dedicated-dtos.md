# ADR-002: Not to Use Dedicated DTOs for Service Boundaries

## Status
Accepted

## Context

In layered architectures, it is common to introduce dedicated Data Transfer Objects (DTOs) to decouple the service layer from both the API (upwards) and the persistence/repository (downwards) layers. DTOs are typically implemented as typed classes (e.g., dataclasses, Pydantic models, or similar) to provide structure, validation, and type safety, and to avoid leaking implementation details between layers.

However, introducing and maintaining dedicated DTOs can add significant boilerplate and complexity, especially in smaller projects or when requirements are evolving quickly. In practice, many Python projects opt for more pragmatic approaches, such as using plain dicts or direct model instances for data transfer.

## Decision

We have decided not to introduce dedicated DTOs for service boundaries at this stage. Specifically:

- For service to repository/persistence communication, we use the persistence model directly, without a separate DTO abstraction.
- For API to service communication, we use plain Python dicts as untyped DTOs to avoid coupling the service layer to persistence models, while also minimizing boilerplate.

This approach keeps the codebase simple and leverages Python's dynamic features, which is suitable for our current project size and complexity.

## Consequences

- Faster development and less boilerplate.
- Tighter coupling between business logic and persistence layer, as no DTO abstraction is used downwards.
- Using plain dicts for API/service boundaries means less type safety and validation compared to dedicated DTOs.
- If the project grows in complexity, we may revisit this decision and refactor to introduce DTOs or typed abstractions for more robustness and decoupling.

## Alternatives Considered

- Implementing dedicated DTOs (dataclasses) for both upward (API) and downward (repository) communication, following DDD or layered architecture principles.
- Using typed abstractions for all service boundaries to maximize decoupling and type safety.

## Rationale

This decision is made for pragmatic reasons, balancing maintainability and development speed. We acknowledge the trade-offs and have documented this ADR to make future revisiting easier if requirements change. If the project requirements evolve or the codebase grows, we may adopt a more layered and type-safe approach with dedicated DTOs for all service boundaries.
