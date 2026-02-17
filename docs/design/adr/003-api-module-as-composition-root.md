# ADR 003: API Module as Composition Root

## Status

Accepted

## Context

In FastAPI projects, dependencies (services, policies, repositories) must be composed and injected. Where should this wiring happen?

### Option 1: Centralized Container

```python
# composition_root.py
@contextmanager
def create_user_service():
    repo = UserRepository(db)
    policy = PasswordPolicy()
    yield UserService(repo, policy)
```

- ✅ Single place to understand wiring
- ❌ Couples features together
- ❌ Hard to extend per-feature logic

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

FastAPI's dependency injection system is designed to work exactly like this approach. The framework provides:

- `Depends()` - Mark dependencies
- `dependency_overrides` - Test-time replacement
- Composability - Dependencies can reference other dependencies
- Lazy evaluation - Only construct when needed

This approach balances **clarity** (explicit wiring), **maintainability** (per-feature composition), and **testability** (easy overrides) without requiring external frameworks or complex configuration.

**When to reconsider:**

- Project has 50+ features and composition becomes unwieldy (migrate to centralized container)
- Multiple teams own different features and need guaranteed composition consistency
- Deployment configuration needs to vary per environment (add configuration layer)
