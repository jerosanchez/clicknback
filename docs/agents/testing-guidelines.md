# Testing Guidelines for AI Agents

Self-contained reference for writing tests in ClickNBack. When asked to write a new test suite, follow every rule here and mirror the structure of the examples below exactly.

---

## 1. Testing Philosophy

### Test Pyramid

| Layer | Count | Description |
| --- | --- | --- |
| Unit Tests | Many | Fast, isolated, all dependencies mocked |
| Integration Tests | Some | Real database, containers (see §14) |
| E2E Tests | Few | Full HTTP flows via Docker Compose (see §15) |

### What to Test

✅ Service business logic
✅ API response/error mapping
✅ Policies and validators
✅ Utilities and builders
❌ Thin repository implementations
❌ Framework internals (FastAPI routing, SQLAlchemy engine)

### Quality Standards

- **AAA pattern** with explicit `# Arrange`, `# Act`, `# Assert` comments (or `# Act & Assert` when using `pytest.raises`).
- Tests are **fully independent** — no shared mutable state between tests.
- Unit tests run in **< 100 ms**.
- **Descriptive names:** `test_{sut}_{result}_on_{condition}` — e.g., `test_create_user_raises_on_email_already_registered`, `test_create_user_returns_201_on_success`, `test_list_merchants_returns_403_on_non_admin`. The `_on_` connector is mandatory and reads as a natural sentence: "*create_user* **raises** *on* email already registered".
- **No magic values:** extract literals into named variables — e.g., `out_of_range_percentage = 150.0`, not a bare `150.0`.
- **Don't over-specify test data:** When a value passes through a mock without being inspected, use the factory defaults. Only set a specific value when *that value is under test*.
- **Full type hints everywhere** (fixtures, helpers, test functions). Exception: `Mock()` assignments are inferred correctly and don't need annotation.

---

## 2. File Structure and Naming

```text
tests/
    conftest.py                         # shared fixtures only
    auth/
        test_auth_api.py
        test_auth_services.py
        test_token_providers.py
    core/
        test_current_user.py
        errors/
            test_builders.py
    merchants/
        test_merchants_api.py
        test_merchants_policies.py
        test_merchants_services.py
    users/
        test_users_api.py
        test_users_policies.py
        test_users_services.py
```

**Rule:** `tests/{module}/test_{module_name}_{layer}.py`
Maps exactly to `app/{module}/{layer}.py` — e.g., `tests/users/test_users_services.py` ↔ `app/users/services.py`.

---

## 3. Import Order

Always follow this order with blank lines between groups:

```python
# 1. stdlib
from typing import Any, Callable, Generator
from unittest.mock import Mock, create_autospec

# 2. third-party
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 3. local — core / infrastructure first, then the module under test
from app.core.current_user import get_current_admin_user
from app.core.database import get_db
from app.core.errors.codes import ErrorCode
from app.main import app
from app.users.composition import get_user_service
from app.users.exceptions import EmailAlreadyRegisteredException
from app.users.models import User
from app.users.services import UserService
```

---

## 4. conftest.py — Shared Fixtures

`tests/conftest.py` contains **only** fixtures that are reused by more than one test module. **Before** defining any fixture locally, read `conftest.py` first — if a factory or input-data builder for the model you need already exists there, reuse it rather than defining a local one.

Expect to find two types of shared fixtures per domain model:

| Pattern | Type signature | Purpose |
| --- | --- | --- |
| `{model}_factory` | `Callable[..., Model]` | Creates a model instance with sensible defaults; any field is overridable via kwargs |
| `{model}_input_data` | `Callable[[Model], dict[str, Any]]` | Builds the input dict passed to a service or API endpoint from a model instance |

### Factory Pattern

```python
# tests/conftest.py
from typing import Any, Callable
import pytest
from app.users.models import User

@pytest.fixture
def user_factory() -> Callable[..., User]:
    def _make_user(**kwargs: Any) -> User:
        defaults: dict[str, Any] = {
            "id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
            "email": "alice@example.com",
            "hashed_password": "hashed_pw",
            "role": "admin",
            "active": True,
            "created_at": "2026-02-15T18:42:18.340977",
        }
        defaults.update(kwargs)
        return User(**defaults)
    return _make_user
```

Usage — pass only the fields that matter for the test:

