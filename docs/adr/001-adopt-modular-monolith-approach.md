# ADR 001: Adopt Modular Monolith Approach

## Status

Accepted

## Context

When designing architecture, two main patterns emerge:

**Microservices from Day 1:**
- ✅ Strong domain isolation
- ❌ Distributed systems complexity (eventual consistency, service discovery, deployment infrastructure)
- ❌ Higher operational burden (container orchestration, inter-service communication, debugging)

**Monolith:**
- ✅ Simple operations
- ❌ All features tightly coupled

**Modular Monolith (Hybrid):**
- ✅ Single deployable unit with independent domains
- ✅ Can extract services later without major refactoring
- ✅ Fast development + good maintainability
- ✅ Well-established in Python community

## Decision

Use **modular monolith** with domain-driven directory structure:

```
app/
├── core/             # Shared infrastructure
│   ├── database.py
│   ├── config.py
│   └── security.py
├── users/            # Feature domain: self-contained
│   ├── api.py        # HTTP handlers
│   ├── services.py   # Business logic
│   ├── repositories.py  # Data access
│   ├── models.py     # SQLAlchemy models
│   ├── schemas.py    # Pydantic schemas
│   └── exceptions.py
└── merchants/        # Another feature domain
    ├── api.py
    ├── services.py
    └── ...
```

### Layered Architecture Within Each Domain

Services orchestrate business logic, not expose it to API:

```python
# app/users/services.py - Business logic isolated
class UserService:
    def create_user(self, data: dict, repository: UserRepository) -> User:
        if repository.get_by_email(data["email"]):
            raise EmailAlreadyRegisteredException()
        user = User(**data)
        return repository.add(user)

# app/users/api.py - HTTP handlers delegate to services
@router.post("/", response_model=UserResponse)
async def create_user(data: CreateUserRequest, service: UserService = Depends()):
    return service.create_user(data.model_dump())
```

### Domain Boundaries

- Each domain owns its models, schemas, and exceptions
- Domains communicate through services, never directly accessing repos
- No circular dependencies between domains

## Consequences

- ✅ Clear separation of concerns (API/Service/Repository per domain)
- ✅ Easy onboarding—each feature self-contained
- ✅ Testable—layers independently testable with mocks (ADR 007)
- ✅ Future-proof—extract service with minimal refactoring
- ✅ Simple operations—single deployment, database, monitoring
- ⚠️ Shared database means coordinated schema migrations
- ⚠️ Cannot scale individual features independently
- ⚠️ Large codebases need discipline on domain boundaries

## What NOT to Do

### Anti-Pattern: Organize by Technical Layer

```
app/
├── models/       # All ORM together (BAD)
├── services/     # All logic together (BAD)
├── api/          # All handlers together (BAD)
└── schemas/
```

**Problem:** Hard to find related code. Scattered across folders. Features blur together.

### Anti-Pattern: Flat Structure

```
app/
├── user_api.py
├── user_service.py
├── merchant_api.py
├── merchant_service.py
...
```

**Problem:** No clear boundaries. Implicit coupling.

## Rationale

**Pragmatic middle ground for early-stage projects:**

- **Time to market:** Single process + shared DB = faster iteration
- **Maintainability:** Clear boundaries prevent spaghetti code
- **Growth path:** Extract service later if needed, no major refactoring
- **Industry standard:** Netflix, Airbnb before moving to microservices

**When to extract to microservices:**
- A feature needs independent scaling
- Languages/frameworks diverge per feature
- Team grows large enough for service ownership
- Operational infrastructure (Kubernetes, service mesh) is manageable

