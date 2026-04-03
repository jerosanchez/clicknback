---
name: review-code
type: skill
description: Structured code review checklist
---

# Skill: Review Code

Structured code review checklist. Use this to audit code for architecture, correctness, and quality.

## Review Checklist

### Architectural Violations

- [ ] API layer has no business logic (services/policies only)
- [ ] Services don't raise HTTPException (domain exceptions only)
- [ ] Repositories don't call `db.commit()` (flush only)
- [ ] Write services use `UnitOfWorkABC` with `await uow.commit()` once
- [ ] No direct ORM model imports between modules (use clients/DTOs)
- [ ] Layering respected: api → services → repositories → db

### Financial Correctness

- [ ] All monetary values are `Decimal` (never `float`)
- [ ] Wallet withdrawals use `SELECT FOR UPDATE` row-level locking
- [ ] External transactions have unique constraint on `external_id`
- [ ] Duplicate requests return 409 Conflict (not 500 or other)
- [ ] State machines enforced (invalid transitions blocked)

### Async & Database

- [ ] All repository methods are `async def` using `select()` style
- [ ] No blocking I/O in request handlers
- [ ] Session usage correct (read methods: `AsyncSession`, write methods: `uow.session`)
- [ ] No mixing of sync/async patterns

### Error Handling

- [ ] Domain exceptions raised in services/policies (not HTTPException)
- [ ] API layer catches domain exceptions and maps to HTTP errors
- [ ] Error codes are specific (e.g., `MERCHANT_NOT_FOUND`, not `ERROR`)
- [ ] All failure modes from spec have corresponding error codes

### Code Quality

- [ ] Type hints on all functions and methods
- [ ] Proper naming: `enforce_*`, `apply_*`, `calculate_*`
- [ ] No magic values (literals extracted to named variables)
- [ ] Logging includes structured context (`extra={"key": value}`)
- [ ] No secrets in logs (passwords, tokens, API keys)

### Testing

- [ ] Unit tests cover all BDD scenarios from spec
- [ ] No skipped tests (`@pytest.mark.skip`)
- [ ] Mocks use `create_autospec` for ABCs
- [ ] Service write tests assert `uow.commit.assert_called_once()`
- [ ] Service write tests assert `uow.commit.assert_not_called()` on failure
- [ ] API tests assert every response field (not just status)

### Dependencies

- [ ] Clients injected via `__init__` and wired in `composition.py`
- [ ] No direct imports of another module's models/repositories
- [ ] Cross-module data returned as DTOs, not ORM models

---
