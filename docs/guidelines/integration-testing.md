# Integration Testing Guidelines for AI Agents

Real-database testing layer — exercise FastAPI routing, service layer, repository layer, and PostgreSQL with **no mocked dependencies**. Use this guide after writing unit tests to add integration coverage for each endpoint.

All integration tests share the same quality standards as unit tests (AAA structure, naming conventions, type hints). See [Unit Testing Guidelines](./unit-testing.md) § 1-4 for shared standards and § 18 for a universal checklist.

---

## 1. Setup

Set `TEST_DATABASE_URL` to point to a dedicated PostgreSQL test database:

```text
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/clicknback_test
```

Run integration tests with:

```bash
make test-integration
```

---

## 2. File Layout and Naming

One file per endpoint; placed under `tests/integration/{module}/`:

```text
tests/integration/
    conftest.py          # engine, session (with rollback), http_client fixtures
    {module}/
        __init__.py
        test_{module}_{feature}_integration.py
```

**Naming convention:** `test_{module}_{verb}_{resource}_integration.py` — e.g., `test_merchants_create_integration.py`, `test_purchases_list_admin_integration.py`.

---

## 3. Isolation Strategy

Each test runs inside an outer connection-level transaction that is rolled back on teardown. `UnitOfWork.commit()` inside services creates and releases a savepoint via `join_transaction_mode="create_savepoint"` rather than committing the outer transaction, so all writes are visible within the test but nothing persists after the test ends. No manual cleanup is needed.

---

## 4. Fixtures

Available fixtures (in `tests/integration/conftest.py`):

| Fixture | Scope | Purpose |
| --- | --- | --- |
| `create_tables` | session | Creates all tables once; drops them after the session |
| `db` | function | Yields a rolled-back `AsyncSession` |
| `http_client` | function | Unauthenticated `httpx.AsyncClient` wired to the app |
| `user_http_client` | function | Authenticated client with a regular-user token |
| `admin_http_client` | function | Authenticated client with an admin token |
| `user_http_client_with_user` | function | Like `user_http_client` but yields `(client, user)` tuple — use when the request body needs the user's own ID |

Two helper functions are also exported:

| Helper | Signature | Purpose |
| --- | --- | --- |
| `create_user` | `async (db, *, role, email, password) → (User, str)` | Insert a user directly into the test session; returns `(user, plain_password)` |
| `make_token` | `(user) → str` | Generate a real JWT for a given `User` instance |

---

## 5. AAA Structure

Integration tests **must** follow the same AAA structure as unit tests. Every test function must contain `# Arrange`, `# Act`, and `# Assert` comments (or `# Act & Assert` for `pytest.raises` blocks). This rule applies regardless of how simple the test is — even a two-line test still needs the two comments.

The only exception is when there is genuinely no arrangement needed (e.g., a read endpoint with a brand-new user and no seeded data). In that case, omit `# Arrange` but always include `# Act` and `# Assert`.

```python
# ✅ Simple test — no Arrange needed, but Act + Assert are mandatory
async def test_get_wallet_returns_200_for_new_user(
user_http_client: AsyncClient,
) -> None:
    # Act
response = await user_http_client.get("/api/v1/users/me/wallet")

    # Assert
assert response.status_code == status.HTTP_200_OK


# ✅ Test with seeding — full AAA
async def test_list_purchases_returns_seeded_purchase(
user_http_client_with_user: tuple[AsyncClient, User],
db: AsyncSession,
) -> None:
    # Arrange
client, user = user_http_client_with_user
merchant = await _seed_merchant_with_offer(db)
await client.post(
"/api/v1/purchases/",
json={
"external_id": f"ext-{uuid.uuid4()}",
"user_id": str(user.id),
"merchant_id": merchant.id,
"amount": "50.00",
"currency": "EUR",
},
)

    # Act
response = await client.get("/api/v1/users/me/purchases")

    # Assert
assert response.status_code == status.HTTP_200_OK
assert response.json()["total"] >= 1
```

---

## 6. Seeding Helpers

Extract repeated DB setup into module-level `async def _seed_*(db)` helpers. They must be `async` (since they call `await db.flush()`) and should return the primary entity needed by the test.

