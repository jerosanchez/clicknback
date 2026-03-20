# ADR 022: Collaborator Integration Verification in Unit Tests

**Status:** Accepted  
**Date:** 2026-03-20  
**Context:** Service-layer testing and test pyramid design  

---

## Problem

When testing a service that depends on other components (clients, repositories, or other services), we must decide at which layer to verify that the service correctly delegates to its collaborators. Two approaches exist:

1. **Unit test collaborator verification**: Include tests in the service layer that verify the service calls its dependencies with the correct arguments and that return values are correctly transformed.
2. **Integration/E2E only**: Skip collaborator verification in unit tests and rely only on integration and E2E tests to catch delegation defects.

The question is: should we verify collaborator integration as part of unit testing, or leave that entirely to higher-layer tests?

---

## Context

### Test Pyramid Constraints

A typical test pyramid allocates test effort as:

- **Many** unit tests (% of test suite) — fast, run locally, exercise business logic in isolation
- **Some** integration tests — real database, slower, but closer to production
- **Few** E2E tests — full HTTP stack, slowest, highest cost

### Real-World Risk

In modular architectures (like ClicknBack's modular monolith), services depend on clients that abstract other modules. Example:

```python
class WalletService:
    def __init__(self, cashback_client: CashbackClientABC) -> None:
        self.cashback_client = cashback_client
    
    async def list_wallet_transactions(self, user_id, limit, offset, db):
        txns, total = await self.cashback_client.list_by_user_id(db, user_id, limit, offset)
        # transform and return
```

Without unit-level verification that:

- The service calls `cashback_client.list_by_user_id(db, user_id, limit, offset)` (not `list_by_user(user_id)` or with arguments in wrong order)
- The returned data is correctly mapped to the service's output schema

...defects in this delegation can slip through to integration/E2E tests or even production, where they are expensive to debug.

### Why Not Isolate Collaborators Away Entirely?

The opposite extreme — mocking the service itself in API tests and never testing its integration with real clients — would make API tests less meaningful. API tests need to verify not just the HTTP response format, but that the service's logic is correctly wired to its dependencies, at least to some degree.

---

## Decision

**We verify collaborator integration in unit tests.**

Unit tests will include assertions that:

1. Dependencies are called with correct arguments (e.g., `mock.assert_called_once_with(expected_args)`)
2. Return values from collaborators are correctly transformed into the service's output schema
3. Edge cases (empty lists, null returns, exceptions) are handled correctly

This approach sits in the middle:

- **Not mocking away all collaborators** — API and service tests both validate delegation exists and works correctly
- **Not requiring full integration setup for basic verification** — verification happens quickly in isolated unit tests without spinning up containers or databases

### Service Test Examples

```python
@pytest.mark.asyncio
async def test_list_wallet_transactions_forwards_limit_and_offset_to_client(
    wallet_service: WalletService,
    cashback_client: Mock,
) -> None:
    # Arrange
    cashback_client.list_by_user_id = AsyncMock(return_value=([], 0))
    db = AsyncMock()

    # Act
    await wallet_service.list_wallet_transactions(_USER_ID, 25, 50, db)

    # Assert — verify delegation
    cashback_client.list_by_user_id.assert_called_once_with(db, _USER_ID, 25, 50)


@pytest.mark.parametrize("cashback_status", ["pending", "available", "reversed"])
async def test_list_wallet_transactions_type_is_always_cashback_credit(
    wallet_service: WalletService,
    cashback_client: Mock,
    cashback_status: str,
) -> None:
    # Arrange
    txn = _make_cashback_txn(status=cashback_status)
    cashback_client.list_by_user_id = AsyncMock(return_value=([txn], 1))
    db = AsyncMock()

    # Act
    result = await wallet_service.list_wallet_transactions(_USER_ID, 10, 0, db)

    # Assert — verify transformation is correct
    assert result.transactions[0].type == WalletTransactionType.CASHBACK_CREDIT
    assert result.transactions[0].status == cashback_status
```

### What to Test in Unit Tests

✅ **Do test**: Service calls collaborator with correct args; return values are transformed correctly; pagination forwarding is correct; nested object mapping is complete  
❌ **Don't test at API layer**: The same delegation (it's already tested in service tests)

---

## Alternatives Considered

### 1. Integration Tests Only

**Rationale:** Let all collaborator verification happen in integration/E2E tests; unit tests focus only on business logic.

