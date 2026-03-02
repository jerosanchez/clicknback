# Deployment Plan

## 1. Overview

Strategic deployment architecture for ClickNBack, showcasing a pragmatic CI/CD lifecycle with production readiness for a demo system. The deployment strategy uses Docker containerization for consistency, GitHub Actions for CI/CD automation, and semantic versioning for controlled releases.

---

## 2. Target Architecture

### 2.1 Infrastructure

- **Compute:** Single VPS (DigitalOcean) running Ubuntu
- **Containerization:** Docker + Docker Compose for consistency across all environments
- **Image Registry:** `ghcr.io` (GitHub Container Registry) — free, gated by `GITHUB_TOKEN`, images private by default
- **Reverse Proxy:** Nginx on the VPS — terminates TLS (via Certbot), routes `clicknback.com` to the app container, hosts the API kill switch
- **Database:** PostgreSQL (Docker Compose locally; containerized on the VPS)
- **CI/CD:** GitHub Actions — CI on pull requests, CD on every merge to `main`

### 2.2 Rationale

The modular monolith (ADR 001) supports single-instance deployment today while allowing domain extraction to microservices later. Docker ensures consistency between local development and production, eliminating "works on my machine" surprises. GitHub Actions provides automated quality gates before production deployments.

---

## 3. CI/CD Lifecycle

### 3.1 Local Development

**Quality Gates:** Enforced automatically on every `git commit` via pre-commit hooks, and again in CI on every pull request.

**Pre-commit hooks** (`.pre-commit-config.yaml`, activated once with `pre-commit install`):

- Trailing whitespace and end-of-file fixers
- YAML syntax check
- Black (code formatting)
- isort (import ordering)
- flake8 (PEP 8 + undefined names)
- Bandit (security scan — medium and high severity)

If any hook fails, the commit is aborted and the developer sees which check failed. The same gates run in CI, so failures are caught locally before they reach the remote.

**Additional gates run manually before opening a PR:**

- `make lint` — markdownlint, flake8, isort, black (read-only check)
- `make test` — full pytest suite with coverage
- `make coverage` — generates `coverage.xml` and prints an emoji-graded result; exits non-zero below **70%** (hard gate); **80%** is the aspirational target
- `make security` — Bandit scan of `app/` at medium/high severity
- Manual peer review

**Rationale:** Catch defects and style issues early. Automation enforces the gates before code ever leaves the developer's machine, eliminating the feedback-loop delay of waiting for CI.

### 3.2 Production Deployment

**Trigger:** Every merge to `main` after all CI gates pass (`lint` → `test` → `coverage` → `security`).

**Pre-deployment Checks:**

- All CI jobs green on the `main` branch
- Code review approval on the PR
- Database schema compatibility verified before merge

**Deployment Pipeline (GitHub Actions `cd.yml`):**

1. **`build-push` job** — logs in to `ghcr.io` with `GITHUB_TOKEN`, builds the Docker image, and pushes two tags:
   - `ghcr.io/jerosanchez/clicknback:latest` — convenience alias for Compose
   - `ghcr.io/jerosanchez/clicknback:sha-<commit>` — exact traceability per deploy
2. **`deploy` job** (needs `build-push`) — SSHes into the VPS and runs:

   ```bash
   docker pull ghcr.io/jerosanchez/clicknback:latest
   docker compose -f /home/clicknback/app/docker-compose.yml up -d --no-build --remove-orphans
   ```

   Docker Compose starts the `migrate` container first (exits 0 on success), then starts `clicknback-app` once migrations complete and the DB is healthy.
3. **Health verification** — `/health/ready` confirms the app is up and the DB is reachable before the pipeline is marked green.