```python
async def _seed_merchant_with_offer(db: AsyncSession) -> Merchant:
merchant = Merchant(
name=f"Test Merchant {uuid.uuid4().hex[:6]}",
default_cashback_percentage=5.0,
active=True,
)
db.add(merchant)
await db.flush()
offer = Offer(
merchant_id=merchant.id,
percentage=5.0,
fixed_amount=None,
start_date=date.today(),
end_date=date.today() + timedelta(days=30),
monthly_cap_per_user=100.0,
active=True,
)
db.add(offer)
await db.flush()
return merchant
```

---

## 7. Request Payload Helpers

Extract repeated request payloads into module-level `_payload()` functions:

```python
def _payload(user_id: str, merchant_id: str, external_id: str) -> dict[str, Any]:
return {
"external_id": external_id,
"user_id": user_id,
"merchant_id": merchant_id,
"amount": "50.00",
"currency": "EUR",
}
```

---

## 8. pytest-asyncio Configuration

Every integration test file must declare:

```python
import pytest

pytestmark = pytest.mark.asyncio
```

This marks all test functions in the file as async without requiring `@pytest.mark.asyncio` on each function individually.

---

## 9. Coverage

Integration tests run separately from unit tests and do not contribute to the `make coverage` gate. The 85% hard gate applies to unit tests only.

---

## 10. What to Cover

- **Happy path** for each endpoint: verify status code and key response fields
- **Key failure modes:** 401/403/404/409/422 responses with correct error codes
- **Do not** repeat every edge case — those belong in unit tests

---

## 11. Canonical Examples

- [`tests/integration/purchases/test_purchases_ingest_integration.py`](../../tests/integration/purchases/test_purchases_ingest_integration.py) — seeding, `_payload()` helper, duplicate-detection, auth checks
- [`tests/integration/purchases/test_purchases_get_details_integration.py`](../../tests/integration/purchases/test_purchases_get_details_integration.py) — creating a second user via `create_user()` and `make_token()` to test ownership enforcement
- [`tests/integration/merchants/test_merchants_create_integration.py`](../../tests/integration/merchants/test_merchants_create_integration.py) — admin endpoint with no seeding (simplest possible structure)

---

## 12. Integration Test Checklist

- [ ] File placed under `tests/integration/{module}/`; named `test_{module}_{endpoint}_integration.py`
- [ ] `pytestmark = pytest.mark.asyncio` declared at module level
- [ ] `# Arrange`, `# Act`, `# Assert` (or `# Act & Assert`) present in every test function; `# Arrange` may be omitted only when nothing needs seeding
- [ ] Seeding uses `async def _seed_*(db: AsyncSession)` helpers; helpers call `await db.flush()`, never `await db.commit()`
- [ ] No mocked dependencies — all collaborators are real
- [ ] Tests cover: happy path, key failure modes (auth, validation, conflict)
- [ ] Edge cases are left to unit tests
- [ ] `db` fixture injected only when the test seeds data; omit it otherwise
- [ ] Status codes use `fastapi.status` constants, never raw integers
- [ ] All fixtures and test functions have full type hints and `-> None` return
- [ ] Imports follow stdlib → third-party → local order

---

## 13. Common Issues and Fixes

### Test transaction not rolling back

**Cause:** `db.commit()` was called instead of `db.flush()`.
**Fix:** Always use `await db.flush()` in seeding helpers — commits are managed by the test harness.

### `db` fixture not provided

**Cause:** Test tries to inject `db` but does not use it.
**Fix:** Omit the `db` fixture if the test only calls HTTP endpoints; seeding helpers access the same session.

### Fixture 'http_client' not found

**Cause:** Fixture is defined in `tests/integration/conftest.py` but not imported.
**Fix:** Import directly from conftest; pytest auto-discovers conftest fixtures.

---

## 14. When to Add Integration Tests

Write integration tests when an endpoint is fully implemented and all manual smoke tests in the `.http` files are passing. Do not write integration tests speculatively — the implementation and unit tests must be stable first.

One integration test per endpoint:

- Endpoint must be routed, documented, and have passing unit tests
- Integration test exercises the full stack (HTTP → service → repository → DB)
- Test covers happy path + key failure modes; edge cases stay in unit tests

---

## 15. Quick Reference

See [Unit Testing Guidelines](./unit-testing.md) § 1, 3, 13 for shared standards:

- AAA structure and naming conventions
- Import order
- Type hints

See integration test checklist (§ 12 above) before submitting.
