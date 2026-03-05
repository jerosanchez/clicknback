-- seeds/all.sql

-- Users
-- Includes both regular users and admins, with active status to test filtering.
-- Hashed passwords corresponds to literal string "Str0ng!Pass"
INSERT INTO users (id, email, hashed_password, role, active, created_at) VALUES
    ('b7e2c1a2-4f3a-4e2b-9c1a-8d2e3f4b5c6d', 'alice@clicknback.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('c8d3e2b1-5a4b-4c3d-8b2a-7e6f5d4c3b2a', 'bob@clicknback.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'user', TRUE, NOW()),
    ('d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1a', 'carol@clicknback.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'admin', TRUE, NOW()),
    ('d9f4b3c2-6b5c-5d4e-7c3b-6a5e4d3c2b1b', 'jero@clicknback.com', '$2b$12$XA7sNuNkVQdhGdbW0bHv.OeNnC4RfBSx74dc6sxIA2ETLtIUtKLxO', 'admin', TRUE, NOW());

-- Merchants
-- Active merchants with a variety of cashback percentages to test sorting and filtering,
-- as well as enough entries to test pagination.
-- Inactive merchants are included to test the active=false filter.
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

-- Offers
-- Active percent offer on an active merchant (Shoply)
INSERT INTO offers (id, merchant_id, percentage, fixed_amount, start_date, end_date, monthly_cap_per_user, active) VALUES
    (
        'f0e1d2c3-b4a5-4678-9012-3456789abcde',
        'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',  -- Shoply
        5.0, NULL, '2026-01-01', '2026-12-31', 50.0, TRUE
    ),
    -- Active fixed offer on QuickCart
    (
        'a1b2c3d4-e5f6-4789-0abc-def012345678',
        'b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e',  -- QuickCart
        0.0, 3.00, '2026-02-01', '2026-11-30', 20.0, TRUE
    ),
    -- Inactive (deactivated) offer on UrbanMart – leaves UrbanMart free for a new offer
    (
        'b2c3d4e5-f6a7-4890-abcd-ef1234567890',
        'c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f',  -- UrbanMart
        2.0, NULL, '2025-01-01', '2025-12-31', 15.0, FALSE
    ),
    -- Additional active offers – enough to exceed default page_size (20) for pagination testing
    ('c3d4e5f6-a7b8-4c9d-1111-000000000001', 'c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f', 2.0, NULL, '2026-03-01', '2026-12-31', 15.0, TRUE),   -- UrbanMart (new active)
    ('c3d4e5f6-a7b8-4c9d-1111-000000000002', 'd4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a', 4.0, NULL, '2026-01-01', '2026-12-31', 40.0, TRUE),   -- MegaGoods
    ('c3d4e5f6-a7b8-4c9d-1111-000000000003', 'e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b', 2.5, NULL, '2026-01-01', '2026-12-31', 25.0, TRUE),   -- ElectroHub
    ('c3d4e5f6-a7b8-4c9d-1111-000000000004', 'f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c', 6.0, NULL, '2026-02-01', '2026-12-31', 60.0, TRUE),   -- TechZone
    ('c3d4e5f6-a7b8-4c9d-1111-000000000005', 'a7b8c9d0-e1f2-4a3b-4c5d-6e7f8a9b0c1d', 1.5, NULL, '2026-01-01', '2026-12-31', 10.0, TRUE),   -- FreshMarket
    ('c3d4e5f6-a7b8-4c9d-1111-000000000006', 'b8c9d0e1-f2a3-4b4c-5d6e-7f8a9b0c1d2e', 8.0, NULL, '2026-01-15', '2026-12-31', 80.0, TRUE),   -- StyleHub
    ('c3d4e5f6-a7b8-4c9d-1111-000000000007', 'c9d0e1f2-a3b4-4c5d-6e7f-8a9b0c1d2e3f', 3.0, NULL, '2026-01-01', '2026-12-31', 30.0, TRUE),   -- HomePlus
    ('c3d4e5f6-a7b8-4c9d-1111-000000000008', 'd0e1f2a3-b4c5-4d6e-7f8a-9b0c1d2e3f4a', 5.5, NULL, '2026-02-01', '2026-12-31', 55.0, TRUE),   -- SportsPro
    ('c3d4e5f6-a7b8-4c9d-1111-000000000009', 'e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b', 7.0, NULL, '2026-01-01', '2026-12-31', 70.0, TRUE),   -- BeautyWell
    ('c3d4e5f6-a7b8-4c9d-1111-000000000010', 'f2a3b4c5-d6e7-4f8a-9b0c-1d2e3f4a5b6c', 4.5, NULL, '2026-01-01', '2026-12-31', 45.0, TRUE),   -- GadgetWorld
    ('c3d4e5f6-a7b8-4c9d-1111-000000000011', 'a3b4c5d6-e7f8-4a9b-0c1d-2e3f4a5b6c7d', 2.0, NULL, '2026-03-01', '2026-12-31', 20.0, TRUE),   -- FoodiesFresh
    ('c3d4e5f6-a7b8-4c9d-1111-000000000012', 'b4c5d6e7-f8a9-4b0c-1d2e-3f4a5b6c7d8e', 6.5, NULL, '2026-01-01', '2026-12-31', 65.0, TRUE),   -- TravelGear
    ('c3d4e5f6-a7b8-4c9d-1111-000000000013', 'c5d6e7f8-a9b0-4c1d-2e3f-4a5b6c7d8e9f', 3.5, NULL, '2026-01-01', '2026-12-31', 35.0, TRUE),   -- PetParadise
    ('c3d4e5f6-a7b8-4c9d-1111-000000000014', 'd6e7f8a9-b0c1-4d2e-3f4a-5b6c7d8e9f0a', 1.0, NULL, '2026-02-01', '2026-12-31', 10.0, TRUE),   -- BookHaven
    ('c3d4e5f6-a7b8-4c9d-1111-000000000015', 'e7f8a9b0-c1d2-4e3f-4a5b-6c7d8e9f0a1b', 9.0, NULL, '2026-01-01', '2026-12-31', 90.0, TRUE),   -- FitnessPeak
    ('c3d4e5f6-a7b8-4c9d-1111-000000000016', 'f8a9b0c1-d2e3-4f4a-5b6c-7d8e9f0a1b2c', 2.5, NULL, '2026-01-01', '2026-12-31', 25.0, TRUE),   -- GreenGrocer
    ('c3d4e5f6-a7b8-4c9d-1111-000000000017', 'a9b0c1d2-e3f4-4a5b-6c7d-8e9f0a1b2c3d', 4.0, NULL, '2026-03-01', '2026-12-31', 40.0, TRUE),   -- ToyLand
    ('c3d4e5f6-a7b8-4c9d-1111-000000000018', 'b0c1d2e3-f4a5-4b6c-7d8e-9f0a1b2c3d4e', 10.0, NULL, '2026-01-01', '2026-12-31', 100.0, TRUE), -- JewelryBox
    -- Inactive offers on inactive merchants – for testing the status=inactive filter
    ('c3d4e5f6-a7b8-4c9d-1111-000000000019', 'a5b6c7d8-e9f0-4a1b-2c3d-4e5f6a7b8c9d', 15.0, NULL, '2025-01-01', '2025-12-31', 150.0, FALSE), -- LuxWatches (inactive merchant)
    ('c3d4e5f6-a7b8-4c9d-1111-000000000020', 'b6c7d8e9-f0a1-4b2c-3d4e-5f6a7b8c9d0e', 12.0, NULL, '2025-01-01', '2025-12-31', 120.0, FALSE), -- VintageVault (inactive merchant)
    -- Active-flagged but EXPIRED offer on AutoParts Plus (end_date before today = 2026-03-04)
    -- This row must NOT appear in GET /offers/active even though active=TRUE
    ('c3d4e5f6-a7b8-4c9d-1111-000000000021', 'c1d2e3f4-a5b6-4c7d-8e9f-0a1b2c3d4e5f', 1.5, NULL, '2026-01-01', '2026-02-28', 15.0, TRUE),   -- AutoParts Plus (expired)
    -- Active-flagged but FUTURE offer on KidsCloset (start_date after today = 2026-03-04)
    -- This row must NOT appear in GET /offers/active even though active=TRUE
    ('c3d4e5f6-a7b8-4c9d-1111-000000000022', 'd2e3f4a5-b6c7-4d8e-9f0a-1b2c3d4e5f6a', 5.0, NULL, '2100-04-01', '2100-12-31', 50.0, TRUE),  -- KidsCloset (future)
    -- Targeted offers for PATCH /offers/{id}/status smoke testing
    -- Active offer on OutdoorEscape – targeted by set-offer-status.http (deactivate scenario)
    ('c1d2e3f4-0000-0000-0001-000000000001', 'f4a5b6c7-d8e9-4f0a-1b2c-3d4e5f6a7b8c', 3.0, NULL, '2026-01-01', '2026-12-31', 30.0, TRUE),   -- OutdoorEscape active
    -- Inactive offer on ChefSupplies – targeted by set-offer-status.http (activate scenario)
    ('c1d2e3f4-0000-0000-0002-000000000002', 'e3f4a5b6-c7d8-4e9f-0a1b-2c3d4e5f6a7b', 2.0, NULL, '2026-01-01', '2026-12-31', 20.0, FALSE);  -- ChefSupplies inactive
