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

- Always test service business logic.
- Always test API response/error mapping.
- Always test policies and validators.
- Always test utilities and builders.
- Always verify **collaborator integration** — that services correctly delegate to their dependencies (clients, repositories) with the right arguments and return values transformed correctly. See [ADR 022](../design/adr/022-collaborator-integration-verification-in-unit-tests.md) for the rationale behind this approach.
- Never test thin repository implementations.
- Never test framework internals (FastAPI routing, SQLAlchemy engine).

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
        audit/
            test_audit_enums.py         # mirrors app/core/audit/enums.py
            test_audit_services.py      # mirrors app/core/audit/services.py + composition.py
        test_current_user.py
        errors/
            test_builders.py
    merchants/
        test_merchants_api.py
        test_merchants_policies.py
        test_merchants_services.py
    offers/
        test_offers_admin_api.py        # mirrors app/offers/api/admin.py
        test_offers_public_api.py       # mirrors app/offers/api/public.py
        test_offers_policies.py
        test_offers_services.py
    purchases/
        test_purchases_api.py
        test_purchases_policies.py
        test_purchases_schemas.py
        test_purchases_services.py
    users/
        test_users_api.py
        test_users_policies.py
        test_users_services.py
```

**Rule:** `tests/{module}/test_{module_name}_{layer}.py`
Maps exactly to the source file it exercises: `app/{module}/{layer}.py` → `test_{module}_{layer}.py`. When `{layer}` is itself a package (e.g., `api/admin.py`), the test file name encodes the sub-module: `test_{module}_{sub_module}_{layer}.py` — e.g., `test_offers_admin_api.py` mirrors `app/offers/api/admin.py`.

See `docs/guidelines/code-organization.md` §6 for the full naming table.

---

## 3. Import Order

Always follow this order with blank lines between groups:

```python
# 1. stdlib
from typing import Any, AsyncGenerator, Callable, Generator
from unittest.mock import AsyncMock, Mock, create_autospec

# 2. third-party
import pytest
from fastapi import status
from fastapi.testclient import TestClient

# 3. local — core / infrastructure first, then the module under test
from app.core.current_user import get_current_admin_user
from app.core.database import get_async_db
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
| `db: AsyncSession` inside a read-only test | `AsyncMock()` — local variable, not a fixture |
| `uow: UnitOfWorkABC` inside a write test | use `_make_uow()` helper — see pattern below |

> **Return type of mock fixtures must be `Mock`, not the ABC.**
> `-> Mock` lets the type checker resolve `.return_value` and `.side_effect`.

#### `_make_uow()` helper

Service methods that commit use `UnitOfWorkABC` instead of a raw `AsyncSession`. Create a module-level `_make_uow()` helper (not a fixture — it must be called fresh inside each test) that returns a plain `Mock` with async attributes:

```python
from unittest.mock import AsyncMock, Mock
from app.core.unit_of_work import UnitOfWorkABC

def _make_uow() -> Mock:
    uow = Mock()           # plain Mock, not create_autospec — session is a property
    uow.session = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow
```

Usage inside a test:

```python
async def test_create_entity_commits_uow_on_success(service, repository, ...) -> None:
    # Arrange
    uow = _make_uow()
    repository.add.return_value = entity_factory()

    # Act
    await service.create_entity(data, uow)

    # Assert
    uow.commit.assert_called_once()
```

> **Why `Mock()` rather than `create_autospec(UnitOfWorkABC)`?**
> `session` is an abstract property; `create_autospec` makes it a descriptor that cannot be freely assigned. A plain `Mock()` avoids this while still being spec-ed by the type hints in the service.

**Canonical example:** `tests/users/test_users_services.py` — read this file before writing a new service test. `tests/merchants/test_merchants_services.py` and `tests/auth/test_auth_services.py` follow the exact same structure.

### Service Test Checklist

