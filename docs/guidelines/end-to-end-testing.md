# End-to-End Testing Guidelines for AI Agents

Full-stack testing layer — spin up the complete application via Docker Compose and test critical user-facing flows that span multiple domain modules. Use this guide for testing multi-step scenarios that would be impractical to unit-test or integration-test in isolation.

All E2E tests share the same quality standards as unit tests (AAA structure, naming conventions, type hints). See [Unit Testing Guidelines](./unit-testing.md) § 1-4 for shared standards and § 18 for a universal checklist.

---

## 1. When to Write E2E Tests

E2E tests are expensive and slow — reserve them for critical user-facing flows that cross-cut multiple domain modules. Write an E2E test when a feature involves a multi-step flow that would be impractical to wire together in an integration test.

**Example scenario:** A full cashback lifecycle:

1. User registers
2. User makes a purchase at a merchant
3. Cashback is confirmed asynchronously
4. Wallet is credited
5. User withdraws cashback

E2E tests cover these end-to-end scenarios; unit and integration tests cover the individual operations.

---

## 2. Running E2E Tests

E2E tests spin up the full stack via Docker Compose and issue real HTTP requests against the running service.

```bash
make test-e2e
```

---

## 3. Test Structure

- **Docker Compose environment** started once per test session (session-scoped fixture)
- **`httpx.AsyncClient`** targeting `http://localhost:{port}`; the port is read from env / settings
- **Unique test data** generated with `uuid4()` so parallel runs do not collide
- **No pre-seeded DB state** — each test creates its own data through the API
- **Cleanup:** Each test creates its own data; the suite truncates or re-applies seeds after the session

---

## 4. Quality Standards

E2E tests follow the **same** AAA structure, naming convention, and type-hint rules as unit and integration tests. There are no exceptions.

Example:

```python
@pytest.mark.asyncio
async def test_user_earns_cashback_on_purchase_flow(
http_client: AsyncClient,
) -> None:
    # Arrange
user_data = {"email": f"test-{uuid.uuid4()}@example.com", "password": "ValidPass123!"}
login_response = await http_client.post("/api/v1/auth/register", json=user_data)
assert login_response.status_code == status.HTTP_201_CREATED
user_token = login_response.json()["token"]

    # Act
authenticated_client = AsyncClient(
app,
base_url="http://localhost:8001",
headers={"Authorization": f"Bearer {user_token}"},
)
purchase_response = await authenticated_client.post(
"/api/v1/purchases/",
json={
"merchant_id": "...",
"amount": "100.00",
"currency": "EUR",
},
)

    # Assert
assert purchase_response.status_code == status.HTTP_201_CREATED
wallet_response = await authenticated_client.get("/api/v1/users/me/wallet")
assert wallet_response.status_code == status.HTTP_200_OK
wallet_data = wallet_response.json()
assert wallet_data["pending"] >= 0
```

---

## 5. File Layout

```text
tests/e2e/
    conftest.py          # Docker Compose lifecycle, base_url, session client
    test_{flow}.py       # one file per user-facing flow
```

**Naming convention:** `test_{flow_name}.py` — e.g., `test_user_registration_and_login.py`, `test_cashback_earn_and_withdraw.py`.

---

## 6. pytest-asyncio Configuration

Every E2E test file must declare:

```python
import pytest

pytestmark = pytest.mark.asyncio
```

This marks all test functions in the file as async without requiring `@pytest.mark.asyncio` on each function individually.

---

## 7. AAA Structure

E2E tests **must** follow AAA structure. Every test function must contains `# Arrange`, `# Act`, and `# Assert` comments (or `# Act & Assert` for error cases). This rule applies regardless of how simple the test is — even a two-line test still needs the comments.

```python
# ✅ Correct
@pytest.mark.asyncio
async def test_example_flow() -> None:
    # Arrange
    setup_data = ...

    # Act
    result = await http_client.post(...)

    # Assert
    assert result.status_code == status.HTTP_200_OK
```

---

## 8. Test Data Creation

