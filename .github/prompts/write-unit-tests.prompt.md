# Prompt: Write Unit Tests for a Feature

Use this prompt after a feature is fully implemented and all manual smoke tests in the `.http` files are passing. Do not write unit tests speculatively — the implementation must be stable first.

## Context

- Read `AGENTS.md` for project context, testing conventions, and quality gates.
- Read `docs/guidelines/unit-testing.md` — all conventions, patterns, naming rules; follow it exactly.
  - § 1-4: Shared standards (AAA structure, imports, fixtures)
  - § 5-14: Unit testing specifics (services, API endpoints, policies, validators, helpers)
  - § 15-16: Checklist and common issues
- Read the functional spec for this feature — BDD scenarios are the test coverage checklist.
- Read the implemented files: `models.py`, `schemas.py`, `policies.py`, `services.py`, `api.py`, etc.
- Read `tests/unit/conftest.py` before writing any fixtures — reuse existing factories.

## Constraints

- Every BDD scenario must produce exactly one test; no scenario may be left untested.
- Do not test thin repository implementations or framework internals.
- Do not modify `tests/unit/conftest.py` unless a new shared factory is genuinely needed by multiple test files.
- Extend existing test files if they already exist; only create new files if the module has no tests yet.

---

## Steps

### Step 1 — Map BDD scenarios to tests

- Scan the module directory for support modules with testable logic beyond `policies.py`, `services.py`, and `api.py` (e.g., `token_provider.py`, `clients.py`).
- For each BDD scenario, note which layer it exercises, what the test name will be, and what inputs and expected output it implies.
- Output the full mapping as a list for human review before writing any code.

### Step 2 — Write support module tests (if any)

- Create `tests/unit/<module>/test_<module>_<support>.py` for each support module identified in Step 1.
- Test every public method — happy path and each failure mode.
- Skip if no support modules were identified.

### Step 3 — Write policy tests

- Create or extend `tests/unit/<module>/test_<module>_policies.py`.
- Policies are pure functions — no mocks needed, just inputs and assertions.
- Write one test per scenario.

### Step 4 — Write service tests

- Create or extend `tests/unit/<module>/test_<module>_services.py`.
- Mock ABCs with `create_autospec(TheABC)`; mock callables with `Mock()`; mock `UnitOfWorkABC` with a plain `Mock` (not `create_autospec`).
- Create `db = AsyncMock()` locally in each read-only test; create `uow = _make_uow()` locally in each write test.
- Assert `uow.commit.assert_called_once()` on success; assert `uow.commit.assert_not_called()` on failure paths.
- Assert that dependencies are called with the correct arguments and their return values are mapped correctly.

### Step 5 — Write API tests

- Create or extend `tests/unit/<module>/test_<module>_api.py`.
- Use `TestClient` with `app.dependency_overrides` to replace the service.
- Write one all-fields success test asserting every field in the response schema individually; extract assertions into a `_assert_*_response` helper.
- Write one parametrized test enumerating every domain exception the handler can raise, including the generic `Exception` → 500 fallback — no exception may be omitted.
- Cover all HTTP response codes: success, validation errors, domain errors, and auth failures (401, 403).

### Step 6 — Test private implementation details (if applicable)

If the module exports internal/private functions (prefixed with `_`) that have significant business logic or are called by multiple entry points, add direct unit tests for them:

- Create or extend a section in an existing test file (e.g., `tests/unit/<module>/test_<module>_handlers.py`).
- **Always add a comment above the import** explaining why private functions are being tested.
- **Add `# pyright: ignore[reportPrivateUsage]`** on each imported private function line to suppress type checker warnings.
- Mock all dependencies exactly as in service tests.
- Follow AAA structure and naming conventions.
- See [Unit Testing Guidelines](../../docs/guidelines/unit-testing.md) § 14a for detailed rules.

Example:

```python
# Testing internal handlers to verify event-to-audit mapping.
# See docs/guidelines/unit-testing.md § Testing Private Implementation Details.
from app.core.audit.handlers import (
    _handle_purchase_confirmed,  # pyright: ignore[reportPrivateUsage]
    _handle_purchase_rejected,  # pyright: ignore[reportPrivateUsage]
)
```

---

## After Writing Unit Tests

When complete, use these additional prompts:
- [Write Integration Tests](./write-integration-tests.prompt.md) — for testing endpoints against a real database
- [Write E2E Tests](./write-e2e-tests.prompt.md) — for testing multi-step user flows across modules

Before submitting, verify all tests pass:
```bash
make test         # unit tests
make lint         # code style
make coverage     # 85% hard gate
```