- [ ] One mock fixture per dependency
- [ ] Service fixture assembles the class, injecting all mocks
- [ ] `db = AsyncMock()` created locally inside each read-only test (not shared)
- [ ] `uow = _make_uow()` created locally inside each write test that commits
- [ ] Each mock is configured in **Arrange**, not in the fixture
- [ ] Happy path, every `raise`, every `side_effect` branch covered
- [ ] Write operations: assert `uow.commit.assert_called_once()` on success, and `uow.commit.assert_not_called()` when an exception prevents reaching the commit
- [ ] `pytest.raises` used with `# Act & Assert` comment
- [ ] **Collaborator verification** (where applicable) — assert that dependencies are called with correct arguments and their return values are transformed/mapped correctly (e.g., `dependency.method.assert_called_once_with(expected_args)`, then verify the returned data is correctly transformed)

---

## 6. Unit Testing API Endpoints

**References:** `tests/users/test_users_api.py`, `tests/auth/test_auth_api.py`, `tests/merchants/test_merchants_api.py`

### Testing Scope

- Always test: status codes matching `fastapi.status` constants.
- Always assert every field in the response body individually — the success test must not check only the status code.
- Always cover every domain exception the endpoint can raise with a single parametrized test; never omit an exception.
- Always test that unhandled exceptions produce a 500 response.
- Always test the non-admin (403) case — verifies the endpoint calls the correct admin-guarded dependency.
- Always test query/path parameter constraint validation for endpoints with `ge`/`le` constraints, covering both valid and invalid boundary values.
- Never test unauthenticated (401) per endpoint — the 401 is raised inside the auth helper (`get_current_user`), which is already tested in `tests/core/test_current_user.py`; repeating it on every endpoint is redundant.
- Never test business logic in API tests (belongs in service tests).
- Never re-verify service argument forwarding at the API level — parameter-to-service delegation is verified in service-layer collaborator tests and tested implicitly through the API success test.

### API Test Structure

1. `{service}_mock` fixture — `create_autospec(TheService)`, return type `Mock`
2. `client` fixture — overrides all FastAPI dependencies, yields `TestClient`, clears overrides
3. Module-level `_input_data()` function — returns a plain `dict` (not a fixture, no `@pytest.fixture`)
4. Module-level assertion helpers — `_assert_*_response`, `_assert_error_payload`
5. Success test — asserts **every** field in the response schema through a `_assert_*_response` helper; stub the service to return a factory-built model instance and verify the full field mapping (id, all value fields, all derived/computed fields such as `status`)
6. Parametrized exceptions test — one entry per exception the endpoint can raise, including the generic unhandled `Exception` → 500 case; **every** exception listed in the api module must appear; checks status code + error code only
7. Individual detail tests for each domain exception (full error body)
8. Boundary value tests for any endpoint with constrained query/path params (two parametrized tests — valid and invalid)

### `client` Fixture Pattern

```python
@pytest.fixture
def client(service_mock: Mock) -> Generator[TestClient, None, None]:
    async def mock_get_async_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_async_db] = mock_get_async_db
    app.dependency_overrides[get_the_service] = lambda: service_mock

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()   # always clean up
```

**For endpoints that use `get_unit_of_work`** (write endpoints), override it with a plain `Mock()` that has async attributes — the service is already mocked so the UoW is never actually called, but FastAPI still needs to resolve the dependency:

