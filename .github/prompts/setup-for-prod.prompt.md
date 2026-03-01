# Prompt: Containerize, Deploy, and Harden ClickNBack

> **Note:** This is a project-specific deployment runbook. The overall structure — containerization, compose orchestration, coverage scripting, SonarCloud integration, GitHub Actions CI/CD, and VPS setup — is a reusable pattern. The project-specific values (domain, registry path, VPS layout, blog coexistence) are listed in the **Project-Specific Configuration** section below. To adapt this for a new project, replace those values before handing to the AI.

The app will be fully containerized (new Dockerfile), the compose file will orchestrate DB + migrations + app in the right order, a CD pipeline will deploy on every merge to `main` via SSH to the DigitalOcean VPS, Nginx on the VPS will route `clicknback.com` to the new container alongside the existing Hugo blog, SonarCloud will detect code smells, and a new `make coverage` target with a graded bash script will give a visual coverage quality signal. All relevant docs are updated at the end.

---

## Project-Specific Configuration

The values below are specific to this project. When adapting this runbook for a new project, replace all of them before proceeding.

| What | This project | Replace with |
|---|---|---|
| App domain | `clicknback.com` | your domain |
| Container image | `ghcr.io/jerosanchez/clicknback` | `ghcr.io/<owner>/<repo>` |
| Container service names | `clicknback-app`, `clicknback-db` | your service names |
| VPS deploy path | `/opt/clicknback/` | your deploy path |
| CORS allowed origin | `https://clicknback.com` | your domain |
| SonarCloud project key | set when creating the project on sonarcloud.io | your project key |
| Coexisting service on VPS | Hugo blog at `jerosanchez.com` (Phase 9, Step 23) | remove or replace if not applicable |
| Python version | `python:3.13-slim` | your required version |

## Context Files (Read First)

Before starting any step, read the following project context files in full:

- `docs/agents/feature-guide.md` — coding conventions, module structure, and layering rules
- `docs/agents/quality-gates.md` — mandatory quality gate sequence
- `docs/agents/testing-guidelines.md` — how tests are structured and what to test
- `docs/agents/project-context.md` — domain model and overall system purpose
- `docs/design/architecture-overview.md` — system structure; the API version prefix decision (Step 1) is documented here
- `docs/design/security-strategy.md` — governs CORS allowed origins (Step 2), non-root container requirement (Step 4), and secrets handling rules (Steps 9–10)
- `docs/design/deployment-plan.md` — read the current state before updating it in Steps 25–27
- `docs/agents/markdown-guidelines.md` — all rules for writing `.md` files; every doc updated in Phase 10 must comply and pass `markdownlint`

## Known Constraints

- Do not use allow-all CORS or wildcard origins (`*`) in any configuration that reaches production.
- Do not log passwords, tokens, or secrets at any log level.
- Do not commit `.env` files or real credentials at any point — `.env` is in `.gitignore` and must stay there.
- Never inject production secrets through CI environment variables — they belong in `/opt/clicknback/.env` on the VPS, placed manually once with `chmod 600`.
- Do not add dependencies to `pyproject.toml` without flagging the addition for human review before proceeding.
- Do not modify `app/core/errors/handlers.py` or the global error response shape.
- The application container must run as a non-root user — do not omit the `USER` instruction from the Dockerfile.
- The `migrate` service must use `restart: "no"` — never `on-failure` — migration failures are not transient errors and must not be retried automatically.
- Do not re-seed the database as part of any automated step — seeding is a one-time manual operation (Step 21 only).
- Phase 9 steps are manual and performed directly on the VPS; describe the exact commands to run but do not attempt to execute them remotely.
- All `.md` files created or updated must comply with `docs/agents/markdown-guidelines.md` and pass `markdownlint` — `make lint` must be green before committing any documentation step.
- All tests written must comply with `docs/agents/testing-guidelines.md` — use module-level functions (not classes), the `test_{sut}_{result}_on_{condition}` naming pattern with the `_on_` connector, AAA comments, and section separators as specified in that document.

## Commit Protocol

Each step that produces code, configuration, or documentation is a **separate commit**. Do not begin the next step until the current step's commit is approved and executed by the human.

