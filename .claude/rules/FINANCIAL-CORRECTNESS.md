---
name: financial-correctness
type: rule
description: Decimal arithmetic, idempotency, concurrency safety, and EUR-only policy
---

# FINANCIAL-CORRECTNESS

Financial transactions demand precision and safety. This rule enforces strict constraints on arithmetic, idempotency, and concurrency.

## Decimal-Only Arithmetic

### ❌ Never Use Float for Money

```python
# ❌ WRONG — Precision loss
amount: float = 19.99  # May become 19.989999999999998
balance = 100.0 + amount  # 119.989999999999998 (WRONG!)

# ✅ CORRECT
from decimal import Decimal
amount: Decimal = Decimal("19.99")
balance = Decimal("100.0") + amount  # 119.99
```

### Why Decimal?

- Floats use binary representation; decimal values (like 0.1 or 19.99) cannot be represented exactly.
- Over thousands of transactions, rounding errors accumulate.
- `Decimal` uses base-10 arithmetic with arbitrary precision.

### All Monetary Fields Use Decimal

- **Models**: All `amount`, `balance`, `price`, `percentage` fields are `Decimal` type.
- **Schemas**: Input/output schemas validate with `Decimal`.
- **Database**: PostgreSQL `NUMERIC(10, 2)` or similar (exact, not approximate).

See [ADR-003](../../docs/design/adr/003-api-module-as-composition-root.md) and [ADR-005](../../docs/design/adr/005-use-containerized-postgresql.md).

## Idempotency

### External IDs Are Unique

Every external transaction (purchase, payout request) has a unique `external_id` assigned by the client. This ID is a **unique database constraint** — replaying the same request with the same `external_id` is safe.

### Handling Duplicate Submission

If a purchase with the same `external_id` is submitted twice:

1. **First request**: Creates purchase, confirms state, updates wallet.
2. **Second request**: DB constraint violation (duplicate `external_id`) is caught in the service.
3. **Response**: HTTP 409 Conflict (not 201 Created, not 500 Internal Server Error).

This ensures that network retries, client timeouts, and accidental double-clicks are handled safely.

### Implementation

```python
# Service layer
class PurchaseService:
    async def ingest_purchase(self, purchase_input: PurchaseIngest, uow: UnitOfWorkABC):
        # Check: external_id already exists?
        existing = await self.repository.get_by_external_id(uow.session, purchase_input.external_id)
        if existing:
            raise DuplicatePurchaseException(purchase_input.external_id)
        
        # Continue with normal flow...
        new_purchase = Purchase(...)
        ...
```

See [ADR-002](../../docs/design/adr/002-not-to-use-dedicated-dtos.md).

## Concurrency Safety

### Row-Level Locking for Wallet Withdrawals

When a user requests a payout, the wallet balance is decremented. To prevent two withdrawal requests from double-spending:

```python
# Use SELECT FOR UPDATE to lock the row
query = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
wallet = (await db.execute(query)).scalar_one()

# Check balance after locking
if wallet.available < payout_amount:
    raise InsufficientFundsException()

# Decrement balance
wallet.available -= payout_amount
await db.flush()
```

### Why SELECT FOR UPDATE?

- Without row-level locking, two concurrent requests can both read the same balance and both approve payouts that exceed the available funds.
- `SELECT FOR UPDATE` locks the row until the transaction commits, preventing this race condition.

### State Machines Enforce Transitions

Purchases and cashback transactions follow defined state machines:

```
Purchase: pending → confirmed | reversed (not pending → reversed directly)
CashbackTransaction: pending → confirmed | reversed (mirrors purchase)
```

Every state transition is validated by a policy; invalid transitions raise a domain exception.

## EUR-Only Currency Policy

- ✅ All monetary values are in EUR.
- ✅ All purchases must declare currency = "EUR".
- ❌ No multi-currency conversions.
- ❌ No currency fields on wallet or balance tables.

See [ADR-011](../../docs/design/adr/011-eur-only-currency-policy.md).

## Validation Checklist

Before submitting code with financial logic:

- [ ] All monetary values are `Decimal` type (not `float`)
- [ ] Wallet updates use atomic transactions (UoW pattern)
- [ ] Withdrawals use `SELECT FOR UPDATE` row-level locking
- [ ] External transactions have unique `external_id` constraint
- [ ] Duplicate submissions return 409 Conflict (not 500 or 201)
- [ ] State transitions are validated before persistence
- [ ] All amounts are EUR (no currency conversions)
- [ ] Tests verify concurrency safety (two concurrent withdrawals blocked correctly)

---
