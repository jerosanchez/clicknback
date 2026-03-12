
# Confirm purchase (Event-Driven)

**Note:** The public API endpoint for purchase confirmation has been removed. Confirmation is now handled asynchronously by a background job and internal event broker.

## Internal Workflow

- The background job verifies pending purchases against simulated bank data.
- On success, it publishes a `PurchaseConfirmed` event.
- On failure after retries, it publishes a `PurchaseRejected` event.
- An event subscriber updates purchase status and triggers cashback calculation.

## Internal Events

- `PurchaseConfirmed` (purchase_id, user_id, merchant_id, amount, verified_at)
- `PurchaseRejected` (purchase_id, user_id, merchant_id, amount, failed_at, reason)

## Security

- Only the background job and event subscriber can change purchase status to `confirmed` or `rejected`.

## See Also

- [PU-02: Purchase Confirmation](../../../specs/functional/purchases/PU-02-purchase-confirmation.md)
- [ADR-013: Async Purchase Confirmation](../../../design/adr/013-async-purchase-confirmation.md)

### 403 Forbidden – Insufficient Permissions

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to confirm purchases. Admin role required.",
    "details": {
      "required_role": "admin",
      "current_role": "user"
    }
  }
}
```

### 404 Not Found – Purchase Does Not Exist

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Purchase with ID 'a1b2c3d4-5678-90ab-cdef-1234567890ab' does not exist.",
    "details": {
      "resource_type": "purchase",
      "resource_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
    }
  }
}
```
