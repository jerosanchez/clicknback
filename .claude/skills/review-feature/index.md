---
name: review-feature
type: skill
description: Audit an existing feature end-to-end before client/mobile implementation
---

# Skill: review-feature

## Purpose

Perform a structured audit of an existing feature before it is consumed by a client (mobile app, frontend, external partner). This skill catches mismatches between spec, implementation, OpenAPI docs, error conventions, and tests.

## When to Use

- Before a mobile/frontend team starts integrating an endpoint
- When a feature was implemented without full documentation review
- When you suspect the implementation diverges from the spec or contract
- As a pre-release quality check

## Workflow

### Step 1 — Identify the Feature Boundary

1. Clarify which endpoint(s) are in scope (method + path).
2. Locate the implementation files:
   - `app/<module>/api.py` (single file) or `app/<module>/api/` package
   - When the `api/` package exists, each endpoint has its own file:
     `app/<module>/api/<verb>_<resource>.py` (e.g. `create_offer.py`, `list_offers.py`)
   - `app/<module>/api/__init__.py` assembles individual routers into `admin_router` and `user_router`
   - `app/<module>/services.py`, `policies.py`, `repositories.py`
3. Locate the documentation files:
   - Functional spec: `docs/specs/functional/<domain>/<XX-NN-name>.md`
   - API contract: `docs/design/api-contracts/<domain>/<verb-resource>.md`
   - HTTP smoke test: `http/<module>/<verb-resource>.http`

### Step 2 — Authorization Model Check

Questions to answer:

- Which auth dependency does the route use — `get_current_user`, `get_current_admin_user`, or none?
- Is this consistent with the intended roles (spec says User/Admin/Public)?
- Is the endpoint wired into the correct aggregate router in `api/__init__.py`?
  (admin-only → included in `admin_router`; user role required → included in `user_router`)

Common defect: endpoint included in `admin_router` but spec says any user can access it.

### Step 3 — OpenAPI Response Documentation

Verify the route decorator includes a `responses={}` dict covering:

- `400` — application-level validation errors
- `401` — missing or invalid token
- `403` — forbidden (if role enforcement is present)
- `422` — type/schema validation failures
- `500` — unexpected server error
- And other responses, depending on the endpoint purpose.

Common defect: only `200` and `422` documented; `400`, `401`, `500` missing.

### Step 4 — Error Format Consistency (422 vs Convention)

FastAPI emits its own `{"detail": [...]}` format for `RequestValidationError`.
The app convention is `{"error": {"code", "message", "details"}}`.

Check that `app/core/errors/handlers.py` registers a `RequestValidationError` handler
that converts Pydantic validation errors to the app's convention.

Common defect: 422 responses from Pydantic validation return FastAPI's default format instead
of the app's `{"error": ...}` envelope.

### Step 5 — Implementation vs Spec / Contract Alignment

Compare the implementation against:

1. **Functional spec** — Are all acceptance criteria implemented?
   Are all constraints (auth rules, input validation, cross-field checks) enforced?
2. **API contract** — Do the request parameters match? Do response field names match?
   Are all error codes documented and actually raised?

Flag each divergence with:

- Location (file + line range)
- Expected behaviour (from spec/contract)
- Actual behaviour (from implementation)
- Severity: `blocking` | `important` | `minor`

### Step 6 — Unit Test Coverage

For each acceptance scenario in the spec, verify a corresponding unit test exists:

- Happy path (200/201 with full response body assertions)
- Each `400` case (invalid filter, cross-field validation)
- `401` (unauthenticated request)
- `422` (type validation failure) — must assert `error.code == VALIDATION_ERROR` and `violations` array
- `500` (unexpected service exception)
- `uow.commit.assert_called_once()` on successful writes

Also verify test placement: each endpoint has its own test file following the pattern
`test_<module>_<verb>_<resource>_api.py` (e.g. `test_offers_create_offer_api.py`,
`test_offers_list_offers_api.py`). Shared fixtures (mock clients, `offer_service_mock`,
`assert_error_code`) live in `tests/unit/<module>/conftest.py`.

### Step 7 — Integration Test Coverage

Verify at least one integration test file exists for the endpoint:
`tests/integration/<module>/test_<module>_list_<resource>_integration.py`.

Check that it exercises:
- Happy path with real DB
- Auth failure (no token → 401)
- (Optional) key business-rule failure modes

### Step 8 — HTTP Smoke Test Accuracy

Review `http/<module>/<verb-resource>.http`:

- Comment header describes the correct access model (not outdated)
- Auth token variable matches required role
- Sad path tests reflect current expected status codes (no stale 403 for endpoints that are now public)
- No hardcoded base URLs; uses `@baseUrl` variable

### Step 9 — Generate Review Report

Use the [template](./template.md) to produce a structured report summarising:

- ✅ Items that are correct
- ❌ Defects found (with location, severity, and fix)
- 🔧 Fixes applied (if running in fix mode)

### Step 10 — Apply Fixes (Fix Mode)

For each `blocking` or `important` defect:

1. Fix the implementation, tests, or docs as appropriate.
2. Re-run the relevant quality gate after each fix.
3. Run `make all-qa-gates` as the final pass.

## Constraints

- Never modify a functional spec or API contract without also updating the other (they must stay in sync).
- When moving an endpoint between routers, always update its tests, integration tests, and smoke test in the same pass.
- After adding a `RequestValidationError` handler, add or update the 422 unit tests to assert the new body shape.
- Do not declare a review complete if any quality gate is failing.

## Validation Checklist

Before closing a review-feature task:

- [ ] Endpoint file is named `<verb>_<resource>.py` and lives in `app/<module>/api/`
- [ ] Endpoint is wired into the correct aggregate router in `api/__init__.py` (admin vs user)
- [ ] Route decorator has `responses={}` covering 400/401/403/422/500
- [ ] 422 body uses app convention `{"error": {"code", "message", "details"}}`
- [ ] Functional spec reflects current authorization model
- [ ] API contract reflects current request/response shape and all error codes
- [ ] Unit tests cover all acceptance scenarios; moved to correct test file
- [ ] Integration tests updated to reflect current auth model
- [ ] HTTP smoke test header and sad paths are accurate
- [ ] `make all-qa-gates` passes with zero failures
