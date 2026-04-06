---
name: write-unit-tests
type: skill
description: Write unit tests for a feature after implementation
---

# Skill: Write Unit Tests

Write unit tests for a fully implemented feature. Don't write tests speculatively — the implementation must be stable first.

## Before Starting

1. **Read the functional spec** — BDD scenarios are your coverage checklist
2. **Read the implemented files** — `models.py`, `schemas.py`, `policies.py`, `services.py`, `api.py`
3. **Read `tests/unit/conftest.py`** — Reuse existing factories; don't create duplicates

## Testing Philosophy

- **Test pyramid**: Many unit tests (all deps mocked), some integration tests (real DB), few E2E tests
- **What to test**: Service logic, API response/error mapping, policies, validators, utilities, collaborator integration
- **What NOT to test**: Thin repositories, framework internals (FastAPI routing, SQLAlchemy engine)
- **Coverage gate**: 85% minimum (aspirational: 80%); applies to unit tests only

## Workflow

### Step 1: Map BDD Scenarios to Tests

For each BDD scenario in the functional spec:
- Identify which layer it exercises (service, API, policy)
- Name the test: `test_{sut}_{result}_on_{condition}`
- Note required inputs and expected outputs

Example mapping:
```
BDD: "User submits valid purchase → HTTP 201"
  → Test: test_create_purchase_returns_201_on_valid_input
  → Layer: API

BDD: "Duplicate external_id → HTTP 409"
  → Test: test_create_purchase_raises_on_duplicate_external_id
  → Layer: Service
```

### Step 2: Test Policies (Simple)

Create `tests/unit/<module>/test_<module>_policies.py`:

```python
def test_enforce_cashback_percentage_raises_on_invalid():
    with pytest.raises(ValueError):
        enforce_cashback_percentage_validity(Decimal("150"))
    # Valid values don't raise
    enforce_cashback_percentage_validity(Decimal("50"))
```

### Step 3: Test Services

Create `tests/unit/<module>/test_<module>_services.py`:

- **Read-only tests**: Create `db = AsyncMock()` locally; no UoW needed
- **Write tests**: Create `uow = _make_uow()` locally; service calls `await uow.commit()`
- **Mock ABCs with `create_autospec(TheABC)`**; mock callables with `Mock()`
- **Verify collaborators**: Assert dependencies called with correct arguments

> ⚠️ **Service contract check:** Before writing tests for a write service method, verify
> that its parameter is `uow: UnitOfWorkABC`, not `db: AsyncSession`. A write method that
> accepts a raw session is a bug — `flush()` runs but `commit()` never does, and an
> `AsyncMock()` session will not expose the missing commit. Fix the service signature first,
> then write tests that assert `uow.commit.assert_called_once()` on success.

```python
async def test_create_merchant_returns_created_merchant_on_success():
    # Arrange
    repository = create_autospec(MerchantRepositoryABC)
    service = MerchantService(repository)
    uow = _make_uow()
    
    merchant_data = {"name": "Acme", "default_cashback_percentage": 10, "active": True}
    
    # Act
    result = await service.create_merchant(merchant_data, uow)
    
    # Assert
    uow.commit.assert_called_once()
    repository.add_merchant.assert_called_once()
    assert result.name == "Acme"
```

### Step 4: Test API Endpoints

Create `tests/unit/<module>/test_<module>_api.py`:

- Assert every response field individually (not just status code)
- One parametrized test enumerates every domain exception the endpoint can raise
- Verify HTTP status codes match intent (201 Created, 404 Not Found, etc.)

```python
async def test_create_merchant_returns_201_on_success():
    # Arrange
    merchant_out = MerchantOut(id="uuid", name="Acme", ...)
    service = create_autospec(MerchantService)
    service.create_merchant.return_value = merchant_out
    
    client = TestClient(app)
    client.depends(get_merchant_service, return_value=service)
    
    # Act
    response = client.post("/merchants", json={"name": "Acme", ...})
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Acme"
    assert response.json()["id"] == "uuid"
```

## Test Structure (AAA Pattern)

Every test uses Arrange-Act-Assert with explicit comments:

```python
async def test_update_merchant_status_raises_on_merchant_not_found():
    # Arrange
    repository = create_autospec(MerchantRepositoryABC)
    repository.get_merchant_by_id.return_value = None
    service = MerchantService(repository)
    uow = _make_uow()
    
    # Act & Assert
    with pytest.raises(MerchantNotFoundException):
        await service.set_merchant_status("unknown_id", active=True, uow=uow)
    
    uow.commit.assert_not_called()
```

## Quality Criteria

- [ ] Every BDD scenario maps to exactly one test
- [ ] No skipped tests (`@pytest.mark.skip`)
- [ ] No xfail without documented reason
- [ ] Service write tests assert `uow.commit.assert_called_once()` on success
- [ ] Service write tests assert `uow.commit.assert_not_called()` on failure
- [ ] API tests assert every response field
- [ ] Run `make test` after adding/changing/removing unit tests (never `pytest` directly)
- [ ] Run `make all-qa-gates` as the final check after completing a task

---
