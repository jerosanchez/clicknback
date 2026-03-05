# ClickNBack — End-to-End Workflows

> **Purpose:** This document describes the main business flows in ClickNBack from a user perspective. It is written for recruiters, hiring managers, and developers who want to understand the domain quickly and manually explore the system without reading all the technical specs.
>
> **Companion files:** Each workflow has its own document (linked below) with full steps, business rules, and a Mermaid sequence diagram. Ready-to-run `.http` request sequences live in [`http/`](http/) and target the live API at `https://clicknback.com`.

---

## Business Context (30-second summary)

ClickNBack is a cashback platform. Users earn a percentage (or fixed amount) back on purchases made at partner merchants. The life cycle goes like this:

1. An **admin** sets up and activates **merchants** and **offers** (cashback rules tied to a merchant and a date range).
2. A **user** registers, browses active offers, and shops at a participating merchant.
3. An **external system** (a merchant's point-of-sale or e-commerce platform) pushes a **purchase event** via webhook — the system records it as `pending`.
4. The purchase is **confirmed** (either automatically or by an admin), at which point cashback is calculated and credited to the user's **wallet** as `pending` balance.
5. Once enough confirmations accumulate, the user requests a **payout** (withdrawal). An admin processes it and the funds move from `pending` to `paid`.

---

## Roles

| Role | Description |
| --- | --- |
| **Anonymous** | Not authenticated. Can register and nothing else. |
| **User** | A registered customer. Can browse offers, view their purchases, check their wallet, and request payouts. |
| **Admin** | A platform operator. Can do everything a user can, plus manage merchants and offers, and process payouts. |

Demo admin credentials for the live environment: `carol@clicknback.com` / `Str0ng!Pass`

---

## Workflow 1 — Admin Platform Setup

An admin creates and activates a merchant, then attaches and activates a cashback offer. After this workflow the platform is ready for users to earn cashback.

→ **[Full details and sequence diagram](01-admin-platform-setup.md)** · HTTP file: [`http/01-admin-platform-setup.http`](http/01-admin-platform-setup.http)

---

## Workflow 2 — User Registration and Offer Discovery

A new user registers, logs in, and browses the currently active cashback offers. Requires at least one active merchant with an active offer (Workflow 1).

→ **[Full details and sequence diagram](02-user-discovery.md)** · HTTP file: [`http/02-user-discovery.http`](http/02-user-discovery.http)

---

## Workflow 3 — Purchase Ingestion and Cashback Calculation ⚪

An external merchant system pushes a purchase event via webhook. An admin confirms it, triggering cashback calculation capped by the offer's monthly limit. The user can then view the credited cashback in their purchase history.

→ **[Full details and sequence diagram](03-purchase-and-cashback.md)** · HTTP file: [`http/03-purchase-and-cashback.http`](http/03-purchase-and-cashback.http)

---

## Workflow 4 — Wallet and Payout ⚪

A user checks their wallet balances, requests a withdrawal, and an admin approves or rejects it. On approval the funds move to the `paid` bucket; on rejection they return to `available`.

→ **[Full details and sequence diagram](04-wallet-and-payout.md)** · HTTP file: [`http/04-wallet-and-payout.http`](http/04-wallet-and-payout.http)

---

## Quick Reference — All Endpoints

| Method | Path | Role | Description |
| --- | --- | --- | --- |
| `POST` | `/api/v1/users` | Anonymous | Register a new user |
| `POST` | `/api/v1/auth/login` | Anonymous | Log in, get JWT token |
| `POST` | `/api/v1/merchants` | Admin | Create a merchant |
| `GET` | `/api/v1/merchants` | Admin | List merchants (paginated, filterable) |
| `PATCH` | `/api/v1/merchants/{id}/status` | Admin | Activate or deactivate a merchant |
| `POST` | `/api/v1/offers` | Admin | Create an offer for a merchant |
| `GET` | `/api/v1/offers` | Admin | List all offers (paginated) |
| `GET` | `/api/v1/offers/active` | User / Admin | List currently active public offers |
| `GET` | `/api/v1/offers/{id}` | User / Admin | Get offer details |
| `PATCH` | `/api/v1/offers/{id}/status` | Admin | Activate or deactivate an offer |
| `POST` | `/api/v1/purchases` ⚪ | Admin / System | Ingest a purchase (webhook) |
| `POST` | `/api/v1/purchases/{id}/confirm` ⚪ | Admin | Confirm a purchase |
| `GET` | `/api/v1/purchases/{id}` ⚪ | Admin | Get purchase details |
| `GET` | `/api/v1/purchases` ⚪ | Admin | List all purchases |
| `GET` | `/api/v1/users/{id}/purchases` ⚪ | User / Admin | List purchases for a user |
| `POST` | `/api/v1/purchases/{id}/reverse` ⚪ | Admin | Reverse a purchase |
| `GET` | `/api/v1/users/{id}/wallet` ⚪ | User / Admin | Get wallet summary |
| `GET` | `/api/v1/users/{id}/wallet/transactions` ⚪ | User / Admin | List wallet transactions |
| `POST` | `/api/v1/users/{id}/payouts` ⚪ | User | Request a payout |
| `GET` | `/api/v1/payouts` ⚪ | Admin | List all payouts |
| `PATCH` | `/api/v1/payouts/{id}/status` ⚪ | Admin | Process a payout |
| `GET` | `/api/v1/users/{id}/payouts` ⚪ | User / Admin | List payouts for a user |

_⚪ = backlog: specified but not yet implemented._

---

## Error Response Shape

All errors share a consistent envelope:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Human-readable description of the problem.",
    "details": {}
  }
}
```

Common codes: `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `BUSINESS_RULE_VIOLATION`, `INTERNAL_SERVER_ERROR`.

---

_See also: [Domain Glossary](../domain-glossary.md) · [Product Overview](../product-overview.md) · [Functional Specs](../functional/) · [API Contracts](../../design/api-contracts/)_
