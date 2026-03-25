-- seeds/e2e.sql
--
-- Minimal seed data for the E2E test stack.
-- Loaded via the `seed` service in docker-compose.e2e.yml after Alembic
-- migrations run, mirroring the same approach used in `make db-reset`.
--
-- Only the data required to exercise E2E test scenarios is included here.
-- Tests create all merchants, offers, and user accounts dynamically through
-- the API so that each test run is fully isolated and self-contained.

-- Admin user
-- Password corresponds to the literal string "Str0ng!Pass"
-- (same hash as used in seeds/all.sql).
INSERT INTO users (id, email, hashed_password, role, active, created_at) VALUES
    (
        'd9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a',
        'carol@clicknback.com',
        '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO',
        'admin',
        TRUE,
        NOW()
    );
