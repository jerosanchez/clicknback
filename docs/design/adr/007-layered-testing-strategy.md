# ADR 007: Layered Testing Strategy

## Status

Accepted

## Context

Testing is crucial for maintaining code quality and preventing regressions. However, not all code requires the same testing approach. Different layers of the application have varying levels of complexity, brittleness, and value from unit testing.

When testing a modular monolith architecture with clear separation of concerns (APIs, services, repositories), the question arises: what should be tested at the unit level, what requires integration testing, and what benefits from end-to-end testing?

Additionally, test code itself is code that requires maintenance. Testing thin layers that are just direct forwarders (e.g., ORM query wrappers) introduces maintenance burden without proportional value, especially when bugs in those layers are caught by higher-level tests.

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

1. **Unit test everything** (services, repositories, utils)
   - Rejected: Too much maintenance burden, requires test DB for repository tests, doesn't scale
2. **Only E2E tests**
   - Rejected: Slow feedback loop, hard to debug business logic issues, expensive to run
3. **Test repositories with fixtures/test records**
   - Rejected: Same maintenance cost, but without the integration test benefits

## Rationale

This approach balances several competing concerns:

- **Developer velocity:** Fast unit test feedback on business logic and HTTP contracts
- **Maintainability:** Avoid testing thin wrapper code that will change; focus on behavior
- **Confidence:**
  - Service tests catch business logic bugs
  - API tests catch HTTP contract violations (wrong status codes, bad error messages)
  - Integration tests verify real DB interactions
  - E2E tests verify complete user workflows
- **Cost:** High ROI on testing effort
  - API layer tests are cheap (mocked services)
  - Repository tests would be expensive (require test DB) with minimal value

### Layered Testing Pyramid

- **Many:** Fast unit tests (services + APIs with error scenarios)
- **Some:** Integration tests (services + repositories + real DB)
- **Few:** E2E tests (complete workflows)

This provides quick feedback (unit tests), real-world confidence (integration tests), and workflow validation (E2E tests) without over-testing implementation details like thin query wrappers.
