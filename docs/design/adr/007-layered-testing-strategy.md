# ADR 007: Layered Testing Strategy

## Status

Accepted

## Context

ClickNBack's modular monolith has three clearly separated layers per domain: API handlers, service classes, and repository classes. The question is: which layers should be covered by unit tests, which require a real database (integration tests), and which should be validated through full HTTP request cycles (end-to-end tests)?

This matters because test code has a maintenance cost. A unit test that verifies a repository method that does nothing but wrap an ORM query provides low signal — the query implementation is an internal detail, and any bug in it is caught by higher-level tests. Conversely, a service method that contains branching logic and raises domain-specific exceptions is exactly the code that benefits from fast, isolated unit test coverage.

Additionally, the API layer has its own testable contract: HTTP status codes, error response shapes, and exception-to-response mappings. These should be verified without involving a real database or the full server stack.

## Decision

We adopt a **layered testing strategy** with three tiers:

### 1. Unit Tests (Pytest with Mocks)

**Scope:** Service layer, API layer (for error handling/status codes), and business logic modules (policies, utilities, validators, etc.)

**Approach:**

- Use pytest fixtures for dependency injection
- Mock external dependencies (repositories, external APIs, services, etc.)
- Use `create_autospec()` for type-safe mocks
- Follow the Arrange-Act-Assert pattern
- Use factory fixtures for generating test data

#### Service Layer Unit Tests

**What to test:** Business logic, validation, exception handling

```python
@pytest.fixture
def user_factory() -> Callable[..., User]:
    def _make_user(**kwargs: Any) -> User:
        defaults = {"email": "test@example.com", ...}
        defaults.update(kwargs)
        return User(**defaults)
    return _make_user

def test_create_user_success(user_service, user_factory):
    # Arrange
    user_repository.get_user_by_email.return_value = None
    
    # Act
    user = user_service.create_user(data, db)
    
    # Assert
    assert user.email == data["email"]
```

#### API Layer Unit Tests

**What to test:** HTTP status codes, error response mappings, response schema correctness

**When to test:**

- Error scenarios → verify correct status codes (409 for conflict, 422 for validation, etc.)
- Exception handling → ensure service exceptions map to proper HTTP responses
- Response serialization → verify schema correctness and field transformations

**When to skip:** Happy path success flows (covered by E2E tests)

```python
from fastapi.testclient import TestClient

@pytest.fixture
def user_service_mock():
    return create_autospec(UserService)

def test_create_user_returns_409_on_duplicate_email(user_service_mock):
    # Arrange
    user_service_mock.create_user.side_effect = EmailAlreadyRegisteredException()
    client = TestClient(app)
    
    # Act
    response = client.post("/users", json={"email": "dupe@example.com", "password": "Test123!"})
    
    # Assert
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]

def test_create_user_returns_422_on_weak_password(user_service_mock):
    # Arrange
    user_service_mock.create_user.side_effect = PasswordNotComplexEnoughException()
    client = TestClient(app)
    
    # Act
    response = client.post("/users", json={"email": "test@example.com", "password": "weak"})
    
    # Assert
    assert response.status_code == 422
    assert "complex" in response.json()["detail"].lower()
```

### 2. Integration Tests

**Scope:** Service + Repository + Database interactions

**Approach:**

- Use a real test database (containerized PostgreSQL via docker-compose)
- Seed test data using factory fixtures
- Test complete workflows with real DB transactions
- Clean up/roll back between tests
- Focus on data persistence and retrieval correctness

**Why later:** As the application grows, integration tests will verify that services correctly integrate with the data layer.

### 3. End-to-End Tests

**Scope:** Full API request/response cycles for key workflows

**Approach:**

- Use `TestClient` from FastAPI to make HTTP requests
- Test complete user journeys (auth, transactions, cashback calculations)
- Include realistic error scenarios
- Verify response formats and status codes match contracts

### What NOT to Unit Test

#### Thin Repositories

Direct ORM query forwarders are not unit tested because:

1. They're implementation details—the service contract and tests do not change if the query is rewritten
2. Bugs are caught by service and integration tests
3. Unit testing requires a test database, adding complexity
4. Maintenance burden is high for minimal benefit
5. ORM migration becomes complicated when tests depend on SQL query details