```python
user = user_factory()                        # all defaults
user = user_factory(active=False)            # override one field
user = user_factory(role=UserRoleEnum.user)  # override another
```

### Input Data Fixture Pattern

```python
@pytest.fixture
def user_input_data() -> Callable[[User], dict[str, Any]]:
    def _build(user: User) -> dict[str, Any]:
        return {
            "email": user.email,
            "password": "PlaceholderPass1!",   # placeholder — not under test
        }
    return _build
```

---

## 5. Unit Testing Services

**References:** `tests/users/test_users_services.py`, `tests/auth/test_auth_services.py`, `tests/merchants/test_merchants_services.py`

### Structure

1. Fixtures (in this order):
   - One fixture per **dependency** (callable dependencies use `Mock()`, ABCs use `create_autospec`)
   - One fixture that **assembles** the service, injecting the dependency fixtures
2. Module-level helper functions (if any)
3. Test functions

### Mocking Rules

| Dependency type | How to mock |
| --- | --- |
| An ABC / interface class | `create_autospec(TheABC)` — returns `Mock` |
| A `Callable[[X], Y]` (e.g. `hash_password`, `enforce_*`) | `Mock()` (optionally with `return_value`) |
| `db: Session` inside a test | `Mock(spec=Session)` — local variable, not a fixture |

> **Return type of mock fixtures must be `Mock`, not the ABC.**
> `-> Mock` lets the type checker resolve `.return_value` and `.side_effect`.

**Canonical example:** `tests/users/test_users_services.py` — read this file before writing a new service test. `tests/merchants/test_merchants_services.py` and `tests/auth/test_auth_services.py` follow the exact same structure.

### Service Test Checklist

- [ ] One mock fixture per dependency
- [ ] Service fixture assembles the class, injecting all mocks
- [ ] `db = Mock(spec=Session)` created locally inside each test (not shared, unless referenced by nearly every test)
- [ ] Each mock is configured in **Arrange**, not in the fixture
- [ ] Happy path, every `raise`, every `side_effect` branch covered
- [ ] `pytest.raises` used with `# Act & Assert` comment

---

## 6. Unit Testing API Endpoints

**References:** `tests/users/test_users_api.py`, `tests/auth/test_auth_api.py`, `tests/merchants/test_merchants_api.py`

### Testing Scope

✅ Status codes match `fastapi.status` constants
✅ Response body maps model fields correctly
✅ Domain exceptions → correct HTTP status + error code
✅ Unhandled exceptions → 500
✅ Non-admin (403) — verifies the endpoint calls the correct admin-guarded dependency
✅ Query/path parameter constraint validation — endpoints with `ge`/`le` constraints must have boundary value tests covering both valid and invalid sides
❌ Unauthenticated (401) per endpoint — the 401 is raised inside the auth helper (`get_current_user`), which is already tested in `tests/core/test_current_user.py`; testing it on every endpoint is redundant
❌ Business logic (belongs in service tests)
❌ Service argument forwarding — verifying that query/path params are passed through to the service is redundant; it is already covered implicitly by the success test and will be exercised further in integration/E2E tests

### API Test Structure

1. `{service}_mock` fixture — `create_autospec(TheService)`, return type `Mock`
2. `client` fixture — overrides all FastAPI dependencies, yields `TestClient`, clears overrides
3. Module-level `_input_data()` function — returns a plain `dict` (not a fixture, no `@pytest.fixture`)
4. Module-level assertion helpers — `_assert_*_response`, `_assert_error_payload`
5. Success test
6. Parametrized exceptions test (status codes + codes only)
7. Individual detail tests for each domain exception (full error body)
8. Boundary value tests for any endpoint with constrained query/path params (two parametrized tests — valid and invalid)

### `client` Fixture Pattern

```python
@pytest.fixture
def client(service_mock: Mock) -> Generator[TestClient, None, None]:
    def mock_get_db() -> Generator[Mock, None, None]:
        yield Mock()

    app.dependency_overrides[get_db] = mock_get_db
    app.dependency_overrides[get_the_service] = lambda: service_mock

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()   # always clean up
```

**For endpoints that require authentication**, also override the auth dependency in `client`:

```python
app.dependency_overrides[get_current_admin_user] = lambda: Mock()
```

