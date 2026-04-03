---
# examples.md for review-code
---

# Example: Real Code Review

Common violations and fixes:

1. **Float used for money** → Use `Decimal("amount")`
2. **Missing SELECT FOR UPDATE** → Add `.with_for_update()` on wallet queries
3. **HTTPException in service** → Raise domain exception; catch in API layer
4. **Business logic in api.py** → Move to service; keep API for HTTP only
5. **Duplicate external_id not handled** → Catch IntegrityError, return 409

---
