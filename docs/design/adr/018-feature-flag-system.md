# ADR-018: Database-Backed Feature Flag System

## Status

Accepted

## Context

Several upcoming features require the ability to enable or disable platform capabilities at runtime without a code redeployment:

- **Manual testing and demo workflows:** the purchase confirmation background job runs every 60 seconds, making step-by-step manual testing inconvenient. An operator needs to pause the job while inspecting state mid-workflow, then resume it — without restarting the process.
- **Staged rollouts after MVP:** as the product moves beyond MVP, some features (new cashback rules, fraud checks, alternative confirmation strategies) should be released to a subset of merchants or users before going fully live.
- **Incident response:** during an incident, the ability to disable a misbehaving feature immediately — without waiting for a CI/CD pipeline run — reduces the blast radius and mean time to recovery.

Three approaches were evaluated:

1. **Environment variable flags:** add a boolean env var per feature; restart the process to toggle.
2. **In-memory flags with an API:** store flags in a Python dict; expose a toggle endpoint; state is lost on restart.
3. **Database-backed flags with a REST API:** persist flags in a `feature_flags` table; expose admin-only CRUD endpoints; state survives restarts and deployments.

## Decision

We adopt a **lightweight, database-backed feature flag system** implemented as a standard ClickNBack module (`app/feature_flags/`) following the same layered architecture used by all other domain modules: models, schemas, repository, service, policies, exceptions, and API.

### Key design choices

**DB-backed persistence:** Flag state must survive process restarts and deployments. Environment variables require a restart to change; an in-memory store loses state on every restart. A single `feature_flags` table — already managed by Alembic and backed by the same PostgreSQL instance used by all other data — provides durable state with no additional infrastructure.

**Scoped flags:** A flag can apply globally to the entire platform, or be narrowed to a specific merchant or user via a `(key, scope_type, scope_id)` triple. This enables targeted testing (disable fraud check only for the `BankSimFail` merchant) and supports future progressive delivery patterns (enable a feature for a single pilot merchant before rolling it out to all). The unique constraint on `(key, scope_type, scope_id)` prevents duplicate records.

**Fail-open resolution:** If no flag record exists for a given key, `is_enabled()` returns `True`. This preserves backward compatibility: features that have never been explicitly flagged continue to behave as before, and deleting a flag record re-enables the feature without any code change.

**Resolution priority:** scoped flag (matching key + scope) → global flag (matching key only) → default (`True`). This mirrors the layered override model used by most feature-flag systems and makes the lookup deterministic.

**Admin-only API:** Flags are a platform configuration concern. Only admins may create, update, or delete them. Read access is also admin-only to avoid leaking information about unreleased features.

**Standard module structure:** The feature flags module follows the exact same layered architecture as every other ClickNBack module. This keeps the codebase uniform: no new patterns to learn, no special-cased wiring. Consuming modules interact with `feature_flags` through the standard cross-module client pattern, exactly as they would with `users`, `merchants`, or any other domain.

**No caching in v1:** Flag resolution always hits the database. At current scale this is negligible — flags are checked at job dispatch boundaries and event handler entry points, not per-request in hot paths. A TTL cache can be layered on top of `FeatureFlagService` if profiling reveals a problem.

## Module: `app/feature_flags/`

```text
app/feature_flags/
  __init__.py
  models.py          ← FeatureFlag ORM model (feature_flags table)
  schemas.py         ← FeatureFlagCreate, FeatureFlagOut, FeatureFlagListOut, FeatureFlagEvaluateOut
  repositories.py    ← FeatureFlagRepositoryABC + FeatureFlagRepository
  services.py        ← FeatureFlagService (upsert, delete, list, is_enabled)
  policies.py        ← validate_scope_id_required (scope_type ≠ global → scope_id must be set)
  exceptions.py      ← FeatureFlagNotFound, FeatureFlagScopeIdRequired
  errors.py          ← ErrorCode: FEATURE_FLAG_NOT_FOUND, FEATURE_FLAG_SCOPE_ID_REQUIRED
  composition.py     ← get_feature_flag_service() FastAPI Depends factory
  api.py             ← GET /feature-flags, PUT /feature-flags/{key}, DELETE /feature-flags/{key},
                       GET /feature-flags/{key}/evaluate
```

## Integration Points

Any domain module that needs to gate behaviour behind a flag treats `feature_flags` as a foreign module and applies the standard cross-module client pattern (see `build-feature.prompt.md` Step 4a): add a `clients/feature_flags.py` file to the **consuming module's own** `clients/` package. This is the same pattern `app/purchases/` already uses for `clients/users.py`, `clients/merchants.py`, and `clients/offers.py`.

