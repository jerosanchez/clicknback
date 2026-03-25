# CONTRIBUTING

## Getting Started

### Prerequisites (Ubuntu 24.04)

This project requires Python 3.13+, Docker, and Node.js for markdown linting. Follow the steps below to set up your development environment on Ubuntu 24.04.

#### 1. Install System Dependencies

```shell
# Update package manager
sudo apt update
sudo apt install -y software-properties-common

# Add the deadsnakes PPA — Ubuntu 24.04 ships with Python 3.12,
# so Python 3.13 must be installed from this PPA
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Install Python and virtual environment tools
sudo apt install -y python3.13 python3.13-venv python3.13-dev
# Install Docker (if not already installed)
sudo apt install -y docker.io docker-compose-v2

# Add your user to the docker group (avoid using sudo with docker)
sudo usermod -aG docker $USER
# Log out and back in, or run: newgrp docker

# Install Node.js 21 (required for markdownlint-cli >=0.48)
curl -fsSL https://deb.nodesource.com/setup_21.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g markdownlint-cli
```

#### 2. Clone the Repository

```shell
cd /path/to/projects
git clone https://github.com/yourusername/clicknback.git
cd clicknback
```

#### 3. Set Up Python Environment

The project uses a Makefile for common tasks. The `make install` command will create and activate a virtual environment and install all dependencies:

```shell
make install
```

This will:

- Create a `.venv` virtual environment
- Install production dependencies
- Install development dependencies (pytest, linting tools, etc.)

#### 4. Start the Database

This project uses PostgreSQL in Docker. Start it with:

```shell
make up
```

This will:

- Create a Docker network (`clicknback-nw`)
- Start PostgreSQL container with the database initialized
- Run pending migrations automatically

#### 5. Install Pre-commit Hooks

This project uses pre-commit to enforce quality gates locally before every commit. Run this once after cloning:

```shell
source .venv/bin/activate
pre-commit install
```

After this, Git will automatically run all hooks before every `git commit`. To run all hooks manually at any time:

```shell
pre-commit run --all-files
```

#### 6. Verify Your Setup

```shell
# Run the unit test suite
make test

# Run integration tests (requires TEST_DATABASE_URL)
# TEST_DATABASE_URL set automatically to match make up container
make test-integration

# Start the development server (in another terminal)
# First, activate the venv again if needed
source .venv/bin/activate
make dev
```

The API will be available at `http://localhost:8000` with interactive docs at
`http://localhost:8000/docs`.

### Common Development Tasks

```shell
# Install dependencies and set up venv
make install     # Create .venv and install all dependencies

# Start/stop the application and database
make up          # Start containers (DB + migrations + app)
make down        # Stop containers and remove network

# Run tests
make test        # Run unit tests with coverage (pytest)
make test-integration   # Run integration tests against real PostgreSQL (requires TEST_DATABASE_URL)
make test-e2e    # Run end-to-end tests via Docker Compose (requires docker-compose)
make coverage    # Run all tests and print emoji-graded coverage report

# Code quality
make lint        # Run all linters (markdown, flake8, isort, black)
make security    # Run Bandit security scan on app/ (medium/high only)

# Start development server (hot-reload, no Docker)
make dev         # Start FastAPI server with auto-reload

# Reset database (useful during development)
make db-reset    # Rollback migrations, apply fresh migrations, seed data

# Clean up artifacts
make clean       # Remove .venv, __pycache__, coverage reports, etc.
```

## Testing Strategy

ClickNBack follows a **three-layer testing pyramid**:

| Layer | Scope | Run with | Purpose |
| --- | --- | --- | --- |
| **Unit Tests** | Business logic, services, APIs — all dependencies mocked | `make test` | Fast feedback; one test per behavior; ~6,000+ tests total |
| **Integration Tests** | HTTP endpoints exercised against real PostgreSQL; no mocks | `make test-integration` | Verify each feature/endpoint works end-to-end with the database |
| **E2E Tests** | Full system flows via Docker Compose | `make test-e2e` | Multi-step user journeys (coming soon) |

**Coverage gate:** `make coverage` enforces an **85% hard gate** on unit tests. This gate runs the unit test suite and verifies coverage meets the threshold before allowing commits in CI. Integration and E2E tests do not count toward the coverage gate — they complement unit tests by verifying real-world interactions.

**When to write each layer:**

- **Unit test:** Whenever you write a service method, API endpoint, policy, or utility function. Mock all external dependencies (DB, other services, policies). Test both success and failure paths.
- **Integration test:** One per endpoint. Exercise the HTTP route through to the database with real objects. Verify status codes, response fields, and key error scenarios. Edge cases belong in unit tests.
- **E2E test:** Reserved for multi-step user flows that span multiple domains (e.g., register → make purchase → withdraw payout). Coming soon.

See [docs/guidelines/unit-testing.md](docs/guidelines/unit-testing.md) for the full testing guidelines, canonical examples, and checklist for every test layer.

## Navigating the Code

The application lives under `app/`. Every domain is a self-contained module (e.g., `app/users/`, `app/merchants/`) that follows the same layered structure: `api` (HTTP routing), `services` (business logic), `policies` (pure business rules), `repositories` (data access), `models`, `schemas`, `exceptions`, `errors`, and `composition` (dependency wiring).