**AI agents may run any read-only or research commands autonomously, without asking permission.** This includes, but is not limited to: `make test`, `make lint`, `make format`, listing files, searching, or any command that does not modify project state. Only state-changing actions (e.g., `git commit`, file edits, deployments) require explicit human approval.

To close a step:

1. Run `make lint && make format && make test` — all must pass.
2. Stage the changes and output `git diff --staged`.
3. Propose a commit message. Keep it short and outcome-focused — state what the step achieves, not which files were
   changed or how it was implemented. File-level details are already visible in the diff. One line is almost always
   enough; use a body paragraph only when the *why* is non-obvious from the step description.
4. **Wait for explicit human approval before executing `git commit`.**

When resuming work after a break, read the **Progress** section first to identify the next incomplete step, then continue from there without re-doing completed ones. After the human approves a commit for a step, mark that step's checkbox as done (`- [x]`) and include that change in the same commit.

---

## Progress

- [x] Step 1 — API version prefix `/api/v1/`
- [x] Step 2 — CORS middleware
- [x] Step 3 — `/health/live` and `/health/ready` probes
- [x] Step 4 — Dockerfile (two-stage, non-root)
- [x] Step 5 — `.dockerignore`
- [x] Step 6 — Add `APP_PORT` and `APP_IMAGE` to `.env.example`
- [ ] Step 7 — Rewrite `docker-compose.yml` (migrate + app services)
- [ ] Step 8 — Rename `make run` → `make dev`, add `make logs`
- [ ] Step 9 — Document static secrets strategy for VPS
- [ ] Step 10 — Add GitHub Secrets (VPS_HOST, VPS_USER, VPS_SSH_KEY, SONAR_TOKEN)
- [ ] Step 11 — Add `--cov-report=xml` to `make test`
- [ ] Step 12 — Create `scripts/coverage-grade.sh`
- [ ] Step 13 — Add `make coverage` target
- [ ] Step 14 — Create SonarCloud project and enable Quality Gate (manual, UI)
- [ ] Step 15 — Create `sonar-project.properties`
- [ ] Step 16 — Add `make sonar` target
- [ ] Step 17 — Update `.github/workflows/ci.yml` (coverage + sonar jobs)
- [ ] Step 18 — Add `.github/dependabot.yml`
- [ ] Step 19 — Create `.github/workflows/cd.yml`
- [ ] Step 20 — Initial VPS provisioning (manual, on VPS)
- [ ] Step 21 — First-deploy seeding (manual, on VPS)
- [ ] Step 22 — Nginx virtual host + Certbot TLS (manual, on VPS)
- [ ] Step 23 — Verify blog coexistence on VPS (manual, on VPS)
- [ ] Step 24 — Database backup and nightly reseed cron jobs (manual, on VPS)
- [ ] Step 25 — Document rollback procedure in deployment-plan.md
- [ ] Step 26 — Document production log access in deployment-plan.md
- [ ] Step 27 — Update `docs/design/deployment-plan.md`
- [ ] Step 28 — Update `docs/agents/quality-gates.md`
- [ ] Step 29 — Update `README.md`
- [ ] Step 30 — Update `.env.example`

---

## Phase 1 — API Hygiene *(generic)*

1. **Decide and apply an API version prefix.** Mount all routers under `/api/v1/` in `app/main.py` (e.g., `/api/v1/users`, `/api/v1/auth`, `/api/v1/merchants`).

Even for a v1-only system, the prefix signals intent and avoids a breaking migration later. Document the decision explicitly in `docs/design/architecture-overview.md`. This is a deliberate design choice that senior engineers are expected to have made — leaving routes at the root silently defers a forward-compatibility problem.

2. **Add CORS middleware** to `app/main.py` via FastAPI's `CORSMiddleware`. For the demo environment allow `https://clicknback.com` (and optionally `http://localhost:*` for local dev) as origins; never use allow-all (`*`) in a configuration that reaches production.

Without CORS headers, any browser-based client — including the hosted Swagger UI at `/docs` — will fail when called from a different origin. This is one of the first things a recruiter will notice if they try to call the API from a script or frontend playground.

3. **Split the health endpoint into two probes:**

