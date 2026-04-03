---
name: quality-gates
type: rule
description: Testing pyramid, coverage gates, lint/security standards, and make commands
---

# QUALITY-GATES

Every change must pass all four quality gates. Failures block deployment and must be fixed before handoff.

## The Four Gates

### 1. Linting (`make lint`)

Runs code formatting and style checks:

- **markdownlint**: Markdown documentation
- **flake8**: Python style (PEP 8)
- **isort --check-only**: Import order (stdlib → third-party → local)
- **black --check**: Code formatting

**Exit code must be 0.** All issues must be fixed autonomously before handoff.

### 2. Unit Tests (`make test`)

Runs unit test suite with coverage:

- **Test directory**: `tests/unit/`
- **Coverage report**: Generates `htmlcov/`, `coverage.xml`, terminal output
- **Coverage gate**: Hard minimum 85%; aspirational target 80%
- **Exit code must be 0.** No skipped tests, no xfail markers without documented reason.

### 3. Security (`make security`)

Runs Bandit static analysis:

- **Scope**: `app/` directory
- **Severity**: Medium/High only
- **Suppressions**: No `# nosec` comments without documented inline reason
- **Exit code must be 0.**

### 4. Integration Tests (`make test-integration`)

Runs integration test suite against real PostgreSQL:

- **Test directory**: `tests/integration/`
- **Database**: Real PostgreSQL instance; isolated transactions (rolled back after each test)
- **Coverage**: Happy path and critical failure modes
- **Requirement**: `TEST_DATABASE_URL` environment variable must be set
- **Exit code must be 0.** Run only after unit tests pass.

## Testing Pyramid

| Layer | Count | Speed | Dependencies | When to Run |
|-------|-------|-------|--------------|------------|
| **Unit** | Many | <100ms each | All mocked | Every change (`make test`) |
| **Integration** | Some | ~1-5s each | Real DB | Before push (`make test-integration`) |
| **E2E** | Few | ~5-30s each | Full Docker stack | Pre-deployment (`make test-e2e`) |

### What to Test

- ✅ Service business logic, API response/error mapping, policies, validators, utilities
- ✅ Collaborator integration (verify dependencies called correctly, return values transformed correctly)
- ✅ Critical failure modes (auth failures, business rule violations, concurrency issues)
- ❌ Don't test: Thin repositories, framework internals, trivial getters

## Coverage Standards

- **Hard gate**: 85% (CI fails below)
- **Aspirational target**: 80%
- **Applies to**: Unit tests only (`tests/unit/`)
- **Excludes**: Integration tests, E2E tests

## Import Order (Enforced by isort)

```python
# 1. Standard library
import sys
from datetime import datetime
from typing import Any

# 2. Third-party
from sqlalchemy import select
from pydantic import BaseModel

# 3. Local — Core/Infrastructure first
from app.core.logging import logger
from app.core.database import AsyncSession

# 4. Local — Module under test
from app.purchases.services import PurchaseService
from app.purchases.models import Purchase
```

## Code Quality

- ❌ **Never**: `@pytest.mark.skip`, `@pytest.mark.xfail`, or stub implementations to make tests pass
- ❌ **Never**: `# noqa` suppressions without a documented inline reason
- ✅ **Always**: Run all four gates after every change

## Running Quality Gates

```bash
# All four gates
make lint && make test && make coverage && make security

# Individual gates
make lint          # Markdown, flake8, isort, black
make test          # Unit tests with coverage
make security      # Bandit security analysis
make test-integration  # Integration tests (requires TEST_DATABASE_URL)
make test-e2e      # E2E tests (requires Docker Compose)
```

---