**Advantages:**

- Simpler unit tests (fewer assertions)
- Forces thinking about the full system early

**Disadvantages:**

- Defects in delegation surface late and expensive (integration test failures, or worse, production)
- Slower feedback loop for developers
- Harder to debug (full stack involved)

***Rejected because*** the cost of late defect discovery outweighs the simplicity gain.

### 2. Mock All Collaborators in API Tests

**Rationale:** Skip service tests for delegation; verify only in API tests with mocked services.

**Advantages:**

- Lighter API test setup

**Disadvantages:**

- API tests become less valuable (testing a mock service instead of real service logic)
- Service layer lacks test coverage
- Defects in service transformation logic slip through

***Rejected because*** the loss of service-layer visibility is too high.

### 3. Collaborator Mocks + Full Integration Tests

**Rationale:** Keep unit tests as decision; add separate integration test suite that exercises the real client→repository chain.

**Advantages:**

- Combines fast unit feedback with comprehensive integration coverage

**Disadvantages:**

- Higher overall test count and maintenance load
- Risk of duplicate test logic between layers

***Viable but deferred*** — current approach is sufficient for MVP.

---

## Implications

### Test Structure

- **Service tests** will include parametrized tests that verify each collaborator is called correctly and return values are transformed.
- **API tests** will focus on HTTP response format and status codes; they won't re-verify that services call collaborators (that's already covered in service tests).
- **Integration tests** (future) will exercise the full stack (service → client → repository → real database) to ensure the mocks' assumptions are correct.

### Test Pyramid Scaling

This approach slightly shifts the test pyramid:

- Unit tests are slightly heavier (more assertions per test)
- But overall test execution remains fast (< 100 ms per test)
- Integration tests can focus on cross-module flows and edge cases not easily captured in isolation

### Maintenance

Tests become more brittle if collaborator contracts change. **Mitigation:** Use `create_autospec` to ensure mocks track the actual interface.

---

## Trade-Off: White-Box Testing (Implementation Details)

**Known limitation:** This approach tests implementation details — we must know *how* the service is implemented (that it calls `cashback_client.list_by_user_id` with specific arguments) to write the tests. This is a form of white-box testing, not pure black-box behavior verification.

**Why we accept this trade-off:**

1. **MVP stage**: At the MVP phase, writing full integration/E2E tests for every collaborator interaction is resource-intensive. Unit-level verification of wiring provides confidence that the system is correctly assembled without that overhead.
2. **Practical necessity**: Defects in delegation (wrong argument order, missing pagination forwarding, incorrect data transformation) are common and expensive to debug if discovered in integration tests or production. Catching them in fast unit tests keeps feedback cycles short.
3. **Community standard**: This approach is accepted and widely practised in the Python and FastAPI communities. By following it, we enable faster onboarding for new team members who already understand the pattern.
4. **Evolution path**: As the project grows and integration/E2E test coverage expands, unit tests can evolve or be pruned; for now, they fill a critical gap.

**When this trade-off becomes untenable:**

- If collaborator contracts change frequently, tests become brittle and require constant updates.
- If business logic becomes more complex and implementation changes are frequent, maintenance burden rises.

**Mitigation:**

- Use `create_autospec(TheABC)` to ensure mocks stay in sync with the actual interface.
- Periodically review and refactor tests when contracts stabilize.
- Introduce integration tests as resource/time permits to verify the mocks' assumptions against reality.

---

## Rationale

1. **Early feedback**: Delegation defects are caught in fast, local unit tests, not in slow integration tests.
2. **Complete unit coverage**: Service layer tests are self-contained and validate the full "happy path" logic including collaborator integration.
3. **Practical compromise**: More thorough than "integration tests only," lighter-weight than full integration stack for basic verification.
4. **Real-world necessity**: In a modular monolith, cross-module contracts are critical; unit-level verification ensures they are honored.
5. **Community alignment**: Following accepted testing patterns in the FastAPI/Python ecosystem reduces cognitive load for new joiners and aligns with industry practice.

---

## References

- [ADR 007: Layered Testing Strategy](007-layered-testing-strategy.md)
- [ADR 001: Adopt Modular Monolith Approach](001-adopt-modular-monolith-approach.md)
- [Unit Testing Guidelines](../../guidelines/unit-testing.md) § 5 (Service Testing)
