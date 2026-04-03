---
# examples.md for write-e2e-tests
---

# Example 1: Purchase Workflow E2E

See `tests/e2e/test_purchase_flow.py`:
- User authenticates
- Submits purchase
- Background job confirms (wait for async)
- Wallet transitions from pending → available

---
