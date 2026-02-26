# ADR 001: Adopt Modular Monolith Approach

## Status

Accepted

## Context

ClickNBack needs an application architecture that can grow with the product — starting lean while keeping the codebase honest about domain boundaries. The question is: what top-level structure should the codebase follow, and how tightly or loosely should its domains be coupled?

### Option 1: Microservices from Day One

Each domain (users, merchants, cashback) runs as an independent deployable process communicating over HTTP or a message broker.

```text
# Separate deployable units
users-service/          # Own DB, own deployment
merchants-service/      # Own DB, own deployment
cashback-service/       # Depends on users + merchants via HTTP calls
api-gateway/            # Routes requests to services
```

```python
# cashback-service must call users-service over the network
import httpx

async def get_user(user_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://users-service/users/{user_id}")
        response.raise_for_status()
        return response.json()
```

- ✅ Strong domain isolation; each service can be deployed and scaled independently
- ✅ Technology heterogeneity possible per service
- ❌ Distributed systems complexity: network failures, eventual consistency, distributed tracing
- ❌ Significant operational burden from day one: container orchestration, service discovery, inter-service auth
- ❌ Cross-domain transactions need sagas or two-phase commits — expensive to implement correctly for financial data
- ❌ Local development requires spinning up multiple services simultaneously

### Option 2: Traditional Layered Monolith

A single process organised by technical concern rather than business domain.

```text
app/
├── models/          # All ORM models together
├── services/        # All business logic together
├── api/             # All routes together
└── schemas/         # All Pydantic schemas together
```

```python
# app/services/user_service.py — tightly coupled with merchant logic
from app.models import User, Merchant, Transaction  # Everything imported from one place

class UserService:
    def create_user_with_default_merchant(self, data: dict) -> User:
        merchant = Merchant(...)  # User service reaches into merchant domain
        user = User(...)
        ...
```

- ✅ Simple to set up initially
- ✅ Single deployment, one database
- ❌ Technical coupling: features share the same import scope, leading to entangled logic
- ❌ Hard to onboard: understanding one feature requires reading across all layers
- ❌ Tests become integration-heavy because dependencies are implicit, not injected

### Option 3: Modular Monolith

A single deployable unit internally structured by business domain. Each domain is a self-contained package with its own API, service, repository, models, and exceptions.

```text
app/
├── core/               # Shared infrastructure (DB, config, security)
├── users/              # Fully self-contained domain
│   ├── api.py          # HTTP handlers — wires and exposes the domain
│   ├── services.py     # Business logic
│   ├── repositories.py # Data access
│   ├── models.py       # SQLAlchemy models
│   ├── schemas.py      # Pydantic request/response schemas
│   └── exceptions.py   # Domain-specific exceptions
└── merchants/          # Another self-contained domain
    ├── api.py
    ├── services.py
    └── ...
```

- ✅ Single deployable unit with independent, explicit domain boundaries
- ✅ Cross-domain calls are in-process function calls — no network overhead or partial failure
- ✅ Domains can be extracted to services later with minimal refactoring (interface already defined)
- ✅ Fast to iterate: one database, one deployment pipeline, one set of logs
- ⚠️ All domains share one database — schema migrations must be coordinated
- ⚠️ Cannot scale individual domains independently without extracting them

## Decision

Use a **modular monolith** with domain-driven directory structure as described in Option 3.

Within each domain, layers are strictly separated and interact only through public interfaces:

```python
# app/users/services.py — Business logic isolated from HTTP concerns
class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        enforce_password_complexity: Callable[[str], None],
        hash_password: Callable[[str], str],
    ):
        self.user_repository = user_repository
        self.enforce_password_complexity = enforce_password_complexity
        self.hash_password = hash_password

    def create_user(self, data: dict, db: Session) -> User:
        if self.user_repository.get_by_email(db, data["email"]):
            raise EmailAlreadyRegisteredException(data["email"])
        self.enforce_password_complexity(data["password"])
        hashed_pw = self.hash_password(data["password"])
        user = User(email=data["email"], hashed_password=hashed_pw)
        return self.user_repository.add(db, user)

# app/users/api.py — HTTP handlers delegate entirely to the service
@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: CreateUserRequest,
    service: UserService = Depends(get_user_service),
):
    return service.create_user(data.model_dump(), db)
```

Domain boundaries are enforced by convention:

- Each domain owns its own models, schemas, repositories, and exceptions.
- Domains communicate through their service layer, never by importing another domain's repository directly.
- No circular imports between domains.
- `app/core/` holds only shared infrastructure (database session, configuration, security utilities).

## Consequences

- ✅ Clear separation of concerns within each domain — a new developer can understand `users/` in isolation.
- ✅ Each layer is independently testable via dependency injection (see ADR 007): business logic in `services.py` can be unit-tested with mocked repositories, no database required.
- ✅ Extraction path: if a domain needs independent scaling, its service interface is already defined. Replacing in-process calls with HTTP calls is a localised change.
- ✅ Simple operations: one deployment, one database, one set of logs and metrics to monitor.
- ✅ Fast iteration: cross-domain calls are plain function calls — no serialisation, no network timeouts, no service discovery.
- ⚠️ Shared database means migrations must account for all domains simultaneously; a breaking schema change in one domain affects deployments of all others.
- ⚠️ Scaling the entire application is the only option until a domain is extracted; individual domain traffic spikes cannot be addressed independently.
- ⚠️ Without active discipline on domain boundaries, cross-domain imports can creep in and erode the modularity over time.

## Alternatives Considered

### Microservices from Day One

- **Pros:** Strong domain isolation; independent deployability and scalability per domain; technology choice per service.
- **Cons:** Distributed systems complexity (eventual consistency, distributed transactions, network partitions) is expensive to manage correctly — particularly for financial data where ACID guarantees matter. Operational burden (container orchestration, service discovery, inter-service auth, distributed tracing) is disproportionate at the project's current scale. Local development setup is significantly more complex.
- **Rejected:** The operational and architectural complexity of microservices is only justified when a domain's scaling needs or team-ownership boundaries require it. Those triggers do not yet exist. The modular monolith explicitly preserves the extraction path for when they do.

### Traditional Layered Monolith (Technical Layers)

- **Pros:** Simple to structure initially; no convention required beyond layer names.
- **Cons:** Organising by technical layer (`models/`, `services/`, `api/`) encourages implicit cross-domain coupling. Understanding or modifying a single feature requires jumping across multiple top-level packages. Tests become harder to scope because dependencies are not collocated with the code they support.
- **Rejected:** The modular-by-domain structure is strictly more maintainable. The cost — agreeing on a directory convention — is paid once and then enforced by linting and code review.

## Rationale

ClickNBack's immediate priorities are correctness of financial logic and velocity of feature delivery. Both are best served by keeping the system simple to run (one process, one database) while preventing the accumulation of implicit coupling that makes monoliths hard to maintain.

The modular monolith is the pragmatic middle ground: it provides the same domain isolation that microservices aspire to, without requiring network infrastructure, distributed transaction coordination, or a multi-service local development setup until those investments are justified.

The extraction trigger is explicit: if a domain needs independent deployment, or if team ownership diverges to the point where shared deployments become a coordination burden, the domain's service interface already defines the boundary — replacing in-process calls with HTTP calls requires changes in one place only.
