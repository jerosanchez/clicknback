---
name: write-integration-tests
type: skill
description: Write integration tests against a real database
---

# Skill: Write Integration Tests

Write integration tests for endpoints. Integration tests use a real PostgreSQL database with transaction rollback for isolation.

## When to Write Integration Tests

- After unit tests are complete and passing
- For critical endpoints (create, update, delete, complex queries)
- **For auth/security endpoints (login, refresh, logout, password change)** — unit test
  mocks cannot verify DB persistence; a missing `await uow.commit()` is invisible to
  `AsyncMock()`. An integration test that calls login then refresh immediately exposes
  any missing commit. These MUST have integration tests.
- For happy path + most important failure modes
- NOT for every edge case (covered by unit tests)

## Testing Approach

- **Real DB**: Tests execute against actual PostgreSQL
- **Isolation**: Each test runs inside a rolled-back outer transaction; data doesn't persist
- **Fixtures**: Use `http_client` (unauthenticated), `user_http_client` (user token), `admin_http_client` (admin token)
- **One test per endpoint**: Happy path + critical failure modes

## Workflow

### Step 1: Confirm Test Database

Set `TEST_DATABASE_URL` environment variable:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/clicknback_test"
```

### Step 2: Create Integration Test File

Create `tests/integration/<module>/test_<module>_<endpoint>.py`:

```python
# tests/integration/merchants/test_merchants_create.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_merchant_persists_to_db(admin_http_client: AsyncClient):
    # Arrange
    merchant_data = {
        "name": "Integration Test Merchant",
        "default_cashback_percentage": 15,
        "active": True
    }
    
    # Act
    response = await admin_http_client.post("/merchants", json=merchant_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Integration Test Merchant"
    assert data["default_cashback_percentage"] == 15
    
    # Verify in DB (within same transaction, before rollback)
    merchants = await admin_http_client.get("/merchants")
    assert any(m["name"] == "Integration Test Merchant" for m in merchants.json()["items"])
```

### Step 3: Test Happy Path + Critical Failures

- Happy path: successful operation, correct response, data persisted
- Auth failure: 401/403 if endpoint requires role
- Validation failure: 422 with error code
- Not found: 404 if resource doesn't exist
- Duplicate/idempotency: 409 if applicable

## Transaction Isolation

See `tests/integration/conftest.py` for setup. Tests run within an outer transaction that rolls back after each test. This ensures:

- No data persists between tests
- Tests don't interfere with each other
- No cleanup code needed

## Quality Criteria

- [ ] Happy path test for each endpoint
- [ ] Critical failure modes tested (auth, validation, not found)
- [ ] Response includes all expected fields
- [ ] Database changes verified (queries within test transaction)
- [ ] Run `make test-integration` after adding/changing/removing integration tests (not `pytest`)
- [ ] Run `make all-qa-gates` as the final check after completing a task

---