```python
from unittest.mock import AsyncMock, Mock
from app.purchases.composition import get_unit_of_work

@pytest.fixture
def client(service_mock: Mock) -> Generator[TestClient, None, None]:
    uow_mock = Mock()
    uow_mock.session = AsyncMock()
    uow_mock.commit = AsyncMock()
    uow_mock.rollback = AsyncMock()

    app.dependency_overrides[get_unit_of_work] = lambda: uow_mock
    app.dependency_overrides[get_the_service] = lambda: service_mock

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
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


def test_endpoint_enforces_admin_user(
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

**Canonical example:** `tests/users/test_users_api.py` — read this file before writing a new API test. `tests/merchants/test_merchants_api.py` and `tests/auth/test_auth_api.py` follow the exact same structure. When the module uses a split `api/` package (e.g., `offers`), the canonical examples are `tests/offers/test_offers_admin_api.py` and `tests/offers/test_offers_public_api.py`.

### API Test Checklist

- [ ] `client` fixture yields, calls `app.dependency_overrides.clear()` after yield
- [ ] Authenticated endpoints override `get_current_admin_user`
- [ ] Success test asserts **every** field in the response schema through a `_assert_*_response` helper — field mapping must be complete, not just the status code
- [ ] One parametrized test covers status code + error code for **every** exception the endpoint can raise (inspect the api module file to enumerate them all); no exception may be omitted
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

**Pattern:**

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

## 8a. Testing Schema Validators

**Reference:** `tests/purchases/test_purchases_schemas.py`

Pydantic `@field_validator` methods are pure functions. Test them by constructing the schema class directly — no mocking required. Treat them exactly like policy functions.

### Key differences from policy tests

| Aspect | Policy tests | Schema validator tests |
| --- | --- | --- |
| SUT invocation | Call the function directly | Construct the schema class: `Schema(**payload)` |
| Valid-input assertion | No exception raised | No exception raised + assert field value |
| Invalid-input assertion | `pytest.raises(DomainException)` | `pytest.raises(ValidationError)` |
| Message check | `str(exc.value)` or attribute | `str(exc_info.value)` contains substring |

**Pattern:**

```python
# tests/purchases/test_purchases_schemas.py
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from app.purchases.schemas import PurchaseCreate


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    """Returns a complete, valid input dict. Override only the field under test."""
    base: dict[str, Any] = {
        "external_id": "txn-001",
        "user_id": "b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d",
        "merchant_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "amount": "100.00",
        "currency": "EUR",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "amount",
    [
        "1",              # integer — 0 decimal places
        "10.5",           # 1 decimal place
        "100.00",         # 2 decimal places — upper scale boundary
        "0.01",           # minimum positive with 2 decimal places
        "9999999999.99",  # maximum representable value at precision=12, scale=2
    ],
)
def test_purchase_create_accepts_valid_amount_scale(amount: str) -> None:
    # Act — should not raise
    schema = PurchaseCreate(**_valid_payload(amount=amount))

    # Assert
    assert schema.amount == Decimal(amount)


@pytest.mark.parametrize(
    "amount,expected_message",
    [
        ("100.001", "at most 2 decimal places"),  # 3 decimal places
        ("0.001",   "at most 2 decimal places"),  # 3 decimal places — near zero
        ("1.1234",  "at most 2 decimal places"),  # 4 decimal places
    ],
)
def test_purchase_create_rejects_amount_with_excess_scale(
    amount: str, expected_message: str
) -> None:
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        PurchaseCreate(**_valid_payload(amount=amount))
    assert expected_message in str(exc_info.value)
```

### When to add schema validators

Add a `@field_validator` (and its tests) whenever the ORM column carries a constraint that cannot be expressed by Pydantic's built-in field arguments alone:

| ORM constraint | Schema validator to add |
| --- | --- |
| `Numeric(scale=N)` | Reject values with more than N decimal places |
| `String` with allowed values | Reject strings outside the allowed set (or use `Literal` / `Enum`) |
| Custom cross-field invariant | `@model_validator(mode="after")` + test with both valid and invalid combinations |

Built-in Pydantic guards (`gt`, `ge`, `lt`, `le`, `min_length`, `max_length`, `pattern`) do not require a separate validator — test them via the API boundary-value tests (§6).

### Schema Validator Test Checklist

- [ ] Module-level `_valid_payload(**overrides)` helper — returns a complete, valid dict; override only the field under test
- [ ] One parametrized test for valid inputs — verify no exception and assert the parsed field value
- [ ] One parametrized test for invalid inputs — verify `ValidationError` is raised and message substring matches
- [ ] Each parametrize entry is commented (role: lower boundary, upper boundary, midpoint, etc.)
- [ ] No magic values — use named boundary constants where applicable

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

## 14. Testing Async Modules (purchases, wallets, payouts, …)

All new modules use the async database stack (see ADR 010). Tests for these modules follow the same structure as sync modules with the following differences.

### pytest-asyncio configuration

The project runs `pytest-asyncio` in **strict mode** (configured in `pyproject.toml`):

```toml
[tool.pytest.ini_options]
asyncio_mode = "strict"
```

Mark every async test function and every async fixture with `@pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_ingest_purchase_returns_purchase_on_success(...) -> None:
    ...
