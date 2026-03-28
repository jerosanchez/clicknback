# Prompt: Write a GitHub Issue for a Feature Requirement Implementation

Use this prompt when you need to create a GitHub issue for implementing a documented feature requirement (FR). The FR is already designed and specified (functional spec, API contract, architecture), but the implementation code does not yet exist (greenfield work).

This prompt differs from `write-github-issue.prompt.md` (generic issues) and `write-adr.prompt.md` (architectural decisions) by focusing specifically on **converting existing documentation into actionable implementation tasks** within a clear module structure.

## When to Use This Prompt

- A functional specification (e.g., `FF-01-set-feature-flag.md`) exists and is frozen or approved.
- An API contract (e.g., `set-feature-flag.md`) is documented with full request/response/error details.
- Architecture and module design decisions are already documented (e.g., ADR-018).
- The data model (e.g., `docs/design/data-model.md`) is finalized.
- No implementation code exists yet (greenfield feature or module).
- You need to create a GitHub issue that provides enough context for anyone to implement the feature.

## When NOT to Use This Prompt

- The feature is undocumented or still in design phase → write the ADR and specs first, then use this prompt.
- The issue is for a bug fix, chore, or maintenance task → use `write-github-issue.prompt.md`.
- The issue is proposing an architectural decision → use `write-adr.prompt.md`.
- The implementation is partially complete → adjust the implementation plan accordingly.

---

## Issue Structure for FR Implementation

### 1. Title

Write as an imperative verb + noun phrase naming the primary user-facing action or a key artifact.

**Good examples:**

- "Implement Set Feature Flag endpoint and service layer"
- "Implement Create Payout endpoint and async withdrawal workflow"
- "Implement Offer creation API with merchant authorization and validity validation"

**Anti-examples:**

