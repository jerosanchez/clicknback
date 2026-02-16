# ADR 005: Use Containerized PostgreSQL Database

## Status

Accepted

## Context

Database setup varies across developer machines and deployment targets, leading to:
- Environment-specific bugs ("Works on my machine")
- Inconsistent testing environments  
- Long onboarding time for new developers
- Deployment surprises

**Options:** Local install (version mismatches), Cloud database (overkill for dev), Docker (consistent, isolated, offline-capable)

## Decision

Use **containerized PostgreSQL via Docker Compose** for all environments.

**Start database:** `docker-compose up -d`  
**Reset database:** `docker-compose down -v && docker-compose up -d`  
**Connect:** `psql -h localhost -U user -d db`

## Consequences

- ✅ All developers use same PostgreSQL version and configuration
- ✅ Database isolated from host system
- ✅ Easy to reset, backup, migrate
- ✅ One command onboarding
- ✅ CI/CD friendly
- ⚠️ Requires Docker installation
- ⚠️ Potential performance overhead vs. native

## Alternatives Considered

- Local installation: Version mismatches, configuration drift
- Cloud database: Inconsistent for local development

## Rationale

**PostgreSQL:** Open source, reliable, proven at scale, excellent Python ORM support  

**Docker:** Industry standard consistency (Netflix, Amazon, Google). Same image dev/test/prod. Simple lifecycle. Works offline.

For production, consider managed PostgreSQL (AWS RDS) to avoid operational burden. Docker Compose excellent for development and can power CI/CD pipelines.