```

### Mocking async repositories

Use `create_autospec` on the ABC as usual. For `async def` methods, `create_autospec` automatically returns `AsyncMock` for those methods — no extra configuration is needed:

```python
from unittest.mock import AsyncMock, Mock, create_autospec

from app.purchases.repositories import PurchaseRepositoryABC


@pytest.fixture
def purchase_repository() -> Mock:
    return create_autospec(PurchaseRepositoryABC)


@pytest.mark.asyncio
async def test_ingest_purchase_raises_on_duplicate_external_id(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    # Arrange
    duplicate_id = "ext-123"
    purchase_repository.get_by_external_id.return_value = Purchase(...)

    # Act & Assert
    with pytest.raises(PurchaseDuplicateException):
        await purchase_service.ingest_purchase({"external_id": duplicate_id}, db=AsyncMock())
```

### Mocking `AsyncSession` in tests

Create a local `AsyncMock(spec=AsyncSession)` inside each test (not a shared fixture):

```python
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

async def test_example(purchase_service: PurchaseService, ...) -> None:
    # Arrange
    db = AsyncMock(spec=AsyncSession)
    ...
    # Act
    result = await purchase_service.some_method(data, db)
```

### HTTP API tests for async handlers

`TestClient` from FastAPI/Starlette wraps `anyio` to run async route handlers synchronously during tests — no test changes are needed for the API layer. Override `get_async_db` (not `get_db`) in the `client` fixture:

```python
from app.core.database import get_async_db

@pytest.fixture
def client(service_mock: Mock) -> Generator[TestClient, None, None]:
    async def mock_get_async_db():
        yield AsyncMock(spec=AsyncSession)

    app.dependency_overrides[get_async_db] = mock_get_async_db
    app.dependency_overrides[get_purchase_service] = lambda: service_mock

    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
```

### Type hints for async tests

```python
# ✅ Async test function — returns None
@pytest.mark.asyncio
async def test_ingest_purchase_success(
    purchase_service: PurchaseService,
    purchase_repository: Mock,
) -> None:
    db = AsyncMock(spec=AsyncSession)
    ...
```

### Quick reference — additions to checklist for async modules

Service tests:

- [ ] `db = AsyncMock(spec=AsyncSession)` created locally in each test (replaces `Mock(spec=Session)`)
- [ ] All service test functions marked `@pytest.mark.asyncio` and declared `async def`
- [ ] `await` used when calling service methods

API tests:

- [ ] `client` fixture overrides `get_async_db` (not `get_db`)
- [ ] The `async_db` generator mock uses `async def` and `yield`

---

## 15. Integration Tests (Not Yet Implemented)

When implemented, integration tests will use `testcontainers` with a real PostgreSQL container and `sqlalchemy` sessions that roll back after each test.

**Planned structure:**

- Module-scoped container spinup
- Session-scoped engine
- Function-scoped database session with rollback on teardown
- No mocking of the repository layer; real SQL queries run against the container

---

## 16. End-to-End Tests (Not Yet Implemented)

When implemented, E2E tests will spin up the full stack via Docker Compose and issue real HTTP requests.

**Planned structure:**

- Docker Compose environment started once per test session
- Standard HTTP client (e.g. `httpx`) against `http://localhost:{port}`
- Unique test data generated with `uuid4()` to avoid collisions
- Cleanup via API calls or database truncation

---

## 17. Common Issues and Fixes

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

## 18. Quick Reference Checklist

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

### Schema validator test files

- [ ] Module-level `_valid_payload(**overrides)` helper present
- [ ] One parametrized test for valid inputs — asserts parsed field value
- [ ] One parametrized test for invalid inputs — asserts `ValidationError` and message substring
- [ ] Each parametrize entry is commented with its role