- **All test data created through the public API** (no direct DB inserts)
- **Use `uuid4()` for uniqueness** — e.g., `f"user-{uuid.uuid4()}"` for email addresses
- **No reliance on pre-existing database state** — each test is independent
- **No fixture-based seeding** — all data flows through HTTP calls

```python
@pytest.mark.asyncio
async def test_multiple_users_can_earn_cashback(http_client: AsyncClient) -> None:
    # Arrange
user1_data = {"email": f"user1-{uuid.uuid4()}@example.com", "password": "Pass1!"}
user2_data = {"email": f"user2-{uuid.uuid4()}@example.com", "password": "Pass2!"}

    # Act
user1_register = await http_client.post("/api/v1/auth/register", json=user1_data)
user2_register = await http_client.post("/api/v1/auth/register", json=user2_data)

    # Assert
assert user1_register.status_code == status.HTTP_201_CREATED
assert user2_register.status_code == status.HTTP_201_CREATED
```

---

## 9. Status Codes

Always use `fastapi.status` constants, never raw integers:

```python
# ✅ Correct
assert response.status_code == status.HTTP_201_CREATED

# ❌ Wrong
assert response.status_code == 201
```

---

## 10. Coverage Strategy

E2E tests cover **critical happy-path flows only**. Do not attempt to cover all error modes — those are already covered by unit and integration tests. Examples of critical flows:

- User registration → login → profile update
- Browse offers → make purchase → wallet credited → withdraw
- Admin setup → merchant creation → offer configuration

Leave edge cases and validation errors to unit/integration tests.

---

## 11. Common Issues and Fixes

### Docker Compose not available

**Cause:** Docker or Docker Compose not installed or not running.
**Fix:** Install Docker and Docker Compose; ensure the daemon is running before executing `make test-e2e`.

### Port already in use

**Cause:** Previous Docker Compose session did not clean up.
**Fix:** Run `make test-e2e-down` to stop containers, then retry.

### Tests timeout waiting for service

**Cause:** Application startup is slow or service is not responding.
**Fix:** Check Docker logs `docker compose -f docker-compose.e2e.yml logs app`;  increase timeout threshold if necessary.

### Test data conflicts (UUID collision)

**Cause:** `uuid4()` not used or used trivially (e.g., always the same value).
**Fix:** Always generate unique identifiers: `f"user-{uuid.uuid4()}"`.

---

## 12. E2E Test Checklist

- [ ] File placed under `tests/e2e/`; named `test_{flow_name}.py`
- [ ] `pytestmark = pytest.mark.asyncio` declared at module level
- [ ] `# Arrange`, `# Act`, `# Assert` in every test function
- [ ] All test data created through the HTTP API (no direct DB inserts)
- [ ] Test data uses `uuid4()` to ensure uniqueness
- [ ] No dependency on pre-existing database state
- [ ] Status codes use `fastapi.status` constants
- [ ] Tests cover **happy path only** — error modes are in unit/integration tests
- [ ] All fixtures and test functions have full type hints and `-> None` return
- [ ] Imports follow stdlib → third-party → local order
- [ ] Multi-step flows are outlined in comments

---

## 13. When to Add E2E Tests

Write E2E tests **after** the feature is fully implemented, all unit tests and integration tests pass, and manual E2E smoke tests are successful. E2E tests are not written speculatively.

- [ ] Feature is complete and stable
- [ ] Unit tests ✅ pass
- [ ] Integration tests ✅ pass
- [ ] Manual E2E smoke tests ✅ successful
- [ ] Flow spans multiple domain modules (not a single endpoint)
- [ ] Flow is customer-facing (not internal/admin-only)

---

## 14. Quick Reference

See [Unit Testing Guidelines](./unit-testing.md) § 1, 3, 13 for shared standards:

- AAA structure and naming conventions
- Import order
- Type hints

See E2E test checklist (§ 12 above) before submitting.

See [Integration Testing Guidelines](./integration-testing.md) for similar patterns applied to single-endpoint testing.
