# Prompt: Write Integration Tests for a Feature

Use this prompt after unit tests are passing and the feature is ready for full-stack testing. Do not write integration tests speculatively — unit tests must be stable first.

## Context

- Read `AGENTS.md` for project context, testing conventions, and quality gates.
- Read [Integration Testing Guidelines](../../docs/guidelines/integration-testing.md) — all conventions, patterns, and practices for integration testing.
  - § 1-4: Setup, file layout, isolation strategy, fixtures
  - § 5-10: AAA structure, seeding helpers, test coverage expectations
  - § 12: Integration test checklist
- Read `tests/integration/conftest.py` to understand available fixtures (`http_client`, `user_http_client`, `admin_http_client`, `db`)
- Read the functional spec for this feature — one integration test per endpoint that was implemented.

## Constraints

- Integration tests exercise the **full stack**: HTTP routing, service layer, repository layer, real PostgreSQL database.
- No mocked dependencies — all collaborators are real.
- Cover happy path and key failure modes (auth, validation, conflicts); edge cases belong in unit tests.
- Do not repeat test logic from unit tests — only verify end-to-end integration works.

---

## Steps

### Step 1 — Identify endpoints to test

- Scan the API module (`api.py` or `api/` package) and list each endpoint that was implemented.
- For each endpoint, plan:
  - Happy path: verify status code and key response fields
  - Key failure modes: 401, 403, 404, 409, 422 (where applicable)

### Step 2 — Create integration test file structure

- Create `tests/integration/<module>/<endpoint>_integration.py` per endpoint.
- Declare `pytestmark = pytest.mark.asyncio` at the module level (marks all tests as async).
- Import `pytest`, `status` (from `fastapi`), and test fixtures from conftest.

### Step 3 — Write happy path tests

- Use `http_client`, `user_http_client`, or `admin_http_client` fixture depending on auth requirements.
- Make the actual HTTP call (no mocked service).
- Assert status code and all key response fields.
- Extract multi-field assertions into `_assert_*_response()` helper.

### Step 4 — Write failure mode tests

- Cover: 401 (unauthenticated), 403 (unauthorized), 404 (not found), 409 (conflict), 422 (validation).
- Use parametrized tests for multiple similar scenarios.
- Do not exhaustively test validation — that's covered by unit tests.

### Step 5 — Add seeding helpers (if needed)

- For endpoints that read from DB (GET, LIST), create `async def _seed_*(db)` helpers.
- Helpers should call `await db.flush()`, never `await db.commit()`.
- Return the primary entity needed by the test.

Example:

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

### Step 6 — Verify isolation and cleanup

- Each test runs in a transaction that rolls back on completion — no manual cleanup needed.
- Verify `db` fixture is only injected when seeding; omit it for tests that only call endpoints.

---

## AAA Structure Example

```python
@pytest.mark.asyncio
async def test_create_merchant_returns_201_on_success(
    admin_http_client: AsyncClient,
) -> None:
    # Arrange
    payload = {
        "name": f"Test Merchant {uuid.uuid4()}",
        "default_cashback_percentage": 5.0,
        "active": True,
    }

    # Act
    response = await admin_http_client.post("/api/v1/merchants", json=payload)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["active"] is True
```

---

## After Writing Integration Tests

Unit tests + integration tests should provide comprehensive coverage. If needed, add [E2E Tests](./write-e2e-tests.prompt.md) for multi-step user flows.

Before submitting:
```bash
make test-integration    # integration tests only
make lint                # code style
```

---

## Reference

- [Integration Testing Guidelines](../../docs/guidelines/integration-testing.md)
- [Unit Testing Guidelines](../../docs/guidelines/unit-testing.md) (for shared standards like AAA, naming, imports)
- Canonical examples: `tests/integration/purchases/`, `tests/integration/merchants/`
