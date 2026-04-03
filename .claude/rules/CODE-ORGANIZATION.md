---
name: code-organization
type: rule
description: How to organize code files under app/; file splitting thresholds and patterns
---

# CODE-ORGANIZATION

## Default: One File Per Layer

Every module starts with one file per layer. Maintain this as long as files remain readable (typically under 200 lines).

```text
app/<module>/
  __init__.py
  models.py           ← SQLAlchemy ORM
  schemas.py          ← Pydantic schemas
  repositories.py     ← DB access (ABC + impl)
  services.py         ← Business logic
  policies.py         ← Pure rule enforcement
  exceptions.py       ← Domain exceptions
  errors.py           ← ErrorCode enum
  composition.py      ← Dependency wiring
  api.py              ← FastAPI router
```

**Do not split preemptively.** Start flat; split only when navigation becomes difficult.

## Helper Functions: `_helpers.py`

Internal helper functions that support multiple layers belong in `_helpers.py`:

```python
# app/<module>/_helpers.py
def apply_purchase_confirmation(purchase: Purchase, confirmed_at: datetime) -> Purchase:
    """Pure function: no side effects, no I/O."""
    purchase.status = PurchaseStatus.CONFIRMED
    purchase.confirmed_at = confirmed_at
    return purchase

def calculate_cashback(amount: Decimal, percentage: Decimal) -> Decimal:
    """Calculation shared by services and background jobs."""
    return (amount * percentage) / Decimal("100")
```

### Helper Rules

- **Internal only**: Never imported from outside the module.
- **No business logic ownership**: Support code that owns logic; don't own logic themselves.
- **Full type hints required**: All helpers must have type annotations.
- **Named with discipline**: `apply_*`, `calculate_*`, `build_*`, `format_*`.
- **Injected via composition**: Like any other dependency.

## When to Split

| File | Threshold | Strategy |
|------|-----------|----------|
| `api.py` | ~200 lines OR distinct endpoint groups (admin vs. public) | Create `api/` package with `admin.py`, `public.py` |
| `services.py` | ~200 lines OR distinct operation types (create, lifecycle, callbacks) | Create `services/` package with multiple modules |
| `schemas.py` | ~150 lines OR many enum types | Create `schemas/` package with `input.py`, `output.py` |
| `repositories.py` | ~150 lines OR clearly separable query types | Create `repositories/` package with multiple modules |

**Judgment call**: A 250-line file with good sectioning may be more readable than three 80-line files with blurry responsibilities.

## Splitting the API Layer Example

### Before (Single File)

```text
app/offers/
  api.py         ← ~250 lines, mixed admin + public endpoints
```

### After (Package)

```text
app/offers/
  api/
    __init__.py       ← Imports and re-exports routers
    admin.py          ← Admin endpoints (create, update, delete)
    public.py         ← Public endpoints (list, get details)
```

```python
# app/offers/api/admin.py
from fastapi import APIRouter
router = APIRouter(prefix="/offers", tags=["offers"])

@router.post("/", ...)
async def create_offer(...):
    ...

# app/offers/api/__init__.py
from app.offers.api.admin import router as admin_router
from app.offers.api.public import router as public_router
__all__ = ["admin_router", "public_router"]

# app/main.py
from app.offers.api import admin_router, public_router
app.include_router(admin_router)
app.include_router(public_router)
```

## Test File Organization

Tests mirror source layout exactly:

```text
tests/unit/<module>/
  test_<module>_api.py
  test_<module>_services.py
  test_<module>_policies.py
  test_<module>_repositories.py
  test_<module>_<helpers>.py       # If helpers exist

tests/integration/<module>/
  test_<module>_<endpoint>.py      # One per endpoint
```

---