**For testing the non-admin (403) scenario**, use a dedicated `non_admin_client` fixture that overrides the auth dependency to raise a forbidden error. Do **not** add an `unauthenticated_client` fixture or a `test_*_returns_401_on_unauthenticated` test — 401 behaviour lives inside the auth helper and is already covered in `tests/core/test_current_user.py`.

```python
@pytest.fixture
def non_admin_client(
    service_mock: Mock,
) -> Generator[TestClient, None, None]:
    def raise_forbidden() -> None:
        raise forbidden_error("Admin access required.", {})

    app.dependency_overrides[get_current_admin_user] = raise_forbidden
    # ... remaining overrides ...
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_endpoint_returns_403_on_non_admin(
    non_admin_client: TestClient,
) -> None:
    # Act
    response = non_admin_client.get("/api/v1/resource")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
```

> **When to use `@pytest.mark.parametrize` vs individual tests:** use parametrize when you are sweeping over a set of equivalent values (boundary numbers, status codes for different exceptions). Use individual named tests when each scenario has a distinct semantic identity — like distinct authorisation roles.

**For endpoints with constrained query or path parameters** (FastAPI `ge`, `le`, etc.), add two parametrized tests — one for values that are valid (expect 200), one for values that are invalid (expect 422). Always drive values from `settings.*` rather than hardcoding. Comment each entry to document its role:

```python
@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",                                         # below minimum page
        "page_size=0",                                    # below minimum page_size
        f"page_size={settings.max_page_size + 1}",        # above maximum page_size
    ],
)
def test_list_resource_returns_422_on_invalid_pagination_params(
    client: TestClient,
    query_string: str,
) -> None:
    # Act
    response = client.get(f"/api/v1/resource?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "query_string",
    [
        "page=1",                                          # minimum page
        "page_size=1",                                     # minimum page_size
        f"page_size={settings.default_page_size}",         # default page_size
        f"page_size={settings.max_page_size}",             # maximum page_size
    ],
)
def test_list_resource_returns_200_on_valid_pagination_params(
    client: TestClient,
    service_mock: Mock,
    query_string: str,
) -> None:
    # Arrange
    service_mock.list_resource.return_value = ([], 0)

    # Act
    response = client.get(f"/api/v1/resource?{query_string}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
```

### Input Data: Module Function vs Fixture

Use a **module-level function** (no `@pytest.fixture`) when input data is self-contained and does not depend on a factory:

```python
def _login_input_data() -> dict[str, Any]:
    return {"email": "alice@example.com", "password": "ValidPass1!"}
```

Use a **fixture** (from `conftest.py`) when the input data must be derived from a model object created by a factory — e.g., `user_input_data(user)`. Check `conftest.py` first; if a `{model}_input_data` fixture for the model you need already exists, inject and use it directly.

**Canonical example:** `tests/users/test_users_api.py` — read this file before writing a new API test. `tests/merchants/test_merchants_api.py` and `tests/auth/test_auth_api.py` follow the exact same structure.

### API Test Checklist

- [ ] `client` fixture yields, calls `app.dependency_overrides.clear()` after yield
- [ ] Authenticated endpoints override `get_current_admin_user`
- [ ] One parametrized test covers status code + code for all exceptions
- [ ] Non-admin (403) scenario uses a `non_admin_client` fixture with a descriptive test name (`test_*_returns_403_on_non_admin`); do **not** add a separate unauthenticated (401) test per endpoint
- [ ] No test verifies that query/path params are forwarded to the service (covered implicitly by success tests)
- [ ] One **separate** test per domain exception verifying full error detail shape
- [ ] Status codes always use `fastapi.status` constants, never raw integers
- [ ] Response assertions extracted into `_assert_*_response` helpers
- [ ] `_assert_error_payload` reused for generic error code checks
- [ ] Endpoints with constrained params (`ge`/`le`) have two parametrized boundary tests: one for invalid values (→ 422) and one for valid boundary values (→ 200); values come from `settings.*`, each entry is commented

---

## 7. Testing Policies and Pure Functions

**References:** `tests/users/test_users_policies.py`, `tests/merchants/test_merchants_policies.py`

Policies are pure functions; no mocking is needed. Use `@pytest.mark.parametrize` to cover the full input space concisely.

### Pattern