- `GET /health/live` — returns `{"status": "alive"}` immediately, no I/O. Used by Docker to decide whether to restart the container (liveness).
- `GET /health/ready` — executes `SELECT 1` via the SQLAlchemy engine and returns `{"status": "ready"}` only if the DB responds. Used by Nginx and the CD pipeline to decide whether to route traffic (readiness). Implementation: import `engine` from `app.core.database` and `text` from `sqlalchemy`; inside the route handler call `engine.connect()` as a context manager, execute `text("SELECT 1")`, and return `{"status": "ready"}`; wrap the entire block in `try/except Exception` and return an `HTTP 503` `JSONResponse` with `{"status": "unavailable"}` on any error. Do not use the `get_db()` FastAPI dependency — this probe must work without a request-scoped session.

The distinction matters because a process can be alive (liveness passes) but unable to serve requests due to a lost DB connection (readiness fails). Conflating the two causes silent availability gaps: the container is never restarted, but every request fails internally.

---

## Phase 2 — App Container *(generic)*

4. **Create `Dockerfile`** at repo root using a two-stage build. The `builder` stage uses `python:3.13-slim` and installs only runtime dependencies (`pip install .` without `[dev]`), producing a populated `site-packages`. The `runtime` stage copies only what is needed (`app/`, `alembic/`, `alembic.ini`, `seeds/`, and the installed packages) and drops privileges to a non-root user before setting `CMD` to `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

Two-stage builds keep the final image small (no build tools, no test libraries) and running as non-root is a baseline container security requirement — running as root inside a container is mapped to root on the host if the container runtime is misconfigured.

**Smoke-test the image before committing.** After creating the Dockerfile, build and run it to confirm the image works end-to-end:

1. Start the database: `docker compose up -d clicknback-db` and wait until healthy.
2. Build the image: `docker build -t clicknback:smoke-test .` — the build must complete with no errors.
3. Start a short-lived container on `clicknback-nw`, passing `DATABASE_URL` as a full connection string (the `config.py` `Settings` model expects this single field, not the individual `POSTGRES_*` vars), plus all other required env vars from `.env`.
4. Confirm startup in the logs: look for `Application startup complete.` and `Uvicorn running on http://0.0.0.0:8000`.
5. Hit both probes: `curl localhost:<port>/health/live` → `{"status":"alive"}` and `curl localhost:<port>/health/ready` → `{"status":"ready"}` with HTTP 200.
6. Confirm the non-root user: `docker exec <container> whoami` must return `appuser`, not `root`.
7. Clean up: `docker rm -f <container>`, `docker rmi clicknback:smoke-test`, `docker compose down`.

Only after all six checks pass may the step be committed.

5. **Add `.dockerignore`** at repo root, excluding: `.venv/`, `__pycache__/`, `htmlcov/`, `tests/`, `.github/`, `.env`, `.env.example`, `*.egg-info`, `coverage.*`, `Makefile`, `docs/`, and `CONTRIBUTING.md`.

Without this file, Docker's build context includes every file in the repo, which slows builds and risks accidentally baking secrets (`.env`) or test artifacts into the image layer cache.

**Do not exclude `README.md`** (with a wildcard or explicit rule). The builder stage copies it explicitly because setuptools reads it for package metadata during `pip install .` — excluding it would fail the build. Exclude `docs/` and individual `.md` files by name instead of using a `*.md` glob.

---

## Phase 3 — Compose Orchestration *(generic)*

6. **Add `APP_PORT` and `APP_IMAGE` variables** to `.env.example`. `APP_PORT` controls the host-side published port (useful to avoid conflicts with other services on the VPS). `APP_IMAGE` allows the CD pipeline to inject the exact `sha`-tagged image pulled from ghcr.io, making each deploy fully traceable to a commit.

   Also add the same variables to your local `.env` before proceeding to Step 7 — they are required to smoke-test the new compose services.