**Rollback Path:** Redeploy a previous `sha-<commit>` image — see [Section 9](#9-rollback-procedure) for the full runbook.

---

## 4. Deployment Strategy

### 4.1 Key Principles

**Environment Consistency:** Local development and production use identical containerized stacks (Python + PostgreSQL). This eliminates environment-specific bugs and reduces deployment surprises.

**Infrastructure as Code:** Deployment configuration (Docker Compose) and CI/CD pipelines (GitHub Actions) are version-controlled alongside application code.

**Schema Evolution:** Database migrations (via Alembic) are versioned and applied deterministically. Rollback capability is preserved through migration history.

**Secret Management:** Application secrets live in a static `.env` file on the VPS, placed once by an operator with `chmod 600`. The CD pipeline never reads or writes this file. See [Section 8](#8-production-secrets-strategy) for the full strategy.

**Single Deployable Unit:** The entire application (FastAPI service + PostgreSQL database) is containerized, enabling reproducible deployments across machines and environments.

---

## 5. Strategic Goals

**Code Quality:** Automated testing and linting gates ensure only high-quality code reaches production. Minimum 70% test coverage.

**Reproducibility:** Same Docker image and configuration work identically across developer computers and production VPS.

**Fast Iteration:** PR-to-production cycle is fast (hours, not weeks) but deliberate—the PR review and CI gate sequence prevents accidental deployments without adding manual release steps.

**Operational Simplicity:** Single VPS and containerized stack minimize operational overhead while demonstrating production discipline.

**Demandable Recovery:** Versioned releases enable quick rollback to previous production state if needed.

---

## 6. Known Constraints & Trade-offs

### 6.1 Single VPS Model

✅ **Pros:**

- Minimal operational overhead
- Clear deployment verification
- Cost-effective for demo system
- Suitable for showcasing architectural patterns

⚠️ **Cons:**

- No automatic scaling or failover
- Single point of failure
- Monitoring and alerting still necessary

**Recommendation:** For a showcase project, single VPS is appropriate. Document the path to multi-instance with load balancing for production scenarios.

### 6.2 Database Strategy

**Local Development:** Docker Compose PostgreSQL runs locally alongside the application container. Schema managed through Alembic migrations.

**Production:** PostgreSQL on VPS (containerized). Automated backups outside the VPS and monitoring recommended for real-world scenarios. Migrations applied automatically during deployment.

### 6.3 Observability & Monitoring

For a demo system, basic approach: application logs to stdout (captured by container runtime), health check endpoints for deployment verification. For production scale, add centralized logging and metric collection.

---

## 7. Implementation Approach

**Implemented:**

- **Pre-commit hooks** — lint, format, and security gates enforced locally before every commit
- **GitHub Actions CI** — `lint` → `test` → `coverage` (70% hard gate) → `security` (Bandit) on every PR and push to `main`
- **GitHub Actions CD** — on every merge to `main`: build image, push to `ghcr.io` with `sha-<commit>` and `latest` tags, deploy to VPS via SSH
- **Two-stage Dockerfile** — minimal runtime image (no build tools, no test deps), non-root user
- **Migration container pattern** — `migrate` service runs `alembic upgrade head` before the app starts; configured `restart: "no"` so failures are not silently retried
- **Health probes** — `GET /health/live` (liveness, no I/O) and `GET /health/ready` (readiness, DB round-trip) for container orchestration and deployment verification
- **Nginx reverse proxy + Certbot TLS** — routes `https://clicknback.com` to the app container; API kill switch available via a file flag
- **Dependabot** — automated weekly dependency update PRs for Python packages and GitHub Actions; security advisories trigger immediate PRs
- **Nightly reseed** — database backed up at 03:00 UTC, wiped and reseeded at 03:05 UTC for a clean demo state each morning

**Future Enhancements (If Scaling):**

- Distributed tracing for request analysis
- Centralized logging across instances
- Automated rollback on health check failure
- Multi-instance load balancing

---

## 8. Production Secrets Strategy

Production secrets (database credentials, OAuth keys, etc.) are managed as a static file on the VPS — never injected through CI environment variables.

### 8.1 Placement

The file lives at `/home/clicknback/app/.env` on the VPS, placed once by an operator:

```bash
# Lock permissions so only the owner can read it
chmod 600 /home/clicknback/app/.env
chown clicknback:clicknback /home/clicknback/app/.env
```

The file is never committed to the repository. `.env` is listed in `.gitignore` and must stay there.

### 8.2 CD Separation of Concerns

The CD pipeline **never** reads, writes, or references the `.env` file. Its only VPS-side actions are:

1. Pull the new image from `ghcr.io`.
1. Run `docker compose up -d --no-build --remove-orphans`.

Docker Compose reads `.env` from `/home/clicknback/app/` at startup — no CI involvement. The image build and push (`build-push` job) happen entirely within GitHub Actions using `GITHUB_TOKEN`; no application secrets are involved.

### 8.3 Why Not CI Secrets Injection

Injecting production secrets through CI environment variables (e.g., `docker compose up -e DB_PASSWORD=${{ secrets.DB_PASSWORD }}`) is an anti-pattern because:

- Variables can appear in CI logs if the command fails verbosely.
- CI secrets rotate independently of the VPS; keeping them in sync adds operational risk.
- A static file on the VPS is auditable via SSH access logs; CI variable injection is not.

### 8.4 GitHub Secrets Scope

GitHub Secrets are reserved for pipeline credentials only:

| Secret | Purpose |
| --- | --- |
| `VPS_HOST` | SSH target for the deploy job |
| `VPS_USER` | SSH username for the deploy job |
| `VPS_SSH_KEY` | Ed25519 deploy key private half |

Application secrets (`DATABASE_URL`, `OAUTH_HASH_KEY`, etc.) never enter GitHub.

---

## 9. Rollback Procedure

Every CD deploy pushes two image tags to `ghcr.io`: `latest` (convenience alias) and `sha-<commit>` (exact traceability). To roll back to any previous version:

```bash
# On the VPS, as the clicknback user
cd /home/clicknback/app
docker pull ghcr.io/jerosanchez/clicknback:sha-<previous-commit>
APP_IMAGE=ghcr.io/jerosanchez/clicknback:sha-<previous-commit> \
  docker compose -f /home/clicknback/app/docker-compose.yml up -d --no-build --remove-orphans
```

**Finding the previous SHA:** check the GitHub Actions run history for the last successful `build-push` job, or run `docker images | grep clicknback` on the VPS to list locally cached images.

**If a schema downgrade is also required**, run the Alembic downgrade before restarting the app:

```bash
docker compose -f /home/clicknback/app/docker-compose.yml \
  run --rm migrate alembic downgrade -1
```

Then re-run the `up` command above to start the app against the downgraded schema.

---

## 10. Production Log Access

Application logs are written to stdout and captured by Docker. To tail them live from any machine with SSH access to the VPS:

```bash
ssh clicknback@<VPS_HOST> \
  "docker compose -f /home/clicknback/app/docker-compose.yml logs -f clicknback-app"
```

No log agent or external service is required for a demo system. Logs include all FastAPI request traces and application-level events emitted by `app/core/logging.py`.
