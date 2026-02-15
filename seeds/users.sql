-- seeds/users.sql
-- Seed script to insert 3 users

-- Hashed passwords corresponds to string "Str0ng!Pass"
INSERT INTO users (id, email, hashed_password, role, active, created_at) VALUES
    ('b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d', 'alice@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a', 'bob@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'admin', TRUE, NOW()),
    ('d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a', 'carol@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW());
