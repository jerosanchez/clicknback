---
name: review-feature-examples
type: skill-examples
description: Real example from the list-offers audit
---

# Example: Auditing `GET /api/v1/offers`

## Context

Before the mobile team started integrating the offers listing endpoint, a full audit was performed. Five defects were found and fixed in one pass.

---

## Defects Found and Fixed

### DEF-01 — Endpoint in wrong router (admin-only instead of any user)

**Severity:** blocking

**Location:** `app/offers/api/admin.py`

**Expected:** Any authenticated user (user or admin) can list offers per the product spec.

**Actual:** `list_offers` was defined in `admin.py` with `get_current_admin_user` dependency,
making it inaccessible to regular users.

**Fix:** Moved `list_offers` (and helpers `_validate_offer_list_params`, `_map_status_to_active`,
`_VALID_OFFER_STATUS_VALUES`) to `app/offers/api/public.py`. Changed dependency to `get_current_user`.

---

### DEF-02 — OpenAPI response docs missing 400, 401, 500

**Severity:** important

**Location:** `app/offers/api/public.py`, `list_offers` route decorator

**Expected:** Route decorator documents 400, 401, 422, and 500 responses for client SDK generation
and Swagger UI completeness.

**Actual:** Only `200` and the default `422` were visible in Swagger UI.

**Fix:** Added `responses={}` dict to the `@router.get("/")` decorator with full JSON examples
for 400 (VALIDATION_ERROR), 401 (INVALID_TOKEN), 422 (VALIDATION_ERROR), 500 (INTERNAL_SERVER_ERROR).

---

### DEF-03 — FastAPI 422 format did not match app convention

**Severity:** blocking

**Location:** `app/core/errors/handlers.py`

**Expected:** All error responses use `{"error": {"code", "message", "details"}}`.

**Actual:** Pydantic type validation failures (`RequestValidationError`) returned FastAPI's default
`{"detail": [...]}` format, bypassing the global `HTTPException` handler.

**Fix:** Added a `RequestValidationError` handler in `handlers.py`:

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request, exc):
    violations = []
    for error in exc.errors():
        loc = error.get("loc", ())
        field = ".".join(str(p) for p in loc[1:]) if len(loc) > 1 else str(loc[0]) if loc else "unknown"
        violations.append({"field": field, "reason": error.get("msg", "Invalid value.")})
    return JSONResponse(
        status_code=422,
        content=error_response(
            ErrorCode.VALIDATION_ERROR,
            "Request validation failed.",
            {"violations": violations},
        ),
    )
```

---

### DEF-04 — API contract outdated and incomplete

**Severity:** important

**Location:** `docs/design/api-contracts/offers/list-offers.md`

**Expected:** Contract accurately reflects roles (any user), all query parameters, full response
shape, and all error codes with correct JSON examples.

**Actual:** Contract stated Roles: Admin, was missing `date_from`/`date_to` params, missing
`start_date`/`end_date`/`monthly_cap_per_user` fields in response, used non-standard error
shape in examples (e.g. `FORBIDDEN` code).

**Fix:** Completely rewrote the contract following the `API-CONTRACT-STRUCTURE.md` rule.

---

### DEF-05 — Functional spec reflected old admin-only access model

**Severity:** important

**Location:** `docs/specs/functional/offers/O-05-offers-listing.md`

**Expected:** Spec should say any authenticated user can list offers; no 403 scenario.

**Actual:** Spec title was "Offers Listing (Admin)"; had a "Non-admin user gets 403" sad path;
user story used "As an admin..."

**Fix:** Rewrote spec with correct user story, removed 403 scenario, updated all BDD scenarios
to use "authenticated user" instead of "admin".

---

### DEF-06 — HTTP smoke test had stale 403 sad path

**Severity:** minor

**Location:** `http/offers/list-offers.http`

**Expected:** Regular-user token should produce 200; no 403 sad path should exist.

**Actual:** File had `### 403 – Sad path: authenticated as a non-admin user` using `@userToken`,
implying a regular user was forbidden.

**Fix:** Replaced the 403 block with a `### 200 – Happy path: regular user (non-admin) can list offers`
block. Updated header comment from "Admin-only endpoint" to "Any authenticated user...".

---

### DEF-07 — Unit tests in wrong file; missing new test cases

**Severity:** important

**Location:** `tests/unit/offers/test_offers_admin_api.py` (old), `test_offers_public_api.py` (new)

**Expected:** `list_offers` tests in the public API test file; 422 tests assert the new body shape.

**Actual:** Tests were in the admin test file using `admin_client`; 422 tests only asserted status code.

**Fix:** Removed `list_offers` section from `test_offers_admin_api.py`. Added full section to
`test_offers_public_api.py` using `user_client`. Updated 422 parametrized tests to assert
`error.code == VALIDATION_ERROR` and `violations` array structure.

---

### DEF-08 — Integration tests expected 401 for regular user

**Severity:** important

**Location:** `tests/integration/offers/test_offers_list_admin_integration.py`

**Expected:** Regular user gets 200 (now that auth dependency is `get_current_user`).

**Actual:** `test_list_offers_admin_returns_401_on_non_admin` expected 401 for `user_http_client`.

**Note:** Before the fix, `get_current_admin_user` raised `InvalidTokenException` (→ 401) for
non-admin users. After moving to `get_current_user`, regular users get 200 as expected.

**Fix:** Renamed test to `test_list_offers_returns_200_for_regular_user`, changed assertion to
`assert response.status_code == 200`. Added `test_list_offers_returns_401_for_unauthenticated`.

---

## Quality Gate Result

After all fixes:

```text
make all-qa-gates
```

- Lint: PASS
- Unit tests + coverage: PASS (coverage 88%)
- Security: PASS
- Integration tests: PASS
- E2E tests: PASS
