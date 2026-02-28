# Prompt: Review Code Against Project Standards

Use this prompt to perform a structured self-review of a diff, branch, or set of files before opening a PR. Hand this to an AI with the output of `git diff main...HEAD` (or a specific file list) as context.

This is not a substitute for human peer review. Its purpose is to catch layer violations, missing tests, security oversights, and style inconsistencies before a human reviewer spends time on them.

## Context Files (Read First)

- `docs/agents/feature-guide.md` — layer responsibilities, error handling convention, logging rules
- `docs/agents/testing-guidelines.md` — what must be tested and at which level
- `docs/agents/quality-gates.md` — mandatory gates and their scope
- `docs/design/error-handling-strategy.md` — the canonical error response shape

## Instructions

Run `git diff main...HEAD` (or the diff provided below) and evaluate every changed file against the checklist that follows. For each finding, state:

1. **File and approximate line** — where the issue is
2. **Category** — which checklist item it violates
3. **Severity** — `blocking` (must fix before merge) or `advisory` (recommended improvement)
4. **Suggested fix** — a concrete, actionable recommendation

After the full checklist pass, produce a summary:

- **Verdict:** `approved` / `approved with advisories` / `changes required`
- **Blocking findings:** numbered list (empty if none)
- **Advisory findings:** numbered list (empty if none)

Do not suggest changes that contradict established decisions documented in `docs/design/` ADRs or the `Decisions` section of any relevant prompt file.

---

## Diff / Files to Review

> **Paste the diff or list the files here before handing to the AI.**

```diff
<!-- paste output of: git diff main...HEAD -->
```

---

## Review Checklist

### Architecture & Layering

- [ ] No business logic in `api.py` — route handlers only call services and map exceptions to HTTP responses.
- [ ] No `HTTPException` raised in `services.py`, `repositories.py`, or `policies.py` — domain exceptions only.
- [ ] Services depend on abstractions (`RepositoryABC`, `Callable`) injected via `__init__()`, not on concrete classes instantiated internally.
- [ ] Policy functions are pure: no DB access, no side effects, no return value on success.
- [ ] Repositories contain only DB queries — no business rules, no policy calls.
- [ ] New ORM models are registered in `app/models.py`.

### Error Handling

- [ ] Every domain exception defined in `exceptions.py` has a corresponding `ErrorCode` in `errors.py`.
- [ ] Every `except <DomainException>` block in `api.py` uses the correct `core/errors/builders.py` factory (`validation_error`, `business_rule_violation_error`, etc.).
- [ ] A catch-all `except Exception` block exists in every route handler, logs at `ERROR`, and raises `internal_server_error()`.
- [ ] No bare `except Exception` blocks that swallow errors silently (no empty `pass` or `return None`).
- [ ] Error response shape is `{"error": {"code": ..., "message": ..., "details": {...}}}` — never a raw string or non-standard structure.

### API Design

- [ ] All routes use the `/api/v1/` prefix.
- [ ] Response models are declared on all route handlers (`response_model=`).
- [ ] HTTP status codes are correct: `201` for creation, `200` for reads and updates, `204` for deletes with no body (or `200` with a body), `409` for business rule violations, `422` for validation errors.
- [ ] Paginated list endpoints include `total`, `page`, `page_size` in the response schema.
- [ ] Authenticated endpoints inject `get_current_user` or `get_current_admin_user` via `Depends()`.
- [ ] For list responses with nested items, `model_validate()` is called explicitly on each item.

### Security

- [ ] No secrets, passwords, or tokens logged at any level.
- [ ] No hardcoded credentials or API keys in any file.
- [ ] Admin-only endpoints use `get_current_admin_user`, not `get_current_user`.
- [ ] No wildcard CORS origins (`*`) in any configuration.
- [ ] No new dependencies added to `pyproject.toml` without justification in the PR description.

### Logging

- [ ] `INFO` is used only for successful state-mutating operations (create, update, delete, login). Not for read-only operations.
- [ ] `DEBUG` is used for expected negative paths (not-found, validation failures, policy violations).
- [ ] `ERROR` is used only in the catch-all exception handler in `api.py`.
- [ ] Contextual data is passed via `extra={}`, never interpolated into the message string.
- [ ] No duplicate logging of the same event in both the service/policy layer and the API layer.

### Database & Migrations

- [ ] A migration file exists in `alembic/versions/` for every ORM model change.
- [ ] The migration's `downgrade()` function correctly reverses `upgrade()`.
- [ ] New nullable columns use `nullable=True` in the migration.
- [ ] New non-nullable columns have a `server_default` to avoid breaking existing rows.
- [ ] `seeds/all.sql` is updated if the schema change affects tables that have seed data.

### Tests

- [ ] Every new policy function has at least one test for the happy path and one per violation.
- [ ] Every new service method has at least one test for the happy path and one per domain exception.
- [ ] Every new API endpoint has tests for all HTTP response codes it can return (success, validation error, domain error, auth failure).
- [ ] No test bypasses `app.dependency_overrides` by importing and calling service methods directly in API tests.
- [ ] No tests import from `app.core.database` to create a real DB session — all DB access is mocked.
- [ ] `conftest.py` factory fixtures are used for creating test data, not inline dict literals repeated across tests.

### Code Style & Conventions

- [ ] All files pass `make lint` (flake8, isort, black).
- [ ] No unused imports.
- [ ] `api-requests/` `.http` files exist for all new endpoints, covering every response code.
- [ ] Markdown files (if any changed) pass `markdownlint` formatting rules.
- [ ] No `print()` statements — use `logging`.
- [ ] No `TODO` comments left in production code paths (stubs and scaffolding are acceptable only in the same commit they are introduced and resolved).

### Documentation

- [ ] If a design decision was made that is not self-evident from the code, an ADR or inline comment explains it.
- [ ] If `docs/` files are affected, they follow the markdown style guide in `docs/agents/markdown-guidelines.md`.