7. **Rewrite `docker-compose.yml`** to add two new services alongside the existing `clicknback-db`:

   - **`migrate` service**: uses the app image; overrides `command` to `alembic upgrade head`; `depends_on: clicknback-db: condition: service_healthy`; `restart: "no"`. It is a one-shot container that must exit 0. The restart policy must be `"no"` — not `on-failure` — because a migration failure (e.g., conflicting schema, bad SQL) is not a transient error. Retrying it automatically would mask the root cause and could corrupt the schema.

   - **`clicknback-app` service**: uses the app image; `depends_on` both `clicknback-db: condition: service_healthy` and `migrate: condition: service_completed_successfully`; exposes `${APP_PORT}:8000`; uses `GET /health/ready` as its Docker health check (not `/health/live`, since we want the container to be healthy only when the DB is reachable); `restart: unless-stopped`. The double dependency chain — DB healthy AND migrations complete — is the key coordination mechanism that prevents the app from starting against an unready or unmigrated database.

   **Smoke-test the compose stack before committing.** After writing the file, run the full stack end-to-end:

   1. Ensure your local `.env` has `APP_PORT` and `APP_IMAGE` set (Step 6).
   2. Build the image with the tag that matches `APP_IMAGE`: `docker build -t <APP_IMAGE> .`
   3. Create the network if it doesn't exist: `docker network create clicknback-nw` (or `make up` does this automatically).
   4. Start the full stack: `make up` — this should bring up `clicknback-db`, then `migrate` (exits 0), then `clicknback-app`.
   5. Confirm the `migrate` container exited successfully: `docker compose ps` must show `migrate` with state `Exited (0)`.
   6. Confirm `clicknback-app` is healthy: `docker compose ps` must show `clicknback-app` with state `healthy`.
   7. Hit the readiness probe: `curl localhost:${APP_PORT}/health/ready` → `{"status":"ready"}` with HTTP 200.
   8. Inspect migration logs: `docker compose logs migrate` — must show `Running upgrade` lines and no errors.
   9. Tear down: `make down`.

   Note: the `migrate` and `clicknback-app` services override `DATABASE_URL` in compose to point at `clicknback-db` (the Docker service name) rather than `localhost`. This is intentional — `localhost` in the local `.env` works for `make test` (direct pytest against the host Postgres), while the compose override ensures containers reach the DB over the Docker network.

   Only after all checks pass may the step be committed.

8. **Update `Makefile`**: rename the existing `make run` to `make dev` (local uvicorn with `--reload`, dev only). Add a `make logs` target (`docker compose logs -f clicknback-app`) for tailing production-style container logs locally. `make up` already starts compose — after this phase it starts the full stack (DB + migrations + app). Keeping `make dev` distinct from `make up` preserves the fast inner-loop workflow without a container rebuild on every code change.

---

## Phase 4 — Production Secrets Management *(generic)*

9. **Establish a static secrets strategy for the VPS.** The `.env` file with production values is placed manually on the VPS at `/opt/clicknback/.env` once, with `chmod 600` and owned by the deploy user.

The CD pipeline never writes or touches this file — it only pulls the new image and restarts compose. This is the correct separation of concerns: secrets are an operational concern, not a deployment artifact. Documenting this explicitly prevents the anti-pattern of injecting secrets through CI environment variables directly into `docker compose up`, which would make secrets visible in CI logs.