- "Feature Flag System" (too vague; doesn't name the action)
- "Fix bugs in feature flags" (signals bug fix, not implementation)
- "Feature flag stuff" (unclear)

### 2. Summary

One paragraph (3–5 sentences) explaining:

1. What is being implemented and why it matters.
2. That the feature is designed but not yet implemented (greenfield or backlog).
3. Reference the key artifacts (functional spec, API contract, ADR).
4. Mention the expected outcome visible to users or consumers.

```markdown
## Summary

The feature flag system is fully designed (ADR-018, FF-01 functional spec, set-feature-flag API contract) but requires implementation across the domain layer (repositories, services, policies, exceptions), API layer (schemas, endpoint), tests (unit and integration), and cross-module client abstraction. Implement `PUT /api/v1/feature-flags/{key}` (Set Feature Flag) along with all supporting infrastructure, enabling admins to create or update feature flags at runtime without redeployment and allowing the purchases module to evaluate flags to gate background job execution.
```

### 3. Feature Overview

Adapt the traditional "Problem Statement" section to describe the feature's design status and requirements. Use subsections:

**Current State:**
- Describe that the feature is documented but not implemented.
- Reference all relevant design artifacts (ADR, functional spec, API contract, data model section).
- Use inline links to these files.
- Explain the business or technical value briefly.

**What Needs to Happen:**
- List 3–5 key requirements extracted from the design (what users can do, what validations exist, what scope constraints apply, what integrations exist).
- Reference specific functional spec sections or API contract constraints.
- Mention any cross-module dependencies or client abstractions that must be created.

**Example:**

```markdown
## Feature Overview

### Current State

The feature flag system is **designed but not yet implemented** (greenfield). All architectural decisions, data model, API contracts, and functional specifications already exist.

**Related design artifacts:**

- [ADR-018: Feature Flag System](../../../docs/design/adr/018-feature-flag-system.md) — Full architecture and module structure.
- [FF-01: Set Feature Flag](../../../docs/specs/functional/feature-flags/FF-01-set-feature-flag.md) — Functional specification with BDD criteria.
- [Set Feature Flag API Contract](../../../docs/design/api-contracts/feature-flags/set-feature-flag.md) — Complete HTTP contract.
- [Data Model](../../../docs/design/data-model.md) § 5.9 — Database schema.

### What Needs to Happen

Implement the complete `app/feature_flags/` module such that:

- Admins can create or update feature flags via `PUT /api/v1/feature-flags/{key}`.
- Flags support three scope types: `global`, `merchant`, `user`.
- The unique constraint prevents duplicate records for the same key and scope.
- Upsert semantics: existing flags are updated; new ones are created.
- Validation enforces scope_id constraints per the functional spec.
- Cross-module client (purchases module) can evaluate flags via `is_enabled(...)`.
```

### 4. Implementation Plan

Break the work into **logical phases** that respect the layering (data → domain → API → tests → integration) and module anatomy.

Each phase should:

- Have a descriptive title (e.g., "Phase 1 — Database & Data Layer", "Phase 2 — Domain Layer").
- Contain a numbered or task-list breakdown of concrete actions.
- Include references to files, classes, or methods that will be created/modified.
- Use task lists (`- [ ]`) so progress is trackable in GitHub.

**Phases typically follow this order:**

1. **Database & Data Layer** — ORM model, migration, repository interface and implementation.
2. **Domain Layer** — Exceptions, error codes, policies, services with business logic.
3. **API Layer** — Schemas, route handlers, error mapping, composition.
4. **Cross-Module Integrations** — Client abstractions, dependencies in other modules.
5. **Unit Tests** — Policies, repositories, services, API endpoints.
6. **Integration Tests** — Full HTTP stack with real DB.
7. **Documentation & Verification** — HTTP request files, quality gates.

**Example structure:**

```markdown
## Implementation Plan

### Phase 1 — Database & Data Layer

- [ ] Create Alembic migration: `alembic/versions/<timestamp>_create_feature_flags_table.py`
  - Create `feature_flags` table with all columns and constraints.
  - Enforce `UNIQUE (key, scope_type, COALESCE(scope_id, ''))`.
- [ ] Create ORM model in `app/feature_flags/models.py` — `FeatureFlag` class.
- [ ] Register model in `app/models.py` for Alembic.
- [ ] Create repository in `app/feature_flags/repositories.py`:
  - `FeatureFlagRepositoryABC` — interface with methods: `upsert(...)`, `get_by_key_and_scope(...)`, `list_all()`.
  - `FeatureFlagRepository` — SQLAlchemy 2.0 async implementation.

### Phase 2 — Domain Layer (Business Logic)

- [ ] Create `app/feature_flags/exceptions.py`:
  - `FeatureFlagNotFound`, `FeatureFlagScopeIdRequired` — include context attributes.
- [ ] Create `app/feature_flags/errors.py`:
  - `ErrorCode` enum: `FEATURE_FLAG_NOT_FOUND`, `FEATURE_FLAG_SCOPE_ID_REQUIRED`.
- [ ] Create `app/feature_flags/policies.py`:
  - `validate_scope_id_required(...)` — raise exception if required scope_id is missing.
  - `validate_key_format(...)` — enforce key constraints (snake_case, max 100 chars).
- [ ] Create `app/feature_flags/services.py`:
  - `FeatureFlagService` with methods: `upsert(...)`, `is_enabled(...)`, `delete(...)`, `get(...)`.

### Phase 3 — API Layer

- [ ] Create `app/feature_flags/schemas.py`:
  - `FeatureFlagCreate` — input schema for requests.
  - `FeatureFlagOut` — output schema for responses.
- [ ] Create `app/feature_flags/api.py`:
  - Route `PUT /api/v1/feature-flags/{key}` with admin role check.
  - Error mapping from domain exceptions to HTTP responses.
- [ ] Create `app/feature_flags/composition.py`:
  - Dependency factories: `get_feature_flag_repository()`, `get_feature_flag_service()`.
- [ ] Update `app/main.py`:
  - Include the feature_flags router.

### Phase 4 — Cross-Module Integration

- [ ] Create `app/purchases/clients/feature_flags.py`:
  - `FeatureFlagsClientABC` interface.
  - `FeatureFlagsClient` implementation calling `FeatureFlagService.is_enabled()`.
- [ ] Update `app/purchases/jobs/verify_purchases/dispatcher.py`:
  - Inject feature_flags client.
  - Check `await self._feature_flags.is_enabled("purchase_confirmation_job")` before dispatch.
- [ ] Update `app/purchases/composition.py`:
  - Wire the client into the dispatcher.

### Phase 5 — Unit Tests

- [ ] Create `tests/unit/feature_flags/test_feature_flags_policies.py` — validation logic.
- [ ] Create `tests/unit/feature_flags/test_feature_flags_repositories.py` — CRUD operations.
- [ ] Create `tests/unit/feature_flags/test_feature_flags_services.py` — business logic, resolution algorithm.
- [ ] Create `tests/unit/feature_flags/test_feature_flags_api.py` — endpoint, error mapping, auth.

### Phase 6 — Integration Tests

- [ ] Create `tests/integration/feature_flags/test_feature_flags_api.py`:
  - Happy path: create, update, retrieve flags.
  - Test scope isolation and unique constraint.
  - Test auth failures (401, 403).
  - Test validation errors (422).

### Phase 7 — Documentation & Verification

- [ ] Create `http/feature-flags/set-feature-flag.http` — manual testing request file.
- [ ] Run `make test && make coverage` — verify 85%+ coverage gate.
- [ ] Run `make lint` — verify all linting passes.
- [ ] Run `make security` — verify security gate passes.
```

### 5. Acceptance Criteria

List testable, measurable conditions extracted from the functional spec and API contract. Use task lists so progress is visible in GitHub.

Group criteria by concern:

- **Data integrity** — constraint enforcement, unique key validation.
- **API contract** — endpoint exists, returns correct status, correct error codes.
- **Business logic** — validation rules, policies, service logic correct.
- **Test coverage** — unit tests, integration tests, coverage thresholds.
- **Cross-module** — client abstraction created, consumers updated.
- **Quality gates** — linting, security, coverage all passing.

**Example:**

```markdown
## Acceptance Criteria

### Data Integrity & Domain Logic

- [ ] Database migration is applied and the `feature_flags` table exists with correct schema and constraints.
- [ ] ORM model is defined and registered in `app/models.py`.
- [ ] Unique constraint `UNIQUE (key, scope_type, COALESCE(scope_id, ''))` prevents duplicate flags.
- [ ] Upsert semantics work correctly: existing flags update, new flags create.
- [ ] All validation policies are implemented (scope_id required, key format, etc.).

### API Contract

- [ ] Endpoint `PUT /api/v1/feature-flags/{key}` exists and accepts correct request schema.
- [ ] Success response returns HTTP 200 with full flag record (FeatureFlagOut schema).
- [ ] All error cases are mapped to correct HTTP status codes:
  - `FEATURE_FLAG_SCOPE_ID_REQUIRED` → 422 with detailed error response.
  - `VALIDATION_ERROR` → 422.
  - Non-admin → 403 Forbidden.
  - Unauthenticated → 401 Unauthorized.

### Testing & Coverage

- [ ] Unit tests cover all policies, repositories, services, and API routes.
- [ ] Unit test coverage for `feature_flags` module is ≥ 85%.
- [ ] Integration tests cover happy path and all exception scenarios.
- [ ] Integration tests use real PostgreSQL with rolled-back transactions for isolation.

### Cross-Module Integration

- [ ] Client abstraction `app/purchases/clients/feature_flags.py` created with `FeatureFlagsClientABC`.
- [ ] Purchases dispatcher injected with and uses the feature flag client.
- [ ] Other modules can follow the same pattern (composition.py updated).

### Quality Gates & Documentation

- [ ] HTTP request file created (`http/feature-flags/set-feature-flag.http`).
- [ ] All quality gates pass: `make lint`, `make test`, `make coverage`, `make security`.
- [ ] Implementation matches ADR-018 architecture and naming conventions.
- [ ] Code follows project guidelines (feature architecture, unit testing, async database layer, UoW pattern).
```

### 6. Related Documentation

Link to all relevant design and specification artifacts. Group by category and include brief descriptions of how each document is used.

```markdown
## Related Documentation

### Architecture & Design

- [ADR-018: Feature Flag System](../../../docs/design/adr/018-feature-flag-system.md) — Complete architecture, module structure, data model, consumer client pattern.
- [ADR-010: Async Database Layer](../../../docs/design/adr/010-async-database-layer.md) — AsyncSession patterns, SQLAlchemy 2.0 style.
- [ADR-021: Unit of Work Pattern](../../../docs/design/adr/021-unit-of-work-pattern.md) — Service transaction boundaries, UoW interface.

### Specifications & Contracts

- [FF-01: Set Feature Flag](../../../docs/specs/functional/feature-flags/FF-01-set-feature-flag.md) — Functional spec with BDD criteria, constraints, use cases.
- [Set Feature Flag API Contract](../../../docs/design/api-contracts/feature-flags/set-feature-flag.md) — HTTP contract, request/response/error schemas.
- [Data Model](../../../docs/design/data-model.md) § 5.9 — `feature_flags` table schema and constraints.

### Implementation Guidelines

- [Feature Architecture](../../../docs/guidelines/feature-architecture.md) — Module anatomy, layer responsibilities, composition.
- [Unit Testing](../../../docs/guidelines/unit-testing.md) — Test patterns, mocking, fixtures, coverage standards.
- [Integration Testing](../../../docs/guidelines/integration-testing.md) — Test isolation, client fixtures, real database patterns.
- [Quality Gates](../../../docs/guidelines/quality-gates.md) — Lint, test, coverage, security checks.
```

### 7. Out of Scope

Clearly define what this issue does NOT include. This prevents scope creep and clarifies expectations for implementers.

```markdown
## Out of Scope

- Implementation of other feature flag CRUD endpoints (delete, list, get) — tracked in separate issues.
- Implementation of `GET /feature-flags/{key}/evaluate` read endpoint (FF-04) — separate issue.
- Extracting feature flags to a microservice — future architectural decision; client abstraction enables this.
- Feature flag audit logging — managed separately by the event-driven audit module.
```

### 8. Notes (Optional)

Additional context, assumptions, trade-offs, or guidance for implementers.

```markdown
## Notes

- The feature flag system is **fail-open**: absence of a flag record means "enabled" — ensure this is understood by implementers.
- The unique constraint uses `COALESCE(scope_id, '')` to handle SQLAlchemy `NULL` handling in unique indexes.
- The purchases module is the initial consumer; other modules follow the same client abstraction pattern.
- Error responses must include a detailed `details` object (e.g., `"details": { "scope_type": "merchant" }`) — see `docs/design/error-handling-strategy.md`.
- Service method `is_enabled()` implements the resolution algorithm; consumers must never duplicate this logic.
```

---

## Tips for Writing Effective FR Implementation Issues

### 1. Extract Information from Existing Documents

- **From ADR:** Architecture, module structure, data model, cross-module patterns, composition pattern.
- **From Functional Spec:** Constraints, validation rules, BDD scenarios, use cases, domain concepts.
- **From API Contract:** Request schema, response schema, all error codes, HTTP status codes, error detail structure.
- **From Data Model:** Table names, column types, constraints (uniqueness, foreign keys, defaults).

### 2. Layer the Implementation Plan Correctly

Follow the modular monolith layering:

1. **Data Layer** (ORM, migrations, repositories)
2. **Domain Layer** (exceptions, errors, policies, services)
3. **API Layer** (schemas, routes, composition)
4. **Tests** (unit → integration)
5. **Cross-Module** (client abstractions, consumer updates)
6. **Verification** (QA gates, documentation)

This order ensures dependencies flow from lower to higher layers; early phases unblock later phases.

### 3. Make Tasks Granular and Actionable

Each task list item should:

- Be completable in one sitting or one focused PR.
- Reference specific file paths and class names; make it obvious what to create or modify.
- Include concrete criteria (e.g., "all columns and constraints per docs/design/data-model.md").
- Avoid vague tasks like "test everything"; be specific (e.g., "test upsert logic, validation, error mapping").

### 4. Cross-Reference Architecture Guidelines

Link to project guidelines that implementers must follow:

- `docs/guidelines/feature-architecture.md` — module anatomy, layer naming.
- `docs/guidelines/unit-testing.md` — test patterns, mocking strategies, coverage thresholds.
- `docs/guidelines/integration-testing.md` — test isolation, real DB usage, client fixtures.
- `docs/guidelines/quality-gates.md` — linting, coverage, security standards.

### 5. Reference ADRs for Non-Obvious Decisions

Link to ADRs for decisions that implementers might question:

- ADR-010 for async database patterns (why `AsyncSession`, why `flush` not `commit`).
- ADR-021 for unit of work pattern (why services take `uow`, not raw `db`).
- ADR-019 for batch-loading strategy (if applicable).
- ADR-023 for event-driven audit (if events must be published).

### 6. Include All Error Scenarios from the API Contract

In the Acceptance Criteria, enumerate every error case from the API contract:

- Each distinct HTTP status code (401, 403, 422, 500, etc.).
- Each specific error code (`FEATURE_FLAG_SCOPE_ID_REQUIRED`, etc.).
- The error detail structure (what fields are in `details`).

Then, in Integration Tests section of the Implementation Plan, write a note that tests must cover all of these scenarios.

### 7. Mention Cross-Module Dependencies

If the feature requires consumer code in other modules:

- Name the module and the file (e.g., "purchases module needs a client in `app/purchases/clients/feature_flags.py`").
- Explain how the consumer uses the feature (e.g., "dispatcher checks `is_enabled()` before dispatch").
- Make it clear that the consumer integration is part of this issue's scope, not a follow-up.

---

## Workflow

1. **Ensure the feature is fully documented first:**
   - Functional spec exists and is approved.
   - API contract is finalized.
   - Architecture (ADR) is decided.
   - Data model is in `docs/design/data-model.md`.

2. **Use this prompt to draft the issue:**
   - Start with the "Feature Overview" section.
   - Break the implementation into layered phases.
   - Extracting criteria from the spec and API contract.
   - Link all relevant docs.

3. **Create the issue on GitHub** using `mcp_io_github_git_issue_write()`:
   - Use the title, summary, sections above.
   - Add labels: `feature`, `needs-design` (if not yet started), or `backlog` (if deferred).

4. **Do not leave a local draft** — GitHub Issues is the single source of truth (see `issue-workflow.md` in repo memory).

5. **Assign to a team member or milestone** as appropriate.

---

## Example Issue (Reference)

See GitHub issue #58 in this repository:

"Implement Set Feature Flag endpoint and service layer" — Created from FF-01 functional spec, set-feature-flag API contract, and ADR-018. Demonstrates all sections above in a real-world feature implementation.

