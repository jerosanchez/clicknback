---
# examples.md for write-integration-tests
---

# Example 1: Merchant Integration Tests

See `tests/integration/merchants/`:
- Create merchant (happy path, validation, auth)
- List merchants (pagination, filtering)
- Update merchant status

# Example 2: Purchase Integration Tests

See `tests/integration/purchases/`:
- Create purchase (idempotency conflict returns 409)
- List purchases (filtering by user, date range, status)
- Admin reverse purchase

---