10. **Add the following GitHub Secrets** to the repository (Settings → Secrets → Actions): `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `SONAR_TOKEN`. These are referenced by the CI/CD workflows. `VPS_SSH_KEY` should be a dedicated deploy key (not a personal key) — generate a new Ed25519 keypair, add the public key to `~/.ssh/authorized_keys` on the VPS, and store the private key as the secret.

---

## Phase 5 — Coverage Script & Makefile Target *(generic)*

11. **Add `--cov-report=xml`** to both `make test` and the new `make coverage` target in `Makefile`. The XML report (`coverage.xml`) is the machine-readable format consumed by SonarCloud and CI coverage gates. The HTML report (`htmlcov/`) is for human inspection. Generating both from the same run avoids running pytest twice and ensures the reports are always in sync.

12. **Create `scripts/coverage-grade.sh`** — a bash script that parses the total line from `coverage.txt` (the captured pytest-cov stdout), extracts the percentage, and prints an emoji-graded result:

    - `< 50%` → ❌ **Poor** — significant gaps, must improve
    - `50–69%` → ⚠️ **Low** — almost there, keep going
    - `70–79%` → ✅ **Approved** — minimum bar cleared
    - `80–89%` → 🌟 **High** — above expectations
    - `≥ 90%` → 🚀 **Excellent** — outstanding coverage

    Exits non-zero if coverage is below 70%, so `make coverage` fails loudly when the threshold is not met. The human-readable grade is designed to give instant visual feedback at the terminal without reading numbers — useful in code review discussions and standup demos.

13. **Add `make coverage`** target in `Makefile`:

    ```makefile
    coverage:
        pytest tests/ --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml > coverage.txt 2>&1; bash scripts/coverage-grade.sh
    ```

---

## Phase 6 — SonarCloud Integration *(generic)*

14. **Create a project on sonarcloud.io**: sign in with GitHub, import the repository, note the `projectKey` and `organization` slug assigned. Enable the "Sonar Way" Quality Gate in the project's Quality Gate settings and tick **"Fail the pipeline if the Quality Gate status is Failed"**. This step is purely in the SonarCloud UI but is critical — without it, the GitHub Action runs the scan but never blocks a PR, making the gate decorative rather than enforcing.

15. **Create `sonar-project.properties`** at repo root with `sonar.projectKey`, `sonar.organization`, source dir (`app/`), coverage report path (`coverage.xml`), and exclusions (`tests/`, `alembic/`, `seeds/`). This file is the contract between the repo and SonarCloud: it tells the scanner what to analyze, what to skip, and where to find the coverage data so that SonarCloud's code smell, duplication, and security hotspot results are scoped correctly to production code.

16. **Add `make sonar`** target in `Makefile`: runs `sonar-scanner` via Docker (`docker run --rm -v $(PWD):/usr/src sonarsource/sonar-scanner-cli`) so no local install is required. This enables developers to run a full SonarCloud scan locally before pushing, closing the feedback loop without waiting for CI.

---

## Phase 7 — GitHub Actions CI Update *(generic)*

17. **Update `.github/workflows/ci.yml`** to extend the job chain: add a **`coverage`** job after `test` that re-runs pytest with `--cov-fail-under=70` as a hard gate (`pytest tests/ --cov=app --cov-report=xml --cov-fail-under=70`); add a **`sonar`** job after `coverage` using `SonarSource/sonarcloud-github-action@master` with `SONAR_TOKEN`. Final job order: `lint` → `test` → `coverage` → `sonar`. Keeping `test` and `coverage` as separate jobs makes failure reasons unambiguous in the GitHub Actions UI: a red `coverage` job means the threshold was missed specifically, not that tests are broken.

18. **Add `.github/dependabot.yml`** to configure automated dependency update PRs for both the Python ecosystem (`pip`, weekly) and GitHub Actions (`github-actions`, weekly). Dependabot PRs run through the full CI pipeline automatically, so security and compatibility regressions in dependencies are caught without manual audits. This is a one-file addition that signals proactive maintenance discipline — a quality that senior engineers are expected to embed into a project from the start.

---

## Phase 8 — GitHub Actions CD Pipeline *(generic — uses project-specific image and domain from the configuration table above)*

19. **Create `.github/workflows/cd.yml`** triggered by `workflow_run` on the CI workflow completing successfully on `main`. The **`build-push`** job logs in to `ghcr.io` with `GITHUB_TOKEN` (no extra secret needed), builds the image, and pushes two tags: `ghcr.io/jerosanchez/clicknback:latest` and `ghcr.io/jerosanchez/clicknback:sha-${{ github.sha }}`. Tagging with the commit SHA makes every image traceable to its exact source — `latest` is a convenience alias for compose to reference, but the SHA tag is what enables precise rollbacks. The **`deploy`** job (needs `build-push`) SSHes into the VPS via `appleboy/ssh-action` and runs:

    ```bash
    docker pull ghcr.io/jerosanchez/clicknback:latest
    docker compose -f /opt/clicknback/docker-compose.yml up -d --no-build --remove-orphans
    ```

    The `--remove-orphans` flag removes the `migrate` container from the previous deploy, preventing stale one-shot containers from accumulating. After `up -d`, the job polls `GET https://clicknback.com/health/ready` with `curl --retry 10 --retry-delay 3 --fail` as the post-deploy health check: if the app does not become ready within ~30 seconds, the job fails and the team is notified via GitHub's native failure notification.

---

## Phase 9 — VPS Setup *(project-specific — manual one-time steps)*

> **⚙️ Project-specific phase.** This phase reflects the exact setup for this project: DigitalOcean VPS, `/opt/clicknback/` deploy path, `clicknback.com` domain, Nginx + Certbot TLS, and coexistence with a Hugo blog. Adapt or drop steps that do not apply to a different deployment target.

