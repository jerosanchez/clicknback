# Prompt: Write E2E Tests for a Feature

Use this prompt for critical multi-step user flows that span multiple endpoints, roles, or time-dependent events. Do not write E2E tests for every feature — reserve them for scenarios that validate critical business logic.

## Context

- Read `AGENTS.md` for project context, testing conventions, and quality gates.
- Read [End-to-End Testing Guidelines](../../docs/guidelines/end-to-end-testing.md) — all conventions, patterns, and practices for E2E testing.
  - § 1-3: When to write, running tests, test structure
  - § 4-7: Quality standards, file layout, pytest-asyncio, AAA structure
  - § 8-11: Test data creation, status codes, coverage strategy
  - § 12-14: E2E checklist, common issues, when to add E2E tests
- Read `tests/e2e/conftest.py` to understand available fixtures (`http_client`, `user_http_client`, `admin_http_client`)
- Read the functional spec and any ADRs for this feature — E2E tests validate the full user journey.

## Constraints

- E2E tests exercise the **complete stack**: Docker Compose environment, full HTTP API, database, all background jobs.
- No mocked services or endpoints.
- Tests are slow (~5–30 seconds each) — write few and only for critical paths.
- Focus on: role-based workflows, time-dependent state machines, multi-step transactions.
- Assertion count should be **low** — spot-check key state transitions, not every field.

---

## Steps

### Step 1 — Identify critical user flows

- List the scenario: e.g., "User earns cashback on purchase → cashback confirmed → runs withdrawal job → payout status updates."
- Ask: Would a unit or integration test find the bug, or only a full-stack flow?
  - If testable with integration tests → don't write E2E test.
  - If requires background jobs, multiple roles, or time progression → write E2E test.

### Step 2 — Create E2E test file

- Create `tests/e2e/<module>_<feature>_e2e.py` (e.g., `tests/e2e/purchases_cashback_confirmation_e2e.py`).
- Import: `pytest`, `status`, `asyncio`, test fixtures, model factories.
- Declare `pytestmark = pytest.mark.asyncio` at module level.

### Step 3 — Write the happy path E2E test

- **Arrange**: Create test users, merchants, offers; seed DB with realistic state.
- **Act**: Execute the multi-step workflow via HTTP (multiple API calls, possibly with delays).
- **Assert**: Spot-check key state transitions; touch only critical fields.

Example flow: User earns cashback → purchase confirmation → withdrawal initiated.

```python
@pytest.mark.asyncio
async def test_complete_cashback_flow_earns_pending_balance_then_becomes_available(
    user_http_client: AsyncClient,
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange: Seed merchant, offer, create user wallet
    merchant = await _seed_merchant_with_active_offer(db)
    user_id = uuid.uuid4()

    # Act 1: Create purchase via API
    purchase_payload = {
        "merchant_id": str(merchant.id),
        "amount": "150.00",
        "external_id": f"purchase-{uuid.uuid4()}",
        "purchase_date": date.today().isoformat(),
    }
    response = await user_http_client.post("/api/v1/purchases", json=purchase_payload)
    assert response.status_code == status.HTTP_201_CREATED
    purchase_id = response.json()["id"]

    # Act 2: Confirm purchase (admin action)
    response = await admin_http_client.post(f"/api/v1/purchases/{purchase_id}/confirm")
    assert response.status_code == status.HTTP_200_OK

    # Act 3: Wait for background job to process cashback
    await asyncio.sleep(2)

    # Assert: Verify wallet state
    response = await user_http_client.get("/api/v1/wallet")
    wallet = response.json()
    assert Decimal(wallet["available"]) > 0  # cashback now available
```

### Step 4 — Add fixtures for data seeding

- Create async seed helpers like `_seed_merchant_with_active_offer(db)`.
- Call `await db.flush()` to persist; do **not** call `await db.commit()`.
- Return the primary entity for use in the test.

Example:

```python
async def _seed_merchant_with_active_offer(db: AsyncSession) -> Merchant:
    merchant = Merchant(
        name=f"E2E Test Merchant {uuid.uuid4().hex[:6]}",
        default_cashback_percentage=10.0,
        active=True,
    )
    db.add(merchant)
    await db.flush()

    offer = Offer(
        merchant_id=merchant.id,
        percentage=10.0,
        fixed_amount=None,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        monthly_cap_per_user=500.0,
        active=True,
    )
    db.add(offer)
    await db.flush()
    return merchant
```

### Step 5 — Handle time-dependent events (if needed)

- Use the `datetime_provider` injected by background jobs to control time progression.
- Or use `asyncio.sleep(seconds)` to wait for background jobs to process.
- Assert state changes occur as expected after time advances.

### Step 6 — Cover one alternative failure scenario

- Write one test that covers a critical failure: e.g., "User cannot withdraw while balance is pending" or "Conflict on duplicate external_id."
- Do not exhaustively test validation — integration tests cover that.

---

## AAA Structure Example

```python
@pytest.mark.asyncio
async def test_purchase_confirmed_flow_increases_wallet_pending_balance(
    user_http_client: AsyncClient,
    admin_http_client: AsyncClient,
    db: AsyncSession,
) -> None:
    # Arrange
    merchant = await _seed_merchant_with_active_offer(db)
    user_id = uuid.uuid4()
    payload = {
        "merchant_id": str(merchant.id),
        "amount": "100.00",
        "external_date": date.today().isoformat(),
        "external_id": f"ext-{uuid.uuid4()}",
    }

    # Act
    response = await user_http_client.post("/api/v1/purchases", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    # Wait for confirmation job (if async)
    await asyncio.sleep(1)

    # Assert
    wallet_response = await user_http_client.get("/api/v1/wallet")
    wallet = wallet_response.json()
    assert Decimal(wallet["pending"]) > 0
```

---

## Running E2E Tests Locally

```bash
# Start full Docker Compose stack
docker-compose -f docker-compose.e2e.yml up -d

# Run tests
make test-e2e

# Cleanup
docker-compose -f docker-compose.e2e.yml down
```

---

## After Writing E2E Tests

Verify test independence: each test should pass when run alone or in any order. Then:

```bash
make test-e2e      # E2E tests only
make lint          # code style
```

Submit only when all E2E and integration tests pass.

---

## Reference

- [End-to-End Testing Guidelines](../../docs/guidelines/end-to-end-testing.md)
- [Unit Testing Guidelines](../../docs/guidelines/unit-testing.md) (for shared standards like AAA, naming)
- Canonical examples: `tests/e2e/`