```python
# tests/merchants/test_merchants_policies.py
import pytest

from app.core.config import settings
from app.merchants.exceptions import CashbackPercentageNotValidException
from app.merchants.policies import enforce_cashback_percentage_validity


@pytest.mark.parametrize(
    "percentage",
    [
        0.0,                                   # lower boundary
        settings.max_cashback_percentage / 2,  # midpoint
        settings.max_cashback_percentage,      # upper boundary
    ],
)
def test_enforce_cashback_percentage_validity_accepts_valid(
    percentage: float,
) -> None:
    # Should not raise
    enforce_cashback_percentage_validity(percentage)


@pytest.mark.parametrize(
    "percentage,expected_message",
    [
        (-0.1,                                   "between 0 and"),
        (-10.0,                                  "between 0 and"),
        (settings.max_cashback_percentage + 0.1, "between 0 and"),
        (150.0,                                  "between 0 and"),
    ],
)
def test_enforce_cashback_percentage_validity_rejects_invalid(
    percentage: float, expected_message: str
) -> None:
    # Act & Assert
    with pytest.raises(CashbackPercentageNotValidException) as exc:
        enforce_cashback_percentage_validity(percentage)
    assert expected_message in str(exc.value)
```

### Policy Test Checklist

- [ ] Use named boundary constants or `settings.*` — no bare magic numbers
- [ ] One parametrized test for valid inputs (verify no exception)
- [ ] One parametrized test for invalid inputs (verify exception type and message)
- [ ] Comment each parametrize entry to document its role: `# lower boundary`, `# midpoint`, etc.

---

## 8. Testing Utilities and Builders

**Reference:** `tests/core/errors/test_builders.py`

Utility functions are pure; test each public function with:

1. Representative valid inputs → assert return type and field values
2. Edge cases or optional arguments → assert default behaviour
3. Invalid inputs → assert exceptions where applicable

### Utility Test Pattern

```python
# tests/core/errors/test_builders.py
from fastapi import HTTPException, status

from app.core.errors.builders import internal_server_error, validation_error
from app.core.errors.codes import ErrorCode


def test_validation_error() -> None:
    # Arrange
    error_code = "VALIDATION_FAILED"
    message = "Invalid input"
    details = [{"field": "email", "error": "required"}]

    # Act
    exc = validation_error(error_code, message, details)

    # Assert
    assert exc.status_code == status.HTTP_400_BAD_REQUEST
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == error_code        # type: ignore[index]
    assert detail["error"]["message"] == message        # type: ignore[index]
    assert detail["error"]["details"]["violations"] == details  # type: ignore[index]


def test_internal_server_error_default_details() -> None:
    # Arrange (nothing)

    # Act
    exc = internal_server_error()

    # Assert
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = exc.detail  # type: ignore[attr-defined]
    assert detail["error"]["code"] == ErrorCode.INTERNAL_SERVER_ERROR  # type: ignore[index]
    assert "request_id" in detail["error"]["details"]  # type: ignore[index]
    assert "timestamp" in detail["error"]["details"]   # type: ignore[index]
```

---

## 9. Testing Concrete Providers (Light Integration)

**Reference:** `tests/auth/test_token_providers.py`

Some infrastructure classes (e.g., `JwtOAuth2TokenProvider`) are tested directly without mocking — they exercise real encoding/decoding logic. These are still fast unit tests; they just use real objects instead of mocks.

Key patterns:

- Fixtures instantiate the real class directly (no `create_autospec`).
- A data fixture (e.g. `token_payload`) holds the input; the test just calls create then verify.
- Expired / invalid token scenarios manipulate the provider's state or pass a bad string in Arrange.

**Canonical example:** `tests/auth/test_token_providers.py`

---

## 10. Testing Functions with Multiple Dependencies (Non-Service)

**Reference:** `tests/core/test_current_user.py`

Some core logic (e.g., `get_current_user`) is a standalone function rather than a class method. Test it exactly like a service: mock each dependency, call the function directly.

**Key difference from service tests:** when input construction needs to vary across tests (e.g. different roles), use a plain module-level `build_*` function — no `@pytest.fixture`, no `_` prefix — called directly in Arrange rather than injected by pytest.

**Canonical example:** `tests/core/test_current_user.py`

---

## 11. Test Helper Functions (DSL Pattern)

These are module-level functions that reduce repetition. They are **not fixtures**.

### Three Categories

#### 1. Input Data Builders

Build the `dict` that gets passed to a service or API call.