20. **Initial VPS provisioning**: create `/opt/clicknback/`, place `docker-compose.yml` and `.env` (with production values, `chmod 600`). Add the deploy user to the `docker` group (`sudo usermod -aG docker deploy`). Create the shared Docker network: `docker network create clicknback-nw`. Log in to ghcr.io: `docker login ghcr.io -u jerosanchez -p <PAT>` (use a Personal Access Token with `read:packages` scope). This bootstrapping only happens once — all subsequent deploys are automated via CD.

21. **First-deploy seeding**: after the initial `docker compose up -d`, seed the database:

    ```bash
    docker exec -i clicknback-db psql -U $POSTGRES_USER -d $POSTGRES_DB < /opt/clicknback/seeds/all.sql
    ```

    Before running this, ensure `seeds/all.sql` includes a hardcoded demo admin user (e.g., `admin@clicknback.com` / `demo1234` with `admin` role). This user is the entry point for testers who need to exercise admin-only endpoints. The credentials will be documented in the README. The nightly cron (Step 24) re-runs this same seed file every morning, so the first-deploy seeding and the nightly reset use the same source of truth.

22. **Nginx virtual host** (`/etc/nginx/sites-available/clicknback.com`): `server_name clicknback.com www.clicknback.com;`, `proxy_pass http://127.0.0.1:${APP_PORT};`, with `proxy_set_header` blocks for `Host`, `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto`. Run `sudo certbot --nginx -d clicknback.com -d www.clicknback.com` for automatic TLS. Add an A record for `clicknback.com` → VPS IP and a CNAME for `www`.

    Also add rate limiting to protect the unauthenticated endpoints (login and registration) from abuse. Define a rate limit zone in the `http` block of `/etc/nginx/nginx.conf`:

    ```nginx
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
    ```

    Then apply it to the sensitive locations inside the `server` block for `clicknback.com`:

    ```nginx
    location ~ ^/api/v1/(auth/login|users)$ {
        limit_req zone=auth burst=3 nodelay;
        proxy_pass http://127.0.0.1:${APP_PORT};
    }
    ```

    This allows bursts of up to 3 requests per IP before rate-limiting kicks in, which is enough for legitimate demo use without enabling brute-force or registration spam. Nginx acts as the TLS terminator, reverse proxy, and first-line abuse guard — the app itself never deals with certificates or rate limiting.

23. **Blog coexistence**: the Hugo container already runs on the VPS and is reached via the `jerosanchez.com` `server_name` block in Nginx. The ClickNBack app gets its own block for `clicknback.com` on a different `APP_PORT`. Both blocks are served by the same Nginx process — no port conflicts, no changes to the blog config needed. Both domains share the same TLS infrastructure managed by Certbot.

24. **Database backup and nightly reseed cron jobs**: add the following entries to the deploy user's crontab (`crontab -e`):

    ```bash
    # 03:00 — back up the database before wiping it
    0 3 * * * docker exec clicknback-db pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > /opt/clicknback/backups/clicknback-$(date +\%F).sql.gz

    # 03:01 — remove backups older than 7 days
    1 3 * * * find /opt/clicknback/backups/ -name "*.sql.gz" -mtime +7 -delete

    # 03:05 — reset and reseed the database for a fresh demo state
    5 3 * * * docker exec -i clicknback-db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" && docker compose -f /opt/clicknback/docker-compose.yml run --rm migrate && docker exec -i clicknback-db psql -U $POSTGRES_USER -d $POSTGRES_DB < /opt/clicknback/seeds/all.sql
    ```

    The backup runs first (03:00) so a restorable snapshot always exists before the wipe. The 5-minute gap gives the backup time to complete. The reseed sequence is three operations: drop and recreate the public schema (wipes all data), run migrations to restore the schema structure, then load `seeds/all.sql`. This gives every recruiter or reviewer a clean, consistent demo state each morning without requiring a manual reset. Even for a demo system, losing the database due to an accidental volume deletion or VPS snapshot failure is an avoidable incident — the backup cron is the minimum responsible baseline regardless of the nightly reset.

