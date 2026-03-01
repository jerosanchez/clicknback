-- seeds/all.sql

-- Hashed passwords corresponds to string "Str0ng!Pass"
INSERT INTO users (id, email, hashed_password, role, active, created_at) VALUES
    ('b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d', 'alice@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a', 'bob@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a', 'carol@example.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'admin', TRUE, NOW());

INSERT INTO merchants (id, name, default_cashback_percentage, active) VALUES
    -- Additional merchants (active) – enough to exercise pagination (default page_size = 20)
    ('a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d', 'Shoply',        5.0,  TRUE),
    ('b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e', 'QuickCart',     3.5,  TRUE),
    ('c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f', 'UrbanMart',     2.0,  TRUE),
    ('d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a', 'MegaGoods',     4.0,  TRUE),
    ('e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b', 'ElectroHub',    2.5,  TRUE),
    ('f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c', 'TechZone',      6.0,  TRUE),
    ('a7b8c9d0-e1f2-4a3b-4c5d-6e7f8a9b0c1d', 'FreshMarket',   1.5,  TRUE),
    ('b8c9d0e1-f2a3-4b4c-5d6e-7f8a9b0c1d2e', 'StyleHub',      8.0,  TRUE),
    ('c9d0e1f2-a3b4-4c5d-6e7f-8a9b0c1d2e3f', 'HomePlus',      3.0,  TRUE),
    ('d0e1f2a3-b4c5-4d6e-7f8a-9b0c1d2e3f4a', 'SportsPro',     5.5,  TRUE),
    ('e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b', 'BeautyWell',    7.0,  TRUE),
    ('f2a3b4c5-d6e7-4f8a-9b0c-1d2e3f4a5b6c', 'GadgetWorld',   4.5,  TRUE),
    ('a3b4c5d6-e7f8-4a9b-0c1d-2e3f4a5b6c7d', 'FoodiesFresh',  2.0,  TRUE),
    ('b4c5d6e7-f8a9-4b0c-1d2e-3f4a5b6c7d8e', 'TravelGear',    6.5,  TRUE),
    ('c5d6e7f8-a9b0-4c1d-2e3f-4a5b6c7d8e9f', 'PetParadise',   3.5,  TRUE),
    ('d6e7f8a9-b0c1-4d2e-3f4a-5b6c7d8e9f0a', 'BookHaven',     1.0,  TRUE),
    ('e7f8a9b0-c1d2-4e3f-4a5b-6c7d8e9f0a1b', 'FitnessPeak',   9.0,  TRUE),
    ('f8a9b0c1-d2e3-4f4a-5b6c-7d8e9f0a1b2c', 'GreenGrocer',   2.5,  TRUE),
    ('a9b0c1d2-e3f4-4a5b-6c7d-8e9f0a1b2c3d', 'ToyLand',       4.0,  TRUE),
    ('b0c1d2e3-f4a5-4b6c-7d8e-9f0a1b2c3d4e', 'JewelryBox',    10.0, TRUE),
    ('c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f', 'AutoParts Plus', 1.5, TRUE),
    ('d2e3f4a5-b6c7-4d8e-9f0a-1b2c3d4e5f6a', 'KidsCloset',    5.0,  TRUE),
    ('e3f4a5b6-c7d8-4e9f-0a1b-2c3d4e5f6a7b', 'ChefSupplies',  3.0,  TRUE),
    ('f4a5b6c7-d8e9-4f0a-1b2c-3d4e5f6a7b8c', 'OutdoorEscape', 7.5,  TRUE),
    -- Inactive merchants – for testing the active=false filter
    ('a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d', 'LuxWatches',    15.0, FALSE),
    ('b6c7d8e9-f0a1-4b2c-3d4e-5f6a7b8c9d0e', 'VintageVault',  12.0, FALSE),
    ('c7d8e9f0-a1b2-4c3d-4e5f-6a7b8c9d0e1f', 'NightOwl Electronics', 8.5, FALSE);
