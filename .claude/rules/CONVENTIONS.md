---
name: conventions
type: rule
description: Code naming, error handling, async patterns, and ORM conventions
---

# CONVENTIONS

## Naming Conventions

### Schemas

- **Input schemas**: `<Entity>Create`, `<Entity>Update` (all fields optional for updates).
- **Output schemas**: `<Entity>Out` with `model_config = {"from_attributes": True}`.
- **Paginated responses**: `Paginated<Entity>Out` with `items`, `total`, `page`, `page_size`.

### Services & Repositories

- **Service class**: `<Entity>Service` (e.g., `PurchaseService`, `MerchantService`).
- **Repository interface**: `<Entity>RepositoryABC` (e.g., `PurchaseRepositoryABC`).
- **Repository implementation**: `<Entity>Repository` (e.g., `PurchaseRepository`).
- **Repository methods**: Verb-noun pairs: `add_*`, `get_*_by_*`, `list_*`, `update_*`, `delete_*`.

### Policies & Helpers

- **Policy functions**: Named with rule intent: `enforce_*`, `validate_*`, `check_*`.
  - **Critical rule**: Policies are the **only place** where domain exceptions are raised.
  - Encapsulate all business rule validation and enforcement in policies, not in services.
  - Example: `enforce_user_active(user, user_id)` → raises domain exception if user is not active.
  - Example: `enforce_password_valid(password_correct)` → raises domain exception if password does not match.
  - Services call policies and let exceptions propagate; they do not raise exceptions directly.
- **Helper functions**: Named with action: `apply_*`, `calculate_*`, `build_*`, `format_*`.
  - Example: `apply_purchase_confirmation(purchase, confirmed_at)` → returns updated purchase state.
  - Helpers return modified state or computed values; they never raise exceptions.

### Exceptions

- **Exception class**: `<Situation>Exception` (e.g., `UserNotActiveException`, `MerchantNotFoundException`).
- **Error code**: `<DOMAIN>_<SITUATION>` (e.g., `USER_NOT_ACTIVE`, `MERCHANT_NOT_FOUND`).

## Error Handling

### Domain Exceptions (Raised in Policies)

Domain exceptions carry context attributes and are schema-agnostic. **All exception raising must happen in policy functions**, never directly in services. This ensures all business rule enforcement is centralized, testable, and maintainable:

```python
# app/users/policies.py
def enforce_user_active(user: UserDTO | None, user_id: str) -> None:
    """Raise if the user does not exist or is not active."""
    if user is None:
        raise UserNotFoundException(user_id)
    if not user.active:
        raise UserNotActiveException(user_id)

# app/users/services.py
class UserService:
    async def get_active_user(self, db: AsyncSession, user_id: str) -> UserDTO:
        user = await self.repository.get(db, user_id)
        # Call policy; let exceptions propagate
        policies.enforce_user_active(user, user_id)
        return user
```

**Why policies?**
- Policies isolate business rules into pure, testable functions.
- Services focus on orchestration; policies focus on validation.
- All exception-raising logic is in one place (policies), reducing bugs and improving maintainability.
- Easy to unit test: test policies independently, then test that services call them correctly.

### ErrorCode Enum (Per Module)

Each module defines its own `ErrorCode` enum:

```python
# app/users/errors.py
class ErrorCode(str, Enum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_NOT_ACTIVE = "USER_NOT_ACTIVE"
    EMAIL_ALREADY_REGISTERED = "EMAIL_ALREADY_REGISTERED"
```

### HTTP Error Mapping (In API Layer)

The API layer translates domain exceptions to HTTP responses:

```python
@router.post("/users")
async def create_user(...):
    try:
        return await service.create_user(...)
    except DuplicateEmailException as e:
        raise validation_error(ErrorCode.EMAIL_ALREADY_REGISTERED, str(e))
    except Exception as e:
        logging.error("Unexpected error", extra={"error": str(e)})
        raise internal_server_error()
```

### Standard Error Response Shape

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User abc123 not found",
    "details": { "user_id": "abc123" }
  }
}
```

## Async & Database Patterns

### Session Usage

- **Read-only services**: Accept `db: AsyncSession` directly.
- **Write services**: Accept `uow: UnitOfWorkABC`, access session via `uow.session`.
- **Repository methods**: Accept `db: AsyncSession` and use it; flush but never commit.

### Query Style

All new modules use **SQLAlchemy 2.0 `select()` style**:

```python
# ✅ Correct (SQLAlchemy 2.0 style)
from sqlalchemy import select

result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()

# ❌ Wrong (legacy query style)
user = db.query(User).filter(User.id == user_id).first()
```

### Async Operations

- ✅ Always: `await db.execute(...)`, `await db.flush()`, `await uow.commit()`.
- ❌ Never: Blocking I/O (requests, file I/O) in request handlers; always delegate to async libraries or background jobs.

## Monetary Values

- ✅ Always: Use `Decimal` for amounts, prices, balances.
- ❌ Never: Use `float` for money.

Example:

```python
# ✅ Correct
amount: Decimal = Decimal("19.99")

