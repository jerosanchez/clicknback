# ADR 005: Use Containerized PostgreSQL Database

## Status

Accepted

## Context

ClickNBack requires a PostgreSQL database available in every execution context: local development, the CI pipeline, and the test suite. The question is: how should that database be provisioned and managed so that all environments use an identical configuration with minimal onboarding friction?

### Option 1: Native PostgreSQL Installation per Developer Machine

Each developer installs PostgreSQL directly on their host operating system.

```bash
# macOS
brew install postgresql@16
brew services start postgresql@16
createdb clicknback

# Ubuntu
sudo apt install postgresql-16
sudo systemctl start postgresql
sudo -u postgres createdb clicknback
```

- ✅ Best raw I/O performance (no containerisation overhead)
- ✅ No Docker dependency
- ❌ PostgreSQL version is tied to the developer's OS package manager — `brew install postgresql` installs whatever version Homebrew pins today, which may differ from the CI image or production server
- ❌ Onboarding requires several OS-specific steps; a new developer on Windows follows an entirely different path
- ❌ Residual data, roles, and extensions can persist between test runs unless the developer manually resets the database
- ❌ Parallel test runs on the same host share the same PostgreSQL process; port conflicts and state leakage are common

### Option 2: Shared Cloud Database (e.g., AWS RDS Dev Instance)

A single development database instance runs in the cloud, shared by all developers.

```python
# .env
DATABASE_URL=postgresql://dev_user:secret@dev-rds.us-east-1.rds.amazonaws.com:5432/clicknback_dev
```

- ✅ Zero installation required; connect with a URL
- ✅ Matches production infrastructure
- ❌ Requires network access — offline development is blocked
- ❌ Developers share state; one developer's incomplete migration can break another's workflow
- ❌ Cloud cost for a permanent dev instance
- ❌ CI pipelines need credentials management; secrets rotation affects all developers simultaneously
- ❌ Test isolation is difficult — concurrent test runs from different developers collide

### Option 3: Containerized PostgreSQL via Docker Compose

A `docker-compose.yml` file declares the exact PostgreSQL version, credentials, and port. Each developer runs `docker compose up -d` to start the database.

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: clicknback
      POSTGRES_PASSWORD: clicknback
      POSTGRES_DB: clicknback
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U clicknback"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

```bash
# Start database
docker compose up -d

# Apply migrations
alembic upgrade head

# Reset everything (including data)
docker compose down -v && docker compose up -d
```

- ✅ Identical PostgreSQL version for every developer and the CI pipeline — the image tag is the version pin
- ✅ Isolated from the host OS: no version conflicts, no leftover roles or extensions
- ✅ One-command setup: `docker compose up -d` — reproducible regardless of OS
- ✅ State can be completely reset with `docker compose down -v`
- ✅ CI uses the same `docker-compose.yml` — what passes locally passes in CI
- ⚠️ Requires Docker Desktop (macOS/Windows) or Docker Engine (Linux) to be installed
- ⚠️ Volume I/O is slightly slower than native on macOS due to file-system translation in Docker Desktop

## Decision

Use **containerised PostgreSQL via Docker Compose** for all local development and CI environments.

1. The `docker-compose.yml` at the repository root defines a `postgres:16-alpine` service with fixed credentials (`clicknback` / `clicknback`) and a named volume for data persistence across container restarts.
2. The application's `DATABASE_URL` points to `localhost:5432`; environment-specific overrides (production RDS URL) are provided through the environment variable layer defined in `app/core/config.py` (see ADR 000).
3. Alembic manages all schema changes — `alembic upgrade head` is run after starting the container and after pulling changes that include migrations.
4. The `Makefile` exposes convenience targets (`make db-start`, `make db-reset`, `make migrate`) so developers do not need to remember the underlying commands.
5. The CI pipeline starts the `db` service from the same `docker-compose.yml` before running the test suite, ensuring the test database matches the local developer's database exactly.

## Consequences

- ✅ Every developer uses PostgreSQL 16-alpine regardless of their host OS — "works on my machine" bugs caused by version differences are eliminated.
- ✅ Onboarding a new developer requires only `docker compose up -d && alembic upgrade head` — no OS-specific database installation steps.
- ✅ The database can be fully reset in seconds (`docker compose down -v && docker compose up -d`), enabling clean-slate test runs and migration testing.
- ✅ CI uses the same container image and credentials as local development; environment divergence between local and CI is eliminated.
- ✅ Named Docker volumes persist data across container restarts, so developers retain their seed data between sessions without committing it.
- ⚠️ Docker must be installed and running before starting the database; developers on locked-down corporate machines may need an IT exception.
- ⚠️ Docker Desktop on macOS introduces a small I/O overhead on volume-mounted paths; for development workloads this is not measurable, but long-running data-intensive operations (e.g., bulk imports) may be slower than a native install.
- ⚠️ For production, a managed PostgreSQL service (e.g., AWS RDS, Supabase) should replace the Docker container — containerised databases in production require careful volume management and backup strategies that managed services provide out of the box.

## Alternatives Considered

### Native PostgreSQL Installation

- **Pros:** Maximum I/O performance; no additional tooling dependency.
- **Cons:** PostgreSQL version is determined by the host OS package manager, leading to version drift across developer machines and CI. Onboarding steps differ per OS. State accumulates on the host and must be manually managed. Parallel test runs from different projects on the same host can collide on port 5432.
- **Rejected:** The version consistency and onboarding simplicity of Docker outweigh the marginal performance advantage of a native install for development and testing workloads.

### Shared Cloud Dev Database

- **Pros:** No local installation; identical to production infrastructure.
- **Cons:** Requires network connectivity; developers share mutable state; concurrent migrations from different branches can break other developers' environments; requires secrets management from day one; cloud cost for a persistent dev instance.
- **Rejected:** Shared mutable state makes local development fragile. Offline work is blocked. The isolation guarantee of a per-developer local database is more valuable than the infrastructure parity argument at this stage.

### SQLite for Local Development

- **Pros:** Zero installation; single file; trivially reset.
- **Cons:** SQLite and PostgreSQL differ in type handling, default behaviour, and supported features (e.g., `RETURNING`, `UPSERT`, JSON columns, advisory locks). Tests passing on SQLite can fail on PostgreSQL in CI or production — a class of environment-specific bugs that Docker eliminates entirely.
- **Rejected:** ClickNBack uses PostgreSQL-specific features (UUID primary keys, `RETURNING` clauses, JSON fields). Running a different database engine in development would invalidate the correctness of the test suite.

## Rationale

The primary goal is **environment parity**: the database engine, version, and configuration used by a developer writing code should be identical to the one used by CI running tests and (as close as possible) to the one used in production. Docker Compose achieves this by making the database a declared, versioned artifact in the repository — the same way application code is versioned — rather than an implicit system-level dependency that varies per machine.

The operational simplicity argument is secondary but significant: a single command starts the database, a single command resets it, and the same declaration drives CI. This removes an entire category of setup and debugging conversations from the development workflow.
