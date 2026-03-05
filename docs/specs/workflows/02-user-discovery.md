# Workflow 2 — User Registration and Offer Discovery

> **Goal:** Register as a new user, log in, and explore what cashback offers are currently available.
>
> **Who runs this:** An end-user (new to the platform).
>
> **Pre-condition:** At least one active merchant with an active offer exists (run Workflow 1 first, or use the pre-seeded demo data).
>
> **HTTP file:** [`http/02-user-discovery.http`](http/02-user-discovery.http)

---

## Sequence Diagram

```mermaid
sequenceDiagram
    actor Anon as Anonymous User
    actor User
    participant API as ClickNBack API
    participant DB as Database

    Anon->>API: POST /api/v1/users<br/>{email, password}
    API->>DB: Insert user (role: "user", active: true)
    DB-->>API: user record
    API-->>Anon: 201 Created · {id, email, role, created_at}

    Note over Anon,User: Account is active immediately — no email verification needed

    User->>API: POST /api/v1/auth/login<br/>{email, password}
    API->>DB: Verify credentials
    DB-->>API: user record
    API-->>User: 200 OK · {access_token, token_type: "bearer"}

    User->>API: GET /api/v1/offers/active?page=1&page_size=10
    API->>DB: Query offers where offer.active=true<br/>AND merchant.active=true<br/>AND today ∈ [start_date, end_date]
    DB-->>API: paginated offer list
    API-->>User: 200 OK · {items: [...], total, page, page_size}

    User->>API: GET /api/v1/offers/{offer_id}
    API->>DB: Fetch offer details
    DB-->>API: offer record
    API-->>User: 200 OK · {cashback_type, cashback_value, monthly_cap, start_date, end_date, status}
```

---

## Steps

| # | Action | Endpoint |
| --- | --- | --- |
| 1 | Register a new user account | `POST /api/v1/users` |
| 2 | Login with the new credentials | `POST /api/v1/auth/login` |
| 3 | Browse the list of currently active offers | `GET /api/v1/offers/active` |
| 4 | View the details of a specific offer | `GET /api/v1/offers/{offer_id}` |

## What to Expect

- The user account is created immediately and is active by default.
- The `offers/active` endpoint applies three filters automatically: the offer must be `active`, its merchant must be `active`, and today's date must fall within `[start_date, end_date]`.
- The offer listing is paginated. Use `page` and `page_size` query parameters to navigate.
- Offer details show whether cashback is a fixed amount (`fixed`) or a percentage (`percent`), the `cashback_value`, and the `monthly_cap` — the maximum cashback a user can earn from that offer in a calendar month.

---

_Back to [End-to-End Workflows](end-to-end-workflows.md)_