```python
# module-level function — only used in this file
def _merchant_input_data(merchant: Merchant) -> dict[str, Any]:
    return {
        "name": merchant.name,
        "default_cashback_percentage": merchant.default_cashback_percentage,
        "active": merchant.active,
    }
```

If the same builder is needed in **more than one test module**, promote it to a fixture in `conftest.py`:

```python
# tests/conftest.py
@pytest.fixture
def merchant_input_data() -> Callable[[Merchant], dict[str, Any]]:
    def _build(merchant: Merchant) -> dict[str, Any]:
        return {
            "name": merchant.name,
            "default_cashback_percentage": merchant.default_cashback_percentage,
            "active": merchant.active,
        }
    return _build
```

**Before writing any input data builder, check `conftest.py` first.**

#### 2. Assertion Helpers

Extract any assertion block that spans more than one field, or accesses nested structure:

```python
def _assert_merchant_out_response(data: dict[str, Any], merchant: Merchant) -> None:
    assert data["id"] == str(merchant.id)
    assert data["name"] == merchant.name
    assert data["default_cashback_percentage"] == merchant.default_cashback_percentage
    assert data["active"] == merchant.active


def _assert_error_payload(data: dict[str, Any], expected_code: str) -> None:
    assert "error" in data
    assert data["error"]["code"] == expected_code


def _assert_cashback_percentage_error_response(
    data: dict[str, Any], exc: CashbackPercentageNotValidException
) -> None:
    assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
    assert data["error"]["details"]["field"] == "default_cashback_percentage"
    assert data["error"]["details"]["reason"] == str(exc)
```

**Trigger rule:** if the Assert block needs an intermediate variable (e.g. `error = response.json()["error"]`) or has more than two `assert` statements, extract it.

#### 3. Arrangement Helpers

```python
def _mock_authenticated_user(service_mock: Mock, user: User) -> None:
    service_mock.get_current_user.return_value = user
```

### Placement and Naming

| Rule | Detail |
| --- | --- |
| Location | After fixtures, before first test |
| Prefix | `_` for internal helpers; no prefix for `build_*` argument-varying helpers |
| Names | `_assert_{subject}_{shape}`, `_mock_{subject}_{state}`, `_{model}_input_data` |
| Annotations | Full type hints required; return type makes call-site annotation unnecessary |

---

## 12. Section Separators

Use `# ──────────────────────────────────────────────────────────────────────────────` (80 characters wide: a hash, a space, then 78 `─` em-dashes) to visually separate major sections within a test file.

### When to add separators

| Situation | Add separator |
| --- | --- |
| File has both fixtures and tests | Before the first test function |
| File tests multiple methods / endpoints | Before each new group of tests |
| Policy file with valid vs invalid parametrized blocks | Between the two blocks |

**Files with no fixtures and a single test group** (e.g., `test_builders.py`) do not need separators.

### What to put between the two separator lines

Use a short, descriptive label:

- API groups: `# POST /api/v1/users` or `# GET /merchants – listing tests`
- Service groups: `# MerchantService.create_merchant` or `# MerchantService.list_merchants`
- Core function groups: `# get_current_user` or `# get_current_admin_user`
- Policy groups: `# valid inputs` / `# invalid inputs`

### Usage example

```python
# ──────────────────────────────────────────────────────────────────────────────
# POST /api/v1/users
# ──────────────────────────────────────────────────────────────────────────────


def test_create_user_success(...) -> None:
    ...
```

When switching to a new test group within the same file:

```python
    ...  # last test of previous group


# ──────────────────────────────────────────────────────────────────────────────
# GET /merchants – listing tests
# ──────────────────────────────────────────────────────────────────────────────


def test_list_merchants_success(...) -> None:
    ...
```

---

## 13. Type Hints Reference

Every function in a test file requires complete type annotations.

```python
# ✅ Mock fixture — return type MUST be Mock, not the ABC
@pytest.fixture
def user_repository() -> Mock:
    return create_autospec(UserRepositoryABC)

# ✅ Callable mock fixture — use the actual callable signature
@pytest.fixture
def enforce_password_complexity() -> Callable[[str], None]:
    return Mock()

# ✅ Service fixture — return the service type
@pytest.fixture
def user_service(
    enforce_password_complexity: Callable[[str], None],
    user_repository: Mock,
) -> UserService:
    return UserService(...)

# ✅ Factory fixture (from conftest)
@pytest.fixture
def user_factory() -> Callable[..., User]:
    ...

# ✅ Test function — always returns None
def test_something(
    user_service: UserService,
    user_repository: Mock,
    user_factory: Callable[..., User],
) -> None:
    db = Mock(spec=Session)             # inferred — no annotation needed
    data = user_input_data(new_user)    # inferred from helper — no annotation needed
    data: dict[str, Any] = {"key": x}  # dict literal — annotate explicitly
```