The file contains a `FeatureFlagsClientABC` with an `is_enabled()` method and an in-process concrete `FeatureFlagsClient` that calls `FeatureFlagService` directly via the shared database. Wire the concrete class in the consuming module's `composition.py`. If `feature_flags` is promoted to a standalone microservice, only that concrete class is replaced with one that calls `GET /api/v1/feature-flags/{key}/evaluate` — no other code in the consuming module changes.

Common integration points:

- **Background job dispatchers:** check the flag once per scheduler tick before querying for pending items.
- **Event handlers:** check the flag before the handler body performs gated work.
- **API route handlers:** check the flag before delegating to the service when a feature should be conditionally available.

```python
# app/purchases/clients/feature_flags.py
from abc import ABC, abstractmethod

class FeatureFlagsClientABC(ABC):
    @abstractmethod
    async def is_enabled(
        self, key: str, scope_type: str = "global", scope_id: str | None = None
    ) -> bool: ...

class FeatureFlagsClient(FeatureFlagsClientABC):
    """In-process implementation — calls FeatureFlagService via the shared DB.

    Replace with an HTTP client calling GET /api/v1/feature-flags/{key}/evaluate
    if feature_flags is extracted to a microservice.
    """
    def __init__(self, service: FeatureFlagService) -> None:
        self._service = service

    async def is_enabled(self, key: str, scope_type: str = "global", scope_id: str | None = None) -> bool:
        return await self._service.is_enabled(key, scope_type=scope_type, scope_id=scope_id)
```

```python
# app/purchases/jobs/verify_purchases/dispatcher.py
class PurchaseConfirmationDispatcher:
    def __init__(
        self,
        repository: PurchaseRepositoryABC,
        feature_flags: FeatureFlagsClientABC,
    ) -> None:
        self._repository = repository
        self._feature_flags = feature_flags

    async def dispatch(self, db: AsyncSession) -> None:
        if not await self._feature_flags.is_enabled("purchase_confirmation_job"):
            logger.info("purchase_confirmation_job disabled — skipping tick")
            return
        # ... normal dispatch logic
```

## Data Model

```sql
CREATE TABLE feature_flags (
    id          TEXT PRIMARY KEY,
    key         TEXT NOT NULL,
    enabled     BOOLEAN NOT NULL,
    scope_type  TEXT NOT NULL DEFAULT 'global',  -- 'global' | 'merchant' | 'user'
    scope_id    TEXT,                             -- NULL for global flags
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL,
    UNIQUE (key, scope_type, COALESCE(scope_id, ''))
);
```

## Consequences

**Benefits:**

- Runtime control over features without redeployment or process restart.
- Scoped flags enable targeted demo, testing, and progressive rollout without code changes.
- Standard module structure — no new patterns, consistent with the rest of the codebase.
- Durable state: flags survive deployments and restarts.
- Clear upgrade path: add TTL caching, percentage rollouts, or audit trail following existing patterns.

**Accepted trade-offs:**

- Every `is_enabled()` call hits the database. Acceptable at current scale; cache if needed.
- No audit trail on flag changes in v1. Admin actions are visible in application logs but not persisted to `audit_logs`. A `AuditTrail.record()` call can be added to `FeatureFlagService` when compliance requires it (see ADR-015).
- No built-in percentage rollout in v1. The `scope_type` field is designed to accommodate this extension without a schema migration (add `percentage_user` as a new scope type and a `rollout_percentage` column).

## Alternatives Considered

### Environment variable flags

Simple and zero overhead, but requires a process restart to toggle, which defeats the purpose of runtime control for testing/demo workflows. Also cannot support scoped flags or dynamic updates from a CD pipeline without restarts.

### In-memory flag store with API

Easy to implement but flag state is lost on every restart or deployment. This is acceptable for a short-lived local test but unusable in the shared demo environment where the database resets nightly and the process may be restarted at any time.

### Third-party feature flag service (LaunchDarkly, Flagsmith, etc.)

Excellent for large-scale production systems but adds an external dependency, operational overhead, and a billing relationship that is disproportionate to the current system's needs. The lightweight DB-backed approach can be promoted to a third-party service later with a one-line binding change in the composition root.

## References

- [ADR-014: In-Process Message Broker and Task Scheduler for MVP](014-in-process-broker-and-scheduler.md)
- [ADR-015: Persistent Audit Trail for Critical Operations](015-persistent-audit-trail.md)
- [ADR-016: Background Job Architecture Pattern](016-background-job-architecture-pattern.md)
- [FF-01: Set Feature Flag](../../specs/functional/feature-flags/FF-01-set-feature-flag.md)
- [FF-02: Delete Feature Flag](../../specs/functional/feature-flags/FF-02-delete-feature-flag.md)
- [FF-03: List Feature Flags](../../specs/functional/feature-flags/FF-03-list-feature-flags.md)
- [FF-04: Evaluate Feature Flag](../../specs/functional/feature-flags/FF-04-evaluate-feature-flag.md)
