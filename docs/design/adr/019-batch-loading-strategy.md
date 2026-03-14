# ADR-019: Batch Loading Strategy for Cross-Module Data Enrichment

**Date:** 2026-03-14
**Status:** Accepted

---

## Context

Listing endpoints frequently need to enrich each item with data that lives in another module. The canonical example is `GET /users/me/purchases`: the repository returns a list of `Purchase` rows, each carrying a `merchant_id`, but the response requires `merchant_name` — a field that belongs to the `merchants` module.

The naive approach is to look up each foreign entity in a loop:

```python
# ❌ N+1 — issues one SELECT per purchase
for purchase in purchases:
    merchant = await merchants_client.get_merchant_by_id(db, purchase.merchant_id)
    merchant_name = merchant.name if merchant else "Unknown"
```

For a page of 20 purchases, this is 21 queries (1 list + 20 lookups). Under any real load this degrades response time visibly and stresses the database connection pool.

---

## Decision

**Batch-load all foreign entities after the initial list query using a single `WHERE id IN (...)` lookup.**

The pattern has three steps:

1. **Fetch the list** — call the repository as normal.
2. **Collect unique foreign IDs** — extract from the result set in O(n) with a set comprehension.
3. **One batch query** — call a dedicated batch method on the foreign module's client, which issues a single `WHERE id IN (ids)` statement and returns `dict[id, DTO]`.

```python
# ✅ 2 queries total, regardless of page size
purchases, total = await self.repository.list_purchases(db, user_id=user_id, ...)

merchant_ids = list({p.merchant_id for p in purchases})
merchants_map = await self.merchants_client.get_merchants_by_ids(db, merchant_ids)

enriched = [
    (p, merchants_map.get(p.merchant_id, MerchantDTO(..., name="Unknown")).name)
    for p in purchases
]
```

### Where the batch method lives

Each consuming module's `clients/` package exposes the batch method on both the ABC and the concrete implementation:

```python
# app/<module>/clients/merchants.py

class MerchantsClientABC(ABC):
    @abstractmethod
    async def get_merchants_by_ids(
        self, db: AsyncSession, merchant_ids: list[str]
    ) -> dict[str, MerchantDTO]:
        pass


class MerchantsClient(MerchantsClientABC):
    async def get_merchants_by_ids(
        self, db: AsyncSession, merchant_ids: list[str]
    ) -> dict[str, MerchantDTO]:
        # delegates to the merchants module's own repository
        merchants = await MerchantRepository().get_merchants_by_ids(db, merchant_ids)
        return {m_id: MerchantDTO(...) for m_id, m in merchants.items()}
```

The matching repository method in the **foreign module** contains the actual query:

```python
# app/merchants/repository.py

async def get_merchants_by_ids(
    self, db: AsyncSession, merchant_ids: list[str]
) -> dict[str, Merchant]:
    if not merchant_ids:
        return {}
    result = await db.execute(
        select(Merchant).where(Merchant.id.in_(merchant_ids))
    )
    return {m.id: m for m in result.scalars().all()}
```

This keeps the query logic inside the owning module (merchants manages its own data access), while the client adapter in the consuming module handles projection to a DTO. If the merchants module is extracted to a microservice, only `MerchantsClient` changes — everything else is untouched.

### When to apply

Apply this pattern whenever a **listing or bulk operation** in module A needs one or more fields from module B for each item in the result set:

| Scenario | Apply batch loading? |
| --- | --- |
| Listing endpoint needs a foreign display field (e.g., merchant name) | ✅ Yes |
| Single-item detail endpoint needs one foreign lookup | No — single lookup is fine |
| Two foreign modules are needed (e.g., merchant + user) | ✅ Yes — one batch per foreign module |
| Foreign data is already on the local row (denormalized) | No — no lookup needed |

### Empty list guard

Always guard the batch query against an empty ID list to avoid `WHERE id IN ()` syntax errors on some databases:

```python
if not merchant_ids:
    return {}
```

---

## Alternatives Considered

### SQL JOIN in the repository

A single `SELECT purchases JOIN merchants ON merchants.id = purchases.merchant_id` would be equally efficient but would require the purchases repository to import the `Merchant` ORM model — a direct violation of the module boundary rule established in [ADR-002](002-not-to-use-dedicated-dtos.md) and enforced in `CONTRIBUTING.md`. It would also make the join non-replaceable when the foreign module becomes a microservice.

### ORM relationship / lazy loading

Defining a SQLAlchemy `relationship` between `Purchase` and `Merchant` and relying on lazy loading is exactly the N+1 anti-pattern in disguise. It would also couple the two ORM models, which are in different modules.

### Eager loading (`joinedload` / `selectinload`)

SQLAlchemy's `selectinload` issues a `WHERE id IN (...)` automatically — functionally identical to the manual batch approach but dependent on the ORM relationship existing between the two models, which again violates module boundaries.

### Denormalizing merchant_name onto the purchase row

Storing `merchant_name` on `purchases` avoids the lookup entirely but creates a data consistency risk (merchant name changes orphan historical records) and couples schema design to query convenience. Rejected.

---

## Consequences

- **Performance:** List endpoints that enrich with foreign data always execute exactly 2 queries regardless of page size.
- **Testability:** Services remain fully unit-testable — the batch client method is mocked via `create_autospec`, and tests can assert it is called exactly once with the collected IDs.
- **Microservice migration path:** The concrete client class is the only code that changes when a module is extracted. The ABC, service, and tests are unaffected.
- **Convention:** Every new listing endpoint that needs cross-module fields must add a `get_<entities>_by_ids` method to the relevant client. This is the default — single-item lookups in list loops are a code-review rejection criterion.
