---
# examples.md for build-feature skill
# Real examples from ClickNBack codebase
---

# Example 1: Purchase Service (Complex with Multiple Layers)

See `app/purchases/services.py` for a real service with:
- Multiple dependencies (repositories, clients, policies)
- Write operations using UnitOfWorkABC pattern
- Event publishing for audit logging
- Cross-module client usage (merchants, users, wallets, offers)

## Key Patterns

1. **Dependency Injection**: All dependencies injected via `__init__`
2. **UoW Pattern**: Write methods accept `uow: UnitOfWorkABC` and call `await uow.commit()` once
3. **Event Publishing**: `await broker.publish(PurchaseConfirmed(...))` after state changes
4. **Policy Delegation**: `self.enforce_purchase_ownership(user_id, purchase_user_id)` raises on validation failure
5. **Exception Handling**: Raises domain exceptions, never HTTPException

# Example 2: Merchant Service (Simple CRUD)

See `app/merchants/services.py` for:
- Simple CRUD operations
- Repository pattern with ABC + concrete implementation
- Policy enforcement (`enforce_cashback_percentage_validity`)
- Read vs. write method signatures

## Key Patterns

1. **Simple Repository**: Abstract interface + concrete implementation
2. **Write Service**: `create_merchant(data, uow)` → `await uow.commit()`
3. **Read Service**: `list_merchants(page, page_size, active, db)` → no transaction needed
4. **Error Mapping**: Catch domain exceptions in API layer, translate to HTTP

# Example 3: Purchase API (Split Into Admin/Public)

See `app/purchases/api/` for endpoint patterns:
- Admin endpoints in `admin.py`: review purchases, reverse purchases
- Public endpoints in `public.py`: user views own purchases
- Response mapping: `PurchaseOut.model_validate(orm_object)`
- Error handling: Catch exceptions, map to HTTP status + error code

## Key Patterns

1. **Role-Based Routing**: Admin and public endpoints separated
2. **Response Mapping**: Always convert ORM models to schemas
3. **Exception Mapping**: `except SomeException as e: raise status_error(...)`
4. **Query Params**: Use `Query(default, ge=1, le=100)` for validation

# Example 4: Wallet Service (Financial Correctness)

See `app/wallets/services.py` for:
- Decimal arithmetic (never float)
- SELECT FOR UPDATE for concurrent withdrawals
- Atomic wallet transitions
- Idempotency by external_id

## Key Patterns

1. **Decimal Amounts**: `amount: Decimal` not `float`
2. **Row-Level Locking**: `select(...).with_for_update()` for withdrawals
3. **Atomic Updates**: Single transaction guards all balance changes
4. **Idempotency**: External operations validated for duplicate submission

# Example 5: Feature Flag Client (Cross-Module Access)

See `app/purchases/clients/feature_flags.py` for:
- DTO pattern: `@dataclass` with cross-module data contract
- Client ABC: Abstract interface
- Client implementation: Queries shared DB, returns DTOs
- Fail-open pattern: Missing flags default to enabled

## Key Patterns

1. **DTOs Not ORM Models**: Client returns `@dataclass`, not `FeatureFlag` model
2. **ABC Pattern**: Abstract interface for testability
3. **Fail-Open**: Missing keys don't block requests
4. **No Foreign Model Imports**: Services never import `FeatureFlag` ORM directly

---
