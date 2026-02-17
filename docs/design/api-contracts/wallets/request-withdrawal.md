# Request a withdrawal from the user's available wallet balance

**Endpoint:** `POST /users/wallet/withdraw`

**Roles:** Authenticated User

## Request

```json
{
  "amount": 50.00,
  "method": "bank_transfer",
  "details": {
    "iban": "ES9121000418450200051332",
    "account_holder": "Alice Example"
  }
}
```

## Success Response

**Status:** 201 Created

```json
{
  "id": "c1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "requested",
  "amount": 50.00,
  "requested_at": "2026-02-13T12:30:00Z"
}
```

## Failure Responses

### 400 Bad Request – Validation Error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for request body.",
    "details": {
      "violations": [
        {
          "field": "amount",
          "reason": "Amount must be positive and a valid decimal."
        },
        {
          "field": "method",
          "reason": "Payment method must be one of: bank_transfer, card."
        },
        {
          "field": "details.iban",
          "reason": "IBAN format is invalid for bank_transfer method."
        }
      ]
    }
  }
}
```

### 401 Unauthorized – Missing Authentication

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication token is missing or invalid.",
    "details": {
      "issue": "Token expired or malformed",
      "action": "Include a valid Bearer token in the Authorization header."
    }
  }
}
```

### 409 Conflict – Insufficient Available Balance

```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Available balance (25.50) is less than requested amount (50.00).",
    "details": {
      "requested_amount": 50.00,
      "available_balance": 25.50,
      "pending_balance": 5.00,
      "action": "Request a smaller amount or wait for pending cashback to be confirmed."
    }
  }
}
```

### 422 Unprocessable Entity – Withdrawal Policy Violation

```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Withdrawal request violates policy constraints.",
    "details": {
      "violations": [
        "Minimum withdrawal amount is 10.00. Requested: 5.00.",
        "Weekly withdrawal limit (200.00) would be exceeded. Already withdrawn this week: 195.00.",
        "Must wait 48 hours between withdrawals. Last withdrawal was 24 hours ago."
      ],
      "action": "Adjust request amount or timing according to policy limits."
    }
  }
}
```
