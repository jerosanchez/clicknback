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
  - Example: `enforce_user_active(user, user_id)` → raises domain exception if check fails.
- **Helper functions**: Named with action: `apply_*`, `calculate_*`, `build_*`, `format_*`.
  - Example: `apply_purchase_confirmation(purchase, confirmed_at)` → returns updated purchase state.

### Exceptions

- **Exception class**: `<Situation>Exception` (e.g., `UserNotActiveException`, `MerchantNotFoundException`).
- **Error code**: `<DOMAIN>_<SITUATION>` (e.g., `USER_NOT_ACTIVE`, `MERCHANT_NOT_FOUND`).

## Error Handling

### Domain Exceptions (Raised in Services/Policies)

Domain exceptions carry context attributes and are schema-agnostic:

```python
class UserNotFoundException(DomainException):
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")
```

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

---
