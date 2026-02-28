# Prompt: Write Tests for a Feature

Use this prompt after a feature is fully implemented and all manual smoke tests in the `api-requests/` `.http` files are passing. Do not write tests speculatively — the implementation must be stable first.

## Context Files (Read First)

Before writing any code, read the following files in full:

- `docs/agents/testing-guidelines.md` — all conventions, patterns, naming rules, and examples. Follow it exactly; do not invent alternatives.
- `docs/design/architecture-overview.md` — system structure and module boundaries
- `docs/design/data-model.md` — entity relationships and field conventions; needed to write accurate fixtures
- `docs/design/error-handling-strategy.md` — error response shape and exception hierarchy; needed to assert on error responses correctly
- `docs/design/security-strategy.md` — auth model and token handling; needed for auth scenario tests
- All ADR files under `docs/design/adr/` — rationale behind conventions; helps avoid testing anti-patterns that conflict with architectural decisions
- The functional spec listed in the **Test Specification** section below — BDD scenarios are the test coverage checklist.
- The implemented files for the feature: `models.py`, `schemas.py`, `policies.py`, `repositories.py`, `services.py`, `api.py`, etc. — understand the code before writing tests for it.

---

## What to Write

### Coverage target

Every BDD scenario in the functional spec must produce exactly one test. Use the scenario description as the test name, converted to snake_case with the project naming convention (`test_{sut}_{result}_on_{condition}`). No scenario may be left untested; no test may lack a corresponding scenario.

### Test files

| File | What it covers |
| --- | --- |
| `tests/<module>/test_<module>_<support>.py` | One test per public method of any support module (e.g., `token_provider.py`, `clients.py`, `password_utils.py`) — happy path and each failure mode |
| `tests/<module>/test_<module>_policies.py` | One test per policy function — happy path and each violation scenario |
| `tests/<module>/test_<module>_services.py` | One test per service method call — happy path and each sad path/exception scenario |
| `tests/<module>/test_<module>_api.py` | One test per HTTP response code the endpoint can return, including all auth scenarios |

Extend existing files if they already exist. Only create new files if the module has no tests yet. Do not modify `tests/conftest.py` unless a new shared factory is genuinely needed by multiple test files.

**Support modules** are any non-standard files in the module directory that contain testable logic — e.g., `token_provider.py`, `clients.py`, `password_utils.py`, `validators.py`. Identify them in Step 1 before writing any tests.

### What not to test

Do not test repository implementations directly (thin DB wrappers). Do not test FastAPI routing or SQLAlchemy internals. See `docs/agents/testing-guidelines.md §1` for the full list.

## Commit Protocol

Each step that produces code is a **separate commit**. Do not begin the next step until the current step's commit is approved and executed by the human.

To close a step:
1. Run `make lint && make format && make test` — all must pass.
2. Stage the changes and output `git diff --staged`.
3. Propose a commit message.
4. **Wait for explicit human approval before executing `git commit`.**

---

## Test Specification

> **Fill this section in before handing to the AI.**

- **Functional spec:** `docs/specs/functional/<!-- e.g. purchases/PU-01-purchase-ingestion.md -->`
- **Domain module:** `app/<!-- e.g. purchases -->/`
- **Notes:** `<!-- Anything not covered by the spec or that overrides it -->`

---

## Steps

### Step 1 — Read the spec and map scenarios to tests

First, scan the module directory for any **support modules** — non-standard files beyond `policies.py`, `services.py`, and `api.py` that contain testable logic (e.g., `policies.py`, `token_provider.py`, `clients.py`, `password_utils.py`). List them and identify which public methods need tests.

Then go through each BDD scenario in the functional spec. For each one, note:
- which layer it exercises (support module / policy / service / API)
- what the test name will be
- what inputs and expected output or exception it implies

Do not write any code yet. Output the full mapping — support modules first, then scenarios — as a list for human review before proceeding.

### Step 2 — Write support module tests (if any)

For each support module identified in Step 1, create `tests/<module>/test_<module>_<support>.py`. Test every public method — happy path and each failure mode or exception it can raise. Inject or mock any dependencies via the constructor. Skip this step if no support modules were identified. Then close the step per the Commit Protocol above.

### Step 3 — Write policy tests

Implement `tests/<module>/test_<module>_policies.py`. One test per scenario. Policies are pure functions — no mocks needed, just inputs and assertions. Then close the step per the Commit Protocol above.

### Step 4 — Write service tests

Implement `tests/<module>/test_<module>_services.py`. Use constructor injection to provide mocked dependencies. Mock the repository and any policy callables. Test that the service calls them correctly and propagates or catches exceptions as expected. Then close the step per the Commit Protocol above.

### Step 5 — Write API tests

Implement `tests/<module>/test_<module>_api.py`. Use `TestClient` with `app.dependency_overrides` to replace the service. Test every HTTP response code — successful responses, domain exception mappings, auth failures (401, 403), and validation errors (422). Then close the step per the Commit Protocol above.