Cross-cutting infrastructure (config, DB session factory, JWT, logging, audit trail, message brokers, schedulers, error builders) lives in `app/core/`. Domain-specific background jobs live under their domain (e.g., `app/purchases/jobs/verify_purchases/`) following the Fan-Out Dispatcher + Per-Item Runner pattern; see `docs/guidelines/background-jobs.md` and ADR-016.

The feature flag system lives in `app/feature_flags/` and follows the same layered module structure as all other domain modules. To query flag state from another module, treat `feature_flags` as a foreign module and apply the standard client pattern (the same one used for any cross-module dependency): add a `clients/feature_flags.py` file to the **consuming module's own** `clients/` package, with an ABC exposing `is_enabled()` and an in-process concrete implementation calling `FeatureFlagService` directly. If `feature_flags` is later promoted to a microservice, only that concrete class is replaced with one calling the HTTP evaluate endpoint. See [ADR-018](docs/design/adr/018-feature-flag-system.md) for resolution semantics and the evaluate endpoint design.

**All new modules must use the async database stack** (ADR 010, `docs/design/adr/010-async-database-layer.md`): repositories accept `AsyncSession`, service methods are `async def`, and route handlers use `async def` with `Depends(get_async_db)`. Existing modules (`users`, `merchants`, `offers`, `auth`) use the synchronous session and are migrated incrementally.

Tests mirror the module structure under `tests/`. Async service tests use `pytest-asyncio` (`@pytest.mark.asyncio`, `AsyncMock(spec=AsyncSession)`). The `conftest.py` at the root provides factory fixtures used across all test suites.

For a detailed walkthrough of each layer, its responsibilities, and the architectural rationale, see [docs/guidelines/feature-architecture.md](docs/guidelines/feature-architecture.md). For guidelines on how to organize and split files as a module grows, see [docs/guidelines/code-organization.md](docs/guidelines/code-organization.md).

## Architecture & Design Decisions

This project follows a modular monolith architecture with clear separation of concerns. Key architectural decisions are documented as Architecture Decision Records (ADRs) in the [`docs/adr/`](docs/adr/) directory.

**We recommend reviewing relevant ADRs before proposing architectural changes.** They provide important context and rationale behind design choices.

Follow a pragmatic approach:

- For architectural decisions not yet documented in ADRs, favor solutions that are **practical** for current needs while leaving room for future scalability
- Prioritize **simplicity and maintainability** over over-engineering
- Keep options open for growth as the project evolves

## Quality Enforcement

Always run the full gate sequence before pushing or opening a pull request:

```shell
make lint       # Check code style, formatting, and docs
make test       # Run all tests with coverage
make coverage   # Verify coverage meets the 85% threshold
make security   # Bandit scan — must exit 0 before pushing
```

If you have completed the one-time `pre-commit install` step (see Initial Setup above), Git runs these checks automatically before every commit.

Refer to `docs/guidelines/quality-gates.md` for the full gate sequence and coverage grading scale.

## Production Deployment

The full production architecture, deployment pipeline, secrets strategy, rollback procedure, and operational runbooks are documented in [docs/design/deployment-plan.md](docs/design/deployment-plan.md).

## Database Migrations

This project uses Alembic for database schema migrations.

### Creating Migrations

1. Make changes to models in `app/<domain>>/models.py`
2. Generate migration:

```shell
source .venv/bin/activate
alembic revision --autogenerate -m "Add new field"
```

<!-- markdownlint-disable MD029 -->
3. Review the generated migration in `alembic/versions/`
4. Apply the migration:

    ```shell
    alembic upgrade head
    ```
<!-- markdownlint-enable MD029 -->

### Working with Migrations

```shell
# View migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Downgrade to base
alembic downgrade base
```

## Troubleshooting

### Virtual Environment Issues

```shell
# If you see errors about ensurepip or venv creation failing,
# make sure python3.13-venv is installed (Ubuntu 24.04 ships Python 3.12
# as the default `python3`, so `python3.13-venv` must be installed explicitly):
sudo apt install python3.13-venv

# If you see "command not found: python3.13", install it via the deadsnakes PPA:
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev

# If venv is broken or you want a clean install
make clean
make install
```

### Docker Issues

```shell
# If containers won't start
docker system prune  # Remove unused images/volumes

# If you can't connect to Docker
# Make sure you've added your user to the docker group:
sudo usermod -aG docker $USER
newgrp docker

# Check if Docker is running
sudo systemctl status docker
```

### Database Connection Issues

```shell
# Check if PostgreSQL is running
docker ps | grep clicknback

# View logs
docker logs clicknback-clicknback-db-1

# Reset the database
make db-reset
```

### Port Already in Use

If port 8000 (FastAPI) or 5432 (PostgreSQL) is already in use:

```shell
# Find what's using the port
sudo lsof -i :8000

# Kill the process (if needed)
kill -9 <PID>

# Or use a different port for FastAPI
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

## Questions or Issues?

- Check the documentation in [`docs/`](docs/)
- Review relevant ADRs in [`docs/adr/`](docs/design/adr/)
- Check existing GitHub issues
- Open an issue with details about the problem and your environment