**Example—No unit test needed:**

```python
class UserRepository:
    def get_user_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()
```

**However, test these if they have complex logic:**

```python
# This would benefit from a unit or integration test
def find_eligible_cashback_users(self, db, min_transactions, min_amount):
    return db.query(User)\
        .join(Transaction)\
        .filter(Transaction.amount > min_amount)\
        .group_by(User.id)\
        .having(func.count(Transaction.id) >= min_transactions)\
        .all()
```

#### Shared Test Infrastructure

- **conftest.py:** Place common fixtures here (factories, DB session, mocked services)
- **Factory fixtures:** Reusable across all test types for consistent test data
- **Test data builders:** Leverage factories to create objects with flexible defaults

## Consequences

- ✅ Fast unit test suite (only business logic and contract verification, no DB)
- ✅ Clear feedback on business logic bugs
- ✅ Early detection of HTTP contract violations (status codes, error mappings)
- ✅ Reduced maintenance burden on thin repository code
- ✅ Layered confidence as we add integration and E2E tests
- ✅ Low cost—API errors use mocked services, so tests run instantly
- ⚠️ Thin repositories aren't directly tested until integration tests are added
- ⚠️ Requires discipline to not over-test simple forwarding methods or happy-path API flows

## Alternatives Considered

### Unit Test Every Layer (Including Repositories)

- **Pros:** 100% unit test coverage of all code paths, including repository queries.
- **Cons:** Repository unit tests require a test database or complex mocking of SQLAlchemy internals. A unit test that mocks `db.query(User).filter(...).first()` is testing mock behaviour, not real behaviour. Any refactoring of the query implementation breaks the test without any actual bug being introduced. The maintenance cost is high with minimal added confidence.
- **Rejected:** Thin ORM wrappers are better covered by integration tests that exercise real database behaviour. Unit-testing them creates a false sense of coverage while adding maintenance burden.

### End-to-End Tests Only

- **Pros:** Maximum realism — tests exercise the full stack on every run.
- **Cons:** E2E tests are slow (every test starts with an HTTP request and a database operation), making tight feedback loops impossible. A business logic bug in a service requires running the full stack to surface it. Debugging failures is harder because the test exercises many layers simultaneously.
- **Rejected:** The feedback loop is too slow for iterative development. Unit tests on the service layer surface business logic bugs in milliseconds; E2E tests are the final confidence check, not the primary feedback mechanism.

### Integration Tests for Repositories (Instead of Deferring Them)

- **Pros:** Repository correctness is verified earlier, before E2E tests are added.
- **Cons:** Integration tests require a live test database, which adds setup complexity and slows the CI pipeline. For simple ORM wrappers, the integration test adds cost without proportional value — the same bug would be surfaced by service integration tests or E2E tests anyway.
- **Rejected:** Repository integration tests are deferred until the application has complex repository logic (joins, aggregations, CTEs) where the test ROI is meaningful. Simple `filter().first()` wrappers do not meet that threshold.

## Rationale

The layered testing strategy maps each test type to a clear responsibility:

- **Service unit tests** verify that business logic branches, validation rules, and exception-raising behaviour work correctly in isolation. Repositories are replaced by `create_autospec()` mocks, so tests run in milliseconds with no database.
- **API unit tests** verify that the HTTP contract is correct: a `EmailAlreadyRegisteredException` maps to a `409`, a `PasswordNotComplexEnoughException` maps to a `422`, and response fields serialise correctly. The service is replaced by a `Mock` — the test focuses on routing and error-mapping code only.
- **Integration tests** (added as the application grows) verify that services and repositories work correctly against a real PostgreSQL instance. These tests are slower and require the database to be running, so they are kept separate from the unit suite.
- **E2E tests** verify complete user workflows through the full HTTP stack. They are the fewest in number and the slowest to run; they act as a final sanity check, not a debugging tool.

This partitioning gives the fastest possible feedback on the most common class of bug (business logic errors in services) while avoiding the maintenance overhead of testing implementation details (ORM query internals) or duplicating coverage at multiple layers.
