---
# examples.md for write-unit-tests
---

# Example 1: Merchant Service Tests

See `tests/unit/merchants/test_merchants_services.py`:
- Creation with uniqueness validation
- List with filtering
- Status updates
- Error cases (not found, validation failure)

# Example 2: Purchase Service Tests

See `tests/unit/purchases/test_purchases_services.py`:
- Complex: Multiple dependencies (repository, clients, policies)
- Write operations with UoW pattern
- Collaborator verification (verify clients called correctly)
- Event publishing assertions

# Example 3:Purchase API Tests

See `tests/unit/purchases/test_purchases_api.py`:
- List endpoint with pagination and filtering
- Create endpoint with error mapping
- Admin vs. public endpoint separation
- Error scenarios (404, 422, 409, 500)

---