### Why `Mock` instead of the ABC type

```python
# ❌ Wrong — type checker won't find .return_value
@pytest.fixture
def user_repository() -> UserRepositoryABC:
    return create_autospec(UserRepositoryABC)

# ✅ Correct
@pytest.fixture
def user_repository() -> Mock:
    return create_autospec(UserRepositoryABC)
```

---

## 14. Integration Tests (Not Yet Implemented)

When implemented, integration tests will use `testcontainers` with a real PostgreSQL container and `sqlalchemy` sessions that roll back after each test.

**Planned structure:**

- Module-scoped container spinup
- Session-scoped engine
- Function-scoped database session with rollback on teardown
- No mocking of the repository layer; real SQL queries run against the container

---

## 15. End-to-End Tests (Not Yet Implemented)

When implemented, E2E tests will spin up the full stack via Docker Compose and issue real HTTP requests.

**Planned structure:**

- Docker Compose environment started once per test session
- Standard HTTP client (e.g. `httpx`) against `http://localhost:{port}`
- Unique test data generated with `uuid4()` to avoid collisions
- Cleanup via API calls or database truncation

---

## 16. Common Issues and Fixes

### `AttributeError: return_value` not found on fixture

**Cause:** Fixture return type is declared as the ABC, not `Mock`.
**Fix:** Change `-> MyABC:` to `-> Mock:` on the fixture.

### Mock method not behaving as expected

**Cause:** `return_value` or `side_effect` was not set before the call.
**Fix:** Always configure mocks in the **Arrange** block of the test, not in the fixture itself.

### Fixture not injected / `fixture 'x' not found`

**Cause:** Fixture defined in the wrong file.
**Fix:** If used by more than one test module, move it to `tests/conftest.py`. Pytest auto-discovers `conftest.py` fixtures in all parent directories.

### `app.dependency_overrides` leaks between tests

**Cause:** The `client` fixture did not call `app.dependency_overrides.clear()`.
**Fix:** Always use a `yield`-based fixture and call `.clear()` after yield:

```python
@pytest.fixture
def client(...) -> Generator[TestClient, None, None]:
    app.dependency_overrides[...] = ...
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Mocking authenticated endpoints

**Cause:** `get_current_admin_user` dependency was not overridden.
**Fix:** Add to the `client` fixture before creating the `TestClient`:

```python
app.dependency_overrides[get_current_admin_user] = lambda: Mock()
```

---

## 17. Quick Reference Checklist

Use this before submitting any new test file.

### All test files

- [ ] Imports follow stdlib → third-party → local order
- [ ] All fixtures and test functions have full type hints and `-> None` return
- [ ] `# Arrange / # Act / # Assert` (or `# Act & Assert`) comments present in every test
- [ ] No magic literals — use named variables or `settings.*`
- [ ] Section separators present: one before the first test (when fixtures exist), one before each additional test group
- [ ] Each separator pair carries a short descriptive label line between the two rule lines

### Service test files

- [ ] One `create_autospec` fixture per ABC dependency
- [ ] One `Mock()` fixture per callable dependency
- [ ] One service assembly fixture
- [ ] `db = Mock(spec=Session)` created locally in each test
- [ ] All branches (happy path, each exception) covered

### API test files

- [ ] `client` fixture is a generator, clears overrides after yield
- [ ] Authenticated endpoints: `get_current_admin_user` overridden
- [ ] Parametrized test covering status code + error code for all exceptions
- [ ] Separate detail test for each domain exception with rich error shape
- [ ] Input data function is a plain function (not fixture) when self-contained
- [ ] All assertions for multi-field responses extracted into `_assert_*` helpers

### Policy test files

- [ ] `@pytest.mark.parametrize` used for valid and invalid inputs
- [ ] Boundary values commented (lower boundary, upper boundary, midpoint)
- [ ] Valid inputs: verify no exception raised
- [ ] Invalid inputs: verify exception type and message substring
