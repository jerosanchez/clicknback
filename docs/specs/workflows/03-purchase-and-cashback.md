# Workflow 3 — Purchase Ingestion and Cashback Calculation

> **Goal:** Simulate a purchase event arriving from an external system (a merchant's POS/e-commerce), confirm it, and verify that cashback is credited to the user's wallet.
>
> **Who runs this:** The first two steps are triggered by an external system (in production); confirmation is done by an admin.
>
> **Pre-condition:** An active merchant + active offer exist (Workflow 1). A registered user exists (Workflow 2). You are authenticated as admin for the webhook call (this endpoint requires a valid token with system-level access).
>
> **HTTP file:** [`http/03-purchase-and-cashback.http`](http/03-purchase-and-cashback.http)
>
> **Note:** Purchase, wallet, and payout endpoints are **backlog** features — they are designed and fully specified but not yet implemented. The `.http` file documents the intended interactions against the upcoming API surface.

---

## Sequence Diagram

```mermaid
sequenceDiagram
    actor ExtSys as External System<br/>(Merchant POS)
    actor Admin
    actor User
    participant API as ClickNBack API
    participant DB as Database
    participant Wallet as Wallet Service

    Admin->>API: POST /api/v1/auth/login
    API-->>Admin: 200 OK · access_token

    ExtSys->>API: POST /api/v1/purchases<br/>{external_id, user_id, merchant_id, amount, currency}
    API->>DB: Check idempotency key (external_id)
    alt external_id already exists
        DB-->>API: existing purchase
        API-->>ExtSys: 200 OK · existing purchase (no duplicate)
    else new purchase
        DB-->>API: —
        API->>DB: Insert purchase (status: "pending", cashback_amount: 0)
        DB-->>API: purchase record
        API-->>ExtSys: 201 Created · {id, status: "pending", cashback_amount: 0}
    end

    Admin->>API: POST /api/v1/purchases/{id}/confirm
    API->>DB: Fetch active offer for merchant on purchase date
    alt active offer found
        DB-->>API: offer {cashback_type, cashback_value, monthly_cap}
        API->>DB: Sum user's cashback for this offer this month
        DB-->>API: already_earned amount
        Note over API: raw = amount × cashback_value%<br/>remaining_cap = monthly_cap − already_earned<br/>credited = min(raw, remaining_cap)
        API->>Wallet: Credit user wallet (amount: credited, status: "pending")
        Wallet->>DB: Insert wallet transaction
    else no active offer
        Note over API: cashback = 0
    end
    API->>DB: Update purchase (status: "confirmed", cashback_amount: credited)
    DB-->>API: updated purchase
    API-->>Admin: 200 OK · {status: "confirmed", cashback_amount}

    User->>API: POST /api/v1/auth/login
    API-->>User: 200 OK · access_token

    User->>API: GET /api/v1/users/{user_id}/purchases
    API->>DB: Query purchases for user
    DB-->>API: paginated purchase list
    API-->>User: 200 OK · {items: [{status, amount, cashback_amount}, ...]}

    User->>API: GET /api/v1/purchases/{purchase_id}
    API->>DB: Fetch purchase details
    DB-->>API: purchase record
    API-->>User: 200 OK · full purchase object with cashback_amount
```

---

## Steps

| # | Action | Endpoint |
| --- | --- | --- |
| 1 | (Admin) Login | `POST /api/v1/auth/login` |
| 2 | Ingest a purchase via webhook (external system call) | `POST /api/v1/purchases` |
| 3 | Confirm the purchase (transitions it from `pending` → `confirmed`, triggers cashback calculation) | `POST /api/v1/purchases/{purchase_id}/confirm` |
| 4 | (User) Login | `POST /api/v1/auth/login` |
| 5 | View the user's purchase history | `GET /api/v1/users/{user_id}/purchases` |
| 6 | View purchase details (includes calculated cashback amount) | `GET /api/v1/purchases/{purchase_id}` |

## What to Expect

- The purchase ingestion endpoint is **idempotent**: submitting the same `external_id` twice returns the existing purchase, not a duplicate. This is critical for resilient webhook delivery.
- A freshly ingested purchase has `cashback_amount: 0` and `status: pending`.
- On confirmation, the system looks up the active offer for the merchant at the time of purchase, applies either the percentage or fixed-amount rule (capped by `monthly_cap_per_user`), and credits the user's wallet with a `pending` cashback transaction.
- If no active offer exists for the merchant at the time of purchase, cashback is `0`.

## Cashback Calculation Logic

Given an offer with `cashback_type = "percent"` and `cashback_value = 5.0` (5%) and a purchase of `€100.00`:

- Raw cashback = `€100.00 × 5% = €5.00`
- If the user has already earned `€3.00` from this offer this month and `monthly_cap = €6.00`, then only `€3.00` more can be credited (cap enforcement).
- The credited amount appears in the wallet as a `pending` balance.

---

_Back to [End-to-End Workflows](end-to-end-workflows.md)_
