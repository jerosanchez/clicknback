-- seeds/all.sql

-- Hashed passwords corresponds to string "Str0ng!Pass"
INSERT INTO users (id, email, hashed_password, role, active, created_at) VALUES
    ('b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d', 'alice@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a', 'bob@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a', 'carol@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'admin', TRUE, NOW());

INSERT INTO merchants (id, name, default_cashback_percentage, active) VALUES
    ('a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d', 'Shoply', 5.0, TRUE),
    ('b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e', 'QuickCart', 3.5, TRUE),
    ('c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f', 'UrbanMart', 2.0, TRUE),
    ('d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a', 'MegaGoods', 4.0, TRUE),
    ('e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b', 'ElectroHub', 2.5, TRUE);