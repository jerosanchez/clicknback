# ADR 005: Use Containerized PostgreSQL Database

## Status

Accepted

## Context

The application requires a reliable, scalable, and consistent database solution for development, testing, and production environments. Previously, database setup and configuration varied across developer machines and deployment targets, leading to inconsistencies and increased onboarding time.

## Decision

We will use a containerized PostgreSQL database, managed via Docker Compose, as the default database solution for all environments (development, testing, and production). The PostgreSQL service will be defined in the `docker-compose.yml` file, ensuring that the database can be started, stopped, and configured consistently across all environments.

## Consequences

- All developers and CI/CD pipelines use the same database version and configuration, reducing environment-specific bugs.
- The database runs in its own container, isolated from the host system, minimizing conflicts with other services.
- Onboarding new developers is simplified, as they only need Docker and Docker Compose to start the database.
- Database state can be easily reset or migrated using container lifecycle commands.
- Developers must have Docker installed and running, and there may be some performance overhead compared to a native installation.

## Alternatives Considered

- Using a locally installed PostgreSQL instance on each developer's machine.
- Using a managed cloud database for all environments.

Both alternatives were rejected due to increased setup complexity, cost, or lack of reproducibility.

## Rationale

PostgreSQL was chosen as the database engine because it is open source, widely adopted, and offers strong support for advanced SQL features, data integrity, and extensibility. It is well-documented, has a large community, and is proven in production for a wide range of applications. PostgreSQL's reliability, standards compliance, and compatibility with popular Python ORMs (such as SQLAlchemy) make it a robust choice for both current and future needs of the application.

Using a containerized PostgreSQL database ensures consistency and reproducibility across all environments, aligning with modern best practices for application development and deployment. This approach simplifies onboarding, reduces environment-specific issues, and supports automated testing and CI/CD workflows. It balances operational simplicity with flexibility, allowing the team to manage database versions and configurations centrally while keeping the development process efficient and reliable.

