# ── builder stage ─────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Copy only the files needed to resolve and install runtime dependencies.
# Keeping this layer separate from the source copy maximises cache reuse:
# as long as pyproject.toml and README.md don't change, the pip install
# layer is not rebuilt even when application code changes.
COPY pyproject.toml README.md ./
COPY app/ ./app/

# Install runtime dependencies only — no [dev] extras.
# --no-cache-dir keeps the layer lean.
RUN pip install --no-cache-dir .

# ── runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /srv

# Bring over the installed packages and console scripts from the builder.
# Nothing else from the build environment is needed in the final image.
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only the runtime artefacts required to run the application.
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY seeds/ ./seeds/

# Run as a dedicated non-root user. This is a baseline container security
# requirement: a misconfigured container runtime would otherwise map root
# inside the container to root on the host.
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# Bind to all interfaces so Docker can route traffic to the container.
# The host-side port is controlled externally via APP_PORT in compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
