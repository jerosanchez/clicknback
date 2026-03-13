# Code Organization and File Size Guidelines

This document is the authoritative reference for how to organize code within a module as it grows. It covers when to keep everything in a single file, when to split, how to split each layer, and how test files mirror those decisions.

---

## 1. The Default: One File Per Layer

Every module starts with one file per layer. This is the default and should be maintained as long as files remain at a **readable size** — typically under **200 lines**.

```text
app/<module>/
  __init__.py
  models.py
  schemas.py
  repositories.py
  services.py
  policies.py
  exceptions.py
  errors.py
  composition.py
  api.py          ← or api/ if split (see §3)
```

The corresponding tests mirror this:

```text
tests/<module>/
  test_<module>_api.py
  test_<module>_services.py
  test_<module>_policies.py
```

Do not split preemptively. Premature splitting adds indirection without benefit. Start flat and split only when a file becomes difficult to navigate.

---

## 2. When to Split

Split a file when it reaches a threshold where human reviewers struggle to navigate it. The practical guide:

| File | Split threshold | Split strategy |
| --- | --- | --- |
| `api.py` | ~200 lines, or distinct endpoint groups with clearly different concerns (e.g., role) | Sub-router package (see §3) |
| `services.py` | ~200 lines, or distinct operation types (creation, lifecycle, callbacks) | Service sub-modules (see §4) |
| `schemas.py` | ~150 lines, or many enum types | Schema sub-modules (see §5) |
| `repositories.py` | ~150 lines, or clearly separable query types | Repository sub-modules (see §5) |

These are guidelines, not hard rules. A 250-line file with good sectioning and a clear narrative may be more readable than three 80-line files with blurry responsibilities. Use judgment.

---

## 3. Splitting the API Layer: Sub-Router Package

When `api.py` grows beyond the threshold or has distinct endpoint groups (e.g., admin vs. public endpoints), replace the single file with a package.

### Directory Structure

```text
app/<module>/
  api/
    __init__.py       ← assembles and exports routers
    admin.py          ← endpoints requiring admin authentication
    public.py         ← endpoints accessible to regular users
```

Each sub-module defines its own `APIRouter` with the same prefix as before:

```python
# app/offers/api/admin.py
router = APIRouter(prefix="/offers", tags=["offers"])

@router.post("/", ...)
def create_offer(...): ...
```

The `__init__.py` assembles and re-exports them:

```python
# app/offers/api/__init__.py
from app.offers.api import admin, public

admin_router = admin.router
public_router = public.router

__all__ = ["admin_router", "public_router"]
```

### Wiring in `main.py`

Replace the single router include with one per sub-router:

```python
# Before
from app.offers import api as offers_api
app.include_router(offers_api.router, prefix="/api/v1")

# After
from app.offers.api import admin_router as offers_admin_router
from app.offers.api import public_router as offers_public_router

app.include_router(offers_admin_router, prefix="/api/v1")
app.include_router(offers_public_router, prefix="/api/v1")
```

### Splitting Criteria for API Sub-Modules

The most natural split boundary for the API layer is **access role**:

- **`admin.py`** — endpoints that require `get_current_admin_user`. All write operations (create, update, deactivate) typically live here, as well as admin-only listings with full details.
- **`public.py`** — endpoints that require only `get_current_user`, or that are fully public. Consumer-facing reads live here.

If role is not a useful boundary (e.g., all endpoints require admin), split by **resource area** instead:

```text
api/
  __init__.py
  lifecycle.py    ← create, activate, deactivate
  listings.py     ← GET collections with filters
  details.py      ← GET individual resource + sub-resources
```

### The Real-World Example: `offers`

Before splitting, `app/offers/api.py` was 328 lines covering three endpoints across two roles. After:

```text
app/offers/api/
  __init__.py      ← exports admin_router, public_router
  admin.py         ← 260 lines: POST /offers, GET /offers (admin listing)
  public.py        ←  86 lines: GET /offers/active
```

The split is immediately legible: `admin.py` is the admin surface, `public.py` is what end-users see.

---

## 4. Splitting the Service Layer

When `services.py` grows beyond the threshold, extract logical sub-concerns into dedicated modules under a `services/` package:

```text
app/<module>/
  services/
    __init__.py       ← re-exports the main service class
    creation.py
    lifecycle.py
    calculations.py
```

The main `<Entity>Service` class can remain in `services/__init__.py` or in a `services/service.py` and import helper functions or sub-services from sibling modules.

The public interface does not change: `composition.py` still imports and instantiates `<Entity>Service` exactly as before. Only the internal file layout changes.

---

## 5. Splitting Schemas or Repositories

For `schemas.py` or `repositories.py`, the pattern is the same: replace the file with a package and re-export from `__init__.py` so that all existing imports continue to work unchanged.

```text
app/<module>/
  schemas/
    __init__.py     ← re-exports everything: OfferCreate, OfferOut, ...
    base.py         ← shared base schemas
    listings.py     ← paginated output schemas
    enums.py        ← all Enum types
```

```python
# schemas/__init__.py
from app.offers.schemas.base import OfferCreate, OfferOut
from app.offers.schemas.listings import PaginatedOffersOut, PaginatedActiveOffersOut
from app.offers.schemas.enums import CashbackTypeEnum

__all__ = [
    "OfferCreate", "OfferOut",
    "PaginatedOffersOut", "PaginatedActiveOffersOut",
    "CashbackTypeEnum",
]
```

This is the key rule: **existing imports must continue to work**. Code in other modules that imports `from app.offers.schemas import OfferOut` must not need to change when you reorganize internals.

---

## 6. Test File Naming

Test files mirror the source file they exercise. When a source file is split into a package, the corresponding test files are named after the sub-modules:

| Source file | Test file |
| --- | --- |
| `app/offers/api.py` | `tests/offers/test_offers_api.py` |
| `app/offers/api/admin.py` | `tests/offers/test_offers_admin_api.py` |
| `app/offers/api/public.py` | `tests/offers/test_offers_public_api.py` |
| `app/offers/services.py` | `tests/offers/test_offers_services.py` |
| `app/offers/services/creation.py` | `tests/offers/test_offers_creation_service.py` |

The naming pattern is always: `test_<module>_<sub-module>_<layer>.py`

Each test file is self-contained: its fixtures, helpers, and test functions cover exactly the source file it mirrors. **Do not share fixtures between API test files via `conftest.py` unless they are truly module-wide** (e.g., the `offer_factory` that all offer tests use).

---

## 7. Maintaining Module Decoupling

These organizational changes are internal to a module. The contracts a module exposes to the outside world — imports in `main.py`, dependency factories in `composition.py`, imports in other modules' API files — do not change when you reorganize internals.

This is the design property that keeps modules ready for extraction into independent services: **each module's public surface is its `composition.py` factories and, if needed, a `clients/` package**. Everything else is private implementation detail.

When splitting, always verify that no import path crosses module boundaries at a level deeper than the module root:

```python
# ✅ Correct: import from module root
from app.offers.schemas import OfferOut

# ❌ Wrong: import from internal sub-module
from app.offers.schemas.listings import OfferOut
```

External modules import from the module root. The module root re-exports from its internal structure via `__init__.py`.