# ❌ Wrong
amount: float = 19.99  # Precision loss!
```

## Idempotency

- Purchases are idempotent by `external_id` (unique DB constraint).
- Re-submission with the same `external_id` yields a conflict (caught in service, mapped to HTTP 409).
- See [ADR-002](../../docs/design/adr/002-not-to-use-dedicated-dtos.md) and [ADR-003](../../docs/design/adr/003-api-module-as-composition-root.md).

## Logging

- Use `app.core.logging.logger` for all logs.
- Log **outcomes**, not inputs (never log passwords, tokens, secrets).
- Include structured context: `logger.info("msg", extra={"key": value})`.

Example:

```python
logger.info(
    "Purchase confirmed",
    extra={"purchase_id": purchase.id, "amount": purchase.amount}
)
```

## DRY Principle & Refactoring Patterns

When reviewing or implementing changes, **proactively detect and extract duplicated logic** into private helper methods or shared utilities. This prevents maintenance bugs where updates to logic miss one or more locations.

### When to Extract

Extract duplicated logic into a private helper (`_helper_name`) when:

1. **Same sequence appears 2+ times** in the same class or module
2. **The containing methods are already long** (>80 lines) — extraction aids readability
3. **The logic is non-trivial** — more than 1-2 lines; trivial getters don't need extraction
4. **The shared logic is unlikely to diverge** — if variations are expected, keep separate

### Red Flags for DRY Violations

- ✅ Scan for repeated patterns within service methods (token creation, balance updates, state transitions, repository calls)
- ✅ When modifying duplicated logic, note that **future maintainers may forget to update all occurrences** → refactor immediately to prevent divergence
- ✅ Long methods (>150 lines) are especially vulnerable; breaking them into helpers improves testability and clarity

### Extraction Steps

1. **Identify the duplicated sequence** — mark start and end lines
2. **Name the helper** — use `_<action>_<object>` pattern (e.g., `_create_refresh_token_record`, `_apply_cashback_rules`)
3. **Extract with shared parameters** — pass all variable inputs; never hardcode values
4. **Return the result** — helpers return the computed value for reuse
5. **Update all call sites** — ensure consistency across all occurrences
6. **Run tests** — verify behavior unchanged (`make test && make coverage`)

### ⛔ CRITICAL: Never Extract `await uow.commit()`

**Transaction boundaries are a service-level responsibility.** `await uow.commit()` must NEVER be called within a helper method.

**Why?**
- Helpers are reusable, but commit boundaries are context-specific
- If a helper commits early and a later operation fails, the transaction is partially persisted (breaking atomicity)
- The service method determines when ALL changes are ready to be committed as one atomic unit
- Multiple helpers may be called within a single transaction; only the top-level service method should commit

**Correct Pattern:**
```python
# ✅ CORRECT: Helper flushes (stages changes); service commits (finalizes transaction)
async def _apply_discount(self, order: Order, discount: Decimal, db: AsyncSession) -> None:
    """Apply discount to order. Does NOT commit."""
    order.total -= discount
    await db.flush()  # Stage the change, don't commit

async def apply_coupon(self, order_id: str, coupon_code: str, uow: UnitOfWorkABC) -> None:
    """Service method: orchestrates multiple operations, then commits once."""
    order = await self.repository.get(uow.session, order_id)
    discount = await self.validate_coupon(coupon_code)
    await self._apply_discount(order, discount, uow.session)
    # ... other operations ...
    await uow.commit()  # ← Single commitment point
```

**Incorrect Pattern:**
```python
# ❌ WRONG: Helper commits (breaks transaction boundaries)
async def _apply_discount(self, order: Order, discount: Decimal, uow: UnitOfWorkABC) -> None:
    order.total -= discount
    await db.flush()
    await uow.commit()  # ❌ WRONG: Helper should not commit!

async def apply_coupon(self, order_id: str, coupon_code: str, uow: UnitOfWorkABC) -> None:
    order = await self.repository.get(uow.session, order_id)
    await self._apply_discount(order, discount, uow)  # Commits prematurely
    # If next operation fails, previous changes were already committed
    await some_other_operation(uow)  # Too late; can't roll back with _apply_discount changes
```

### Example: Token Creation Refactoring

**Before (duplicated in two methods):**
```python
refresh_token = self.token_provider.create_refresh_token(user_id)
token_hash = self.token_provider.hash_refresh_token(refresh_token)
expires_at = now + timedelta(minutes=self.token_provider.refresh_ttl_in_minutes)
await self.repository.create(uow.session, user_id, token_hash, issued_at=now, expires_at=expires_at)
await uow.commit()
```

**After (extracted helper — correct, with commit at service level):**
```python
async def _create_refresh_token_record(self, user_id: str, now: datetime, uow: UnitOfWorkABC) -> str:
    """Create and persist a refresh token; return token string.
    
    Does not commit; caller is responsible for committing the transaction.
    """
    refresh_token = self.token_provider.create_refresh_token(user_id)
    token_hash = self.token_provider.hash_refresh_token(refresh_token)
    expires_at = now + timedelta(minutes=self.token_provider.refresh_ttl_in_minutes)
    await self.repository.create(uow.session, user_id, token_hash, issued_at=now, expires_at=expires_at)
    # ← NO commit here; only flush
    return refresh_token

# Call site 1: login (service method owns the commit)
refresh_token = await self._create_refresh_token_record(str(user.id), now, uow)
await uow.commit()  # ← Service decides when to commit the whole transaction

# Call site 2: refresh (service method owns the commit)
new_refresh_token = await self._create_refresh_token_record(user_id, now, uow)
# ... possibly other operations ...
await uow.commit()  # ← Service decides when to commit the whole transaction
```

---
