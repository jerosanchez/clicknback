---
name: review-feature-template
type: skill-template
description: Output template for the review-feature skill
---

# Feature Review Report — `<METHOD> /api/v1/<path>`

_Date: YYYY-MM-DD_

_Reviewer: GitHub Copilot_

---

## Summary

| Check | Status | Notes |
|-------|--------|-------|
| Authorization model | ✅ / ❌ | |
| Router placement | ✅ / ❌ | |
| OpenAPI response docs | ✅ / ❌ | |
| 422 error format convention | ✅ / ❌ | |
| Implementation vs spec | ✅ / ❌ | |
| Implementation vs contract | ✅ / ❌ | |
| Unit test coverage | ✅ / ❌ | |
| Integration test coverage | ✅ / ❌ | |
| HTTP smoke test accuracy | ✅ / ❌ | |

---

## Defects Found

### DEF-01 — [Short title]

**Severity:** blocking | important | minor

**Location:** `app/<module>/api/<file>.py` lines XX–YY

**Expected:** (from spec / contract)

**Actual:** (from implementation)

**Fix:** (what was changed or needs to change)

---

### DEF-02 — [Short title]

_(copy block above for each defect)_

---

## Fixes Applied

List each file modified and why:

- `app/<module>/api/<file>.py` — moved endpoint to correct router, changed auth dependency
- `app/core/errors/handlers.py` — added `RequestValidationError` handler
- `docs/design/api-contracts/<domain>/<verb-resource>.md` — updated roles, added 400/422/500 responses
- `docs/specs/functional/<domain>/<spec>.md` — updated authorization constraint, removed stale 403 scenario
- `tests/unit/<module>/test_<module>_public_api.py` — added 422, 400, 401 test cases
- `tests/integration/<module>/test_<module>_list_integration.py` — updated expected status codes
- `http/<module>/<verb-resource>.http` — corrected header comment, replaced 403 sad path with 200 user test

---

## Quality Gate Result

```text
make all-qa-gates
```

- Lint: PASS / FAIL
- Unit tests + coverage: PASS / FAIL (coverage: XX%)
- Security: PASS / FAIL
- Integration tests: PASS / FAIL
- E2E tests: PASS / FAIL
