# ADR 003: API Module as Composition Root

## Status

Accepted

## Context

ClickNBack uses FastAPI's dependency injection system (`Depends()`) to wire services, repositories, and policies together. Each service constructor requires its collaborators to be created and passed in at request time. The question is: where should this construction and wiring logic live?

### Option 1: Centralised Application-Level Container

A single module builds and exposes all dependencies for the entire application. All feature modules import their wired objects from this central location.

```python
# app/composition_root.py — builds everything in one place
from app.core.database import get_db
from app.users.repositories import UserRepository
from app.users.services import UserService
from app.users.policies import enforce_password_complexity
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(
        user_repository=UserRepository(),
        enforce_password_complexity=enforce_password_complexity,
        hash_password=lambda pw: pwd_context.hash(pw),
    )

# app/merchants/composition_root.py would also live here, coupling all features
```

- ✅ Single file to inspect all application wiring
- ❌ All domain imports converge in one module — a change in any domain forces a review of the global container
- ❌ Adding a new dependency to `MerchantService` requires editing the shared container, not the merchant module
- ❌ Test overrides must target a central location rather than the module under test

### Option 2: Feature-Level Composition (per API module)

```python
# app/users/api.py - Wiring close to usage
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    policy = PasswordPolicy()
    return UserService(repo, policy)

@router.post("/")
async def create_user(service = Depends(get_user_service)):
    ...
```

- ✅ Explicit and colocated with usage
- ✅ Each feature manages its own dependencies
- ✅ Easy to override in tests
- ✅ Aligns with FastAPI idioms

### Option 3: DI Container Framework (python-dependency-injector)

```python
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    db = providers.Singleton(Database, config.db.url)
    user_service = providers.Factory(
        UserService,
        repository=providers.Factory(UserRepository, db=db)
    )
```

- ✅ Powerful for complex scenarios
- ❌ Overkill for Flask/FastAPI micro-services
- ❌ Learning curve, harder to debug

## Decision

Use **API module as composition root** for each feature:

```python
# app/users/api.py - Dependency wiring colocated with endpoints

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.users.services import UserService
from app.users.repositories import UserRepository
from app.users.policies import PasswordPolicy

router = APIRouter(prefix="/users", tags=["users"])

# Provider functions define how to construct dependencies
def get_password_policy() -> PasswordPolicy:
    return PasswordPolicy()

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    policy: PasswordPolicy = Depends(get_password_policy),
) -> UserService:
    return UserService(repo, policy)

# Endpoints receive fully-injected service
@router.post("/")
async def create_user(
    data: CreateUserRequest,
    service: UserService = Depends(get_user_service),
):
    return service.create_user(data)
```

### Features of This Approach

1. **Explicit:** Wiring is visible code, not hidden in config
2. **Composable:** Dependencies reference other dependencies via Depends()
3. **Testable:** Override with `app.dependency_overrides`
4. **Modular:** Each feature manages its own composition
5. **Pythonic:** Leverages FastAPI's design idioms

### Testing Example

```python
# tests/users/test_users_api.py

def test_create_user_returns_409_on_duplicate(client):
    # Arrange
    mock_service = Mock(spec=UserService)
    mock_service.create_user.side_effect = EmailAlreadyRegisteredException()

    # Override dependency for this test
    app.dependency_overrides[get_user_service] = lambda: mock_service

    # Act
    response = client.post("/users", json={...})

    # Assert
    assert response.status_code == 409

    # Cleanup
    app.dependency_overrides.clear()
```

## Consequences

- ✅ Dependency wiring is explicit and colocated with usage
- ✅ Each feature manages its own composition root
- ✅ Testability improved via dependency_overrides
- ✅ Clear separation of concerns within each API module
- ✅ Easy to extend or replace dependencies per-feature
- ⚠️ Wiring spread across multiple modules (not centralized)
- ⚠️ If project grows very large, may become harder to track all compositions

## Alternatives Considered

### Centralized Composition Root

- **Pros:** Single view of all dependencies
- **Cons:** Couples all features together, centralized bottleneck
- **Rejected:** Harder to scale to multiple teams/domains

### Dependency Injection Framework

- **Pros:** Powerful, flexible, industry-standard in some ecosystems
- **Cons:** Overkill for FastAPI, adds learning curve and complexity
- **Rejected:** FastAPI's built-in DI is sufficient and more idiomatic

### Global Dependency Imports

- **Pros:** Minimal boilerplate
- **Cons:** Hidden dependencies, hard to test, implicit contracts
- **Rejected:** Violates explicit-is-better-than-implicit principle

## Rationale

FastAPI's dependency injection system is explicitly designed for this pattern. `Depends()` is composable — a provider function can itself declare dependencies, which FastAPI resolves recursively. `dependency_overrides` replaces any provider by its function reference, which is locally defined in the feature module. Lazy evaluation means nothing is constructed until a request arrives at an endpoint that requires it.

The per-feature composition root aligns directly with ADR 001's modular monolith structure: each domain package is self-contained. Its `api.py` is the only file that needs to know how to construct the domain's service, because `api.py` is the only consumer of that service. A new developer working on the `users` domain reads `app/users/api.py` and immediately sees what collaborators `UserService` requires — no global container to trace.

For ClickNBack specifically, this approach keeps testing lightweight: each endpoint's provider function can be replaced with a `Mock` via `dependency_overrides` in a single line, allowing unit tests to run against the full routing layer without any database or infrastructure (see ADR 007).

**When to reconsider:**

- The project has many domains (50+) and a cross-cutting concern (e.g., audit logging, rate limiting) must be injected into every service — at that point a partial central registry for shared infrastructure makes sense alongside per-feature wiring.
- Multiple teams own different domains and need a guaranteed-consistent construction policy enforced by CI — a validation layer over the existing providers can achieve this without abandoning the per-feature structure.