25. **Rollback procedure** (documented in `docs/design/deployment-plan.md`): every deploy pushes a `sha-<commit>` image to ghcr.io. To roll back to the previous version:

    ```bash
    # On the VPS
    docker pull ghcr.io/jerosanchez/clicknback:sha-<previous-commit>
    export APP_IMAGE=ghcr.io/jerosanchez/clicknback:sha-<previous-commit>
    docker compose -f /opt/clicknback/docker-compose.yml up -d --no-build --remove-orphans
    ```

    If the rollback also requires a schema downgrade: `docker compose run --rm migrate alembic downgrade -1` before restarting the app. The rollback SHA can be found in the GitHub Actions run history or via `docker images | grep clicknback`. Document this as a runbook section, not left implicit.

26. **Production log access** (documented as a runbook one-liner):

    ```bash
    ssh deploy@<VPS_HOST> "docker compose -f /opt/clicknback/docker-compose.yml logs -f clicknback-app"
    ```

    Application logs flow to stdout (as configured by `app/core/logging.py`), Docker captures them, and this command tails them remotely in real time. No log agent is required for a demo system. Document this in the deployment plan so the team knows how to diagnose a production issue without guessing.

---

## Phase 10 — Documentation *(generic)*

27. **Update `docs/design/deployment-plan.md`**: reflect the full production architecture — Dockerfile two-stage build, ghcr.io image registry, `clicknback.com` domain, Nginx reverse proxy with Certbot, CD on merge to main, migration container pattern, secrets strategy, backup cron, nightly reseed schedule, rollback runbook, and log access one-liner.

28. **Update `docs/agents/quality-gates.md`**: add `make coverage` and `make sonar` to the mandatory gate sequence, document the coverage grading scale, and note the SonarCloud Quality Gate dashboard configuration as a required one-time setup step.

29. **Update `README.md`**: add the following sections:

    - **"Try the Live API"** — place this near the top, before any local setup instructions. Include: the base URL (`https://clicknback.com`), a direct link to the interactive Swagger UI (`https://clicknback.com/docs`), demo credentials for the admin user (`admin@clicknback.com` / `demo1234`) to access admin-only endpoints, a note that anyone can also self-register via `POST /api/v1/users` for a personal account, a note that the database resets nightly at 03:00 UTC so any data created will not persist, and a short etiquette line — "This is a shared demo environment; please be considerate." Keep this section to ~8 lines — Swagger covers endpoint details.
    - **"Running with Docker"** — `make up` starts the full stack (DB + migrations + app).
    - **"Development"** — `make dev` for local hot-reload without Docker.
    - **"Production"** — pointer to `docs/design/deployment-plan.md` for the full runbook.

30. **Update `.env.example`**: add `APP_PORT` (e.g., `8001`), `APP_IMAGE` (e.g., `ghcr.io/jerosanchez/clicknback:latest`), and a comment explaining the static secrets strategy.

---

## Verification

- Locally: `make up` → DB healthy → migrations complete → app healthy → `curl localhost:${APP_PORT}/health/ready` returns `{"status":"ready"}`.
- Locally: `make coverage` → `coverage.xml` generated → emoji grade printed → exits non-zero below 70%.
- CI on a PR: `lint` → `test` → `coverage` (gate at 70%) → `sonar` (Quality Gate enforced in SonarCloud dashboard).
- CD on merge to main: image built and pushed to ghcr.io with `sha-` and `latest` tags → VPS pulls → `--remove-orphans` cleans stale containers → `/health/ready` polling confirms readiness.
- Production: `https://clicknback.com/health/ready` returns HTTP 200 over HTTPS.

---

## Decisions

- **CD trigger**: merge to `main` (over semver tag) — simpler for a demo/showcase workflow; a tag-based strategy can be layered on top later.
- **Image registry**: `ghcr.io` — free, no extra credentials beyond `GITHUB_TOKEN`, images are private by default.
- **Static analysis**: SonarCloud (hosted) over self-hosted SonarQube — no VPS resources consumed, free for OSS, GitHub-native Quality Gate integration.
- **Coverage threshold**: 70% hard gate in CI, 80% aspirational goal documented in deployment plan.
- **Secrets**: static `.env` on VPS, never written by CI — clean separation of deployment and operational concerns.
- **No re-seeding on deploy**: seeds are dev/demo only (`make db-reset`); automated re-seeding in CD would destroy production data.
- **API versioning**: `/api/v1/` prefix applied now — zero cost to add, high cost to add after a public API exists.
- **CORS**: explicit allowlist (not wildcard) — production-safe from day one, easy to extend.
