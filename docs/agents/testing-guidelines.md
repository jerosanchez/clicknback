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
4. **Use helper functions** for complex assertions (_assert_user_out_response, _assert_error_payload)
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
    # Test implementation
```

**Why Mock types:** Type checkers recognize `.return_value` on Mock, not on ABCs.

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
