# Deployment Plan

## 1. Overview

Strategic deployment architecture for ClickNBack, showcasing a pragmatic CI/CD lifecycle with production readiness for a demo system. The deployment strategy uses Docker containerization for consistency, GitHub Actions for CI/CD automation, and semantic versioning for controlled releases.

---

## 2. Target Architecture

### 2.1 Infrastructure

- **Compute:** Single VPS (DigitalOcean, Linode, AWS EC2) or Heroku for simplicity
- **Containerization:** Docker for consistency across all environments
- **Database:** PostgreSQL (Docker Compose locally; managed service or containerized in production)
- **CI/CD:** GitHub Actions (native to GitHub, minimal setup cost)

### 2.2 Rationale

The modular monolith (ADR 001) supports single-instance deployment today while allowing domain extraction to microservices later. Docker ensures consistency between local development and production, eliminating "works on my machine" surprises. GitHub Actions provides automated quality gates before production deployments.

---

## 3. CI/CD Lifecycle

### 3.1 Local Development

**Quality Gates:** Before code merges to `main`

- Lint and format checks (flake8, black, isort, markdownlint)
- Unit and integration tests with automated database containers
- Code coverage enforcement (minimum 80%)
- Manual peer review

**Rationale:** Catch defects and style issues early. Maintain code quality through automation rather than post-hoc review.

### 3.2 Production Deployment

**Trigger:** Explicit release via semantic version tag (e.g., `v0.1.0`)

**Pre-deployment Checks:**

- Merge to `main` branch with passing CI gates
- Code review approval
- Database schema compatibility verified

**Deployment Strategy:**

- Build containerized application
- Push image to registry
- Deploy to VPS with automated migrations
- Verify health checks post-deployment

**Rollback Path:** Redeploy previous tagged version if needed

---

## 4. Deployment Strategy

### 4.1 Key Principles

**Environment Consistency:** Local development and production use identical containerized stacks (Python + PostgreSQL). This eliminates environment-specific bugs and reduces deployment surprises.

**Infrastructure as Code:** Deployment configuration (Docker Compose) and CI/CD pipelines (GitHub Actions) are version-controlled alongside application code.

**Schema Evolution:** Database migrations (via Alembic) are versioned and applied deterministically. Rollback capability is preserved through migration history.

**Secret Management:** Credentials and sensitive config are stored in GitHub Secrets, never in repositories. Injected at runtime into the VPS environment.

**Single Deployable Unit:** The entire application (FastAPI service + PostgreSQL database) is containerized, enabling reproducible deployments across machines and environments.

---

## 5. Strategic Goals

**Code Quality:** Automated testing and linting gates ensure only high-quality code reaches production. Minimum 80% test coverage.

**Reproducibility:** Same Docker image and configuration work identically across developer computers and production VPS.

**Fast Iteration:** PR-to-production cycle is fast (hours, not weeks) but deliberate—manual release tag prevents accidental deployments.

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

**Recommendation:** For a hiring showcase project, single VPS is appropriate. Document the path to multi-instance with load balancing for production scenarios.

### 6.2 Database Strategy

**Local Development:** Docker Compose PostgreSQL runs locally alongside the application container. Schema managed through Alembic migrations.

**Production:** PostgreSQL on VPS (containerized or managed service like AWS RDS). Automated backups and monitoring recommended for real-world scenarios. Migrations applied automatically during deployment.

### 6.3 Observability & Monitoring

For a demo system, basic approach: application logs to stdout (captured by container runtime), health check endpoints for deployment verification. For production scale, add centralized logging and metric collection.

---

## 7. Implementation Approach

**Immediate (Local → Production Ready):**

- GitHub Actions workflow: PR quality gates (lint, test, coverage)
- Semantic versioning for production releases
- Automated deployment via tagged releases
- Health check endpoints for deployment verification

**Future Enhancements (If Scaling):**

- Distributed tracing for request analysis
- Centralized logging across instances
- Automated rollback on health check failure
- Multi-instance load balancing
