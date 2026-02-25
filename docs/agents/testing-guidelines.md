# Testing Guidelines for AI Agents

Concise guidelines for writing tests in ClickNBack. Follow existing test patterns in the codebase.

## 1. Testing Philosophy

### Test Pyramid

- **Unit Tests (Many):** Fast, isolated, mocked dependencies
- **Integration Tests (Some):** Real database interactions
- **E2E Tests (Few):** Complete user workflows

### What to Test

✅ Service business logic, API responses/errors, policies, utilities
❌ Thin repositories, framework behavior

### Quality Standards

- AAA pattern with explicit comments (Arrange/Act/Assert or Arrange/Act & Assert for exceptions)
- Independent tests, no shared state
- Fast (< 100ms for unit tests)
- Descriptive names: `test_{function}_{scenario}_{outcome}`
- **No magic values:** extract literals into named variables that explain their role (e.g. `out_of_range_cashback_percentage = 150.0` instead of a bare `150.0`)
- **Don't over-specify test data:** when a dependency is mocked, the input values passed through it are irrelevant — use default factory values instead of constructing semantically meaningful (e.g. invalid) data. Only set specific values when the value itself is what's under test.

## 2. File Structure

**Pattern:** `tests/{module}/test_{module_name}.py`

Example: `tests/users/test_users_services.py` for `app/users/services.py`

**Shared fixtures:** `tests/conftest.py` (e.g., `user_factory`)
**Module fixtures:** In test file after imports

## 3. Unit Testing Services

**Reference:** See `tests/users/test_users_services.py` and `tests/auth/test_auth_services.py`

### Key Rules

1. **Mock all dependencies**
   - Use `create_autospec(InterfaceABC)` for interfaces/ABCs
   - Use `Mock()` for callables (lambdas/functions)

2. **Fixtures**
   - Create fixture for each dependency mock
   - Create fixture for service that injects all mocks
   - Place fixtures after imports, before tests

3. **Configure mocks in Arrange**
   - `mock.return_value = result` for return values
   - `mock.side_effect = Exception()` for exceptions

4. **Test all scenarios:** happy paths, exceptions, edge cases

## 4. Unit Testing API Endpoints

**Reference:** See `tests/users/test_users_api.py`

### Testing Scope

✅ Success scenarios (status codes + response mapping)
✅ Error scenarios (status codes + error structure)
✅ Exception mapping to HTTP responses
❌ Business logic (in service tests)

### Key Patterns

1. **Override FastAPI dependencies** with `app.dependency_overrides`, clear after test
2. **Use TestClient** from fastapi.testclient
3. **Assert status codes** using `fastapi.status` constants
4. **Use helper functions** for complex assertions and repeated arrangement (`_assert_user_out_response`, `_assert_error_payload`, `_user_input_data`)
5. **Use @pytest.mark.parametrize** for multiple error scenarios

## 5. Policies and Validators

**Reference:** See `tests/users/test_users_policies.py`

**Key:** Test pure functions with valid and invalid inputs using `@pytest.mark.parametrize`

## 6. Utilities and Builders

**Reference:** See `tests/core/errors/test_builders.py`

**Key:** Test inputs, outputs, return types, and exception scenarios

## 7. Fixtures and Factories

### Shared Fixtures

Place in `tests/conftest.py` for reuse across modules

### Factory Pattern

Return callables that create objects with overridable defaults:

```python
@pytest.fixture
def user_factory() -> Callable[..., User]:
    def _make_user(**kwargs: Any) -> User:
        defaults = {"email": "test@example.com", ...}
        defaults.update(kwargs)
        return User(**defaults)
    return _make_user
```

### Test Helper Functions (DSL Pattern)

Extract any logic that repeats across tests into module-level helper functions (prefixed with `_`). This avoids duplication and makes each test read as a concise, high-level description of intent.

Helpers fall into three categories:

#### 1. Input data builders — construct service/API input dicts from model objects

```python
def _merchant_input_data(merchant: Merchant) -> dict[str, Any]:
    return {
        "name": merchant.name,
        "default_cashback_percentage": merchant.default_cashback_percentage,
        "active": merchant.active,
    }

# Usage
data = _merchant_input_data(new_merchant)
```

#### 2. Assertion helpers — encapsulate multi-field or structural assertions

```python
def _assert_user_out_response(body: dict[str, Any], user: User) -> None:
    assert body["id"] == user.id
    assert body["email"] == user.email

def _assert_error_payload(body: dict[str, Any], expected_code: str) -> None:
    assert body["error"]["code"] == expected_code

# Usage
_assert_user_out_response(response.json(), user)
_assert_error_payload(response.json(), "EMAIL_ALREADY_REGISTERED")
```

#### 3. Arrangement helpers — set up recurring mock states

```python
def _mock_authenticated_user(service_mock: Mock, user: User) -> None:
    service_mock.get_current_user.return_value = user

# Usage
_mock_authenticated_user(service_mock, user)
```

#### Placement and naming

- Place helpers after fixtures and before the first test.
- Use `_` prefix to signal they are internal to the test module.
- Name them `_{subject}_{role}`: `_merchant_input_data`, `_assert_user_out_response`, `_mock_authenticated_user`.
- Helpers must have full type annotations; their return types eliminate the need to annotate call-site variables.

## 8. Type Hints (CRITICAL)

**All fixtures and tests must have complete type hints:**

```python
@pytest.fixture
def user_repository() -> Mock:  # ✅ Return Mock, not UserRepositoryABC
    return create_autospec(UserRepositoryABC)

def test_something(
    user_service: UserService,  # ✅ Service type
    db: Mock,                    # ✅ Mock type
    user_factory: Callable[..., User],  # ✅ Factory type
) -> None:  # ✅ Tests return None
    # Arrange
    db = Mock(spec=Session)              # ✅ inferred, no annotation needed
    data: dict[str, Any] = {"key": ...} # ✅ annotate dict literals explicitly
    data = _model_input_data(obj)        # ✅ type inferred from helper, no annotation needed
    # Test implementation
```

**Why Mock types:** Type checkers recognize `.return_value` on Mock, not on ABCs.

**Local variable annotation rules:**

- Annotate `dict` literals used as service input inline: `data: dict[str, Any] = {...}`
- Prefer extracting a DSL helper (see section 7) when the same logic repeats — the helper's return type makes inline annotation unnecessary.
- `Mock()` assignments are inferred correctly and do not require annotation

## 9. Integration Tests (Not Yet Implemented)

Use testcontainers with PostgreSQL, real database sessions with rollback after each test.

**Structure:** Module-scoped container, session-scoped engine, function-scoped session with rollback.

## 10. End-to-End Tests (Not Yet Implemented)

Use Docker Compose, real HTTP requests, test complete user workflows. Use unique test data (uuid).

## 11. Common Issues

### return_value Attribute Not Found

**Fix:** Fixture return type must be `Mock`, not the interface it mocks

### Mock Not Configured

**Fix:** Set `return_value` in Arrange section before calling method

### Fixture Not Found

**Fix:** Move shared fixtures to `conftest.py`
