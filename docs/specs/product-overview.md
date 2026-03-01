# ClickNBack – Product Overview

## 1. Purpose

**ClickNBack** is a simplified cashback platform backend that models how modern cashback applications operate in production.

The system allows:

- Users to earn cashback on purchases made at partner merchants
- Merchants to define cashback offers and promotional campaigns
- The platform to track purchases, calculate rewards, manage pending/confirmed balances, and process withdrawals
- Administrators to monitor usage, enforce rules, and prevent abuse

The primary goal of ClickNBack is to simulate a **real-world financial incentive system** with correctness, concurrency, idempotency, and fraud-awareness constraints.

It is intentionally designed as a compact but deep backend system to explore advanced backend concepts in a realistic domain.

---

## 2. Business Context & Justification

Cashback products are compelling demo systems because they combine:

- Financial correctness requirements
- Event ingestion
- Fraud prevention logic
- State transitions
- Concurrency-sensitive balance updates
- Reporting and analytics
- Role-based access control

Unlike generic CRUD applications, cashback systems must:

- Prevent double rewards
- Handle asynchronous confirmations
- Enforce caps and limits
- Maintain consistent wallet balances under concurrent access
- Support auditability

This makes ClickNBack a strong demonstration of production-grade backend engineering in a domain that is:

- Commercially relevant
- Product-driven
- Technically non-trivial

---

## 3. Core Domain Concepts

### Users

Individuals who register in the system and earn cashback from purchases.

### Merchants

Partner businesses offering cashback incentives.

### Offers

Time-bound or merchant-specific reward rules that define:

- Cashback percentage or fixed amount
- Validity period
- Monthly caps per user

### Purchases

Events representing a user transaction at a merchant.
Purchases enter the system as external events (e.g., webhook ingestion).

### Cashback Transactions

Internal reward records generated from purchases.
These track state changes independently from purchase state.

### Wallet

A financial abstraction tracking:

- Pending balance
- Available balance
- Paid balance

Wallet integrity is critical and must remain consistent under concurrent operations.

---

## 4. Main System Flows

### 4.1 User Registration

#### Registration

1. User registers with email/password.
2. Password is securely hashed.

#### Authentication (Login)

1. User authenticates with email/password.
2. System validates credentials and issues JWT for authenticated requests.
3. JWT includes expiration and role claims.

#### Role-based Access Control

- Regular users
- Admin users

Security considerations:

- Password hashing (bcrypt/argon2)
- JWT expiration
- Role enforcement in endpoints

---

### 4.2 Merchant & Offer Creation (Admin Flow)

1. Admin creates a merchant.
2. Admin defines cashback offers:
   - Percentage or fixed reward
   - Time validity window
   - Optional per-user monthly cap

Business rules:

- Only one active offer per merchant at a time (optional constraint).
- Offers cannot overlap unless explicitly allowed.

---

### 4.3 Purchase Ingestion (Core Flow)

Purchases enter the system via an API endpoint simulating external tracking (e.g., affiliate webhook).

Request includes:

- External purchase ID (idempotency key)
- User ID
- Merchant ID
- Amount
- Currency

Processing steps:

1. Validate idempotency (unique external ID).
2. Validate merchant and active offer.
3. Calculate cashback.
4. Create:
   - Purchase record (status = pending)
   - Cashback transaction (status = pending)
5. Increase user's pending wallet balance.

Important concerns:

- Database-level uniqueness constraint on external purchase ID.
- Use Decimal for monetary precision.
- All updates happen inside a transaction.

---

### 4.4 Cashback Calculation Engine

Rules:

- If offer has percentage → cashback = amount * percentage.
- If fixed amount → use fixed.
- Apply monthly cap per user.
- Enforce minimum/maximum limits if defined.

Design considerations:

- Calculation logic isolated in a service layer.
- Deterministic rounding strategy.
- Clear audit trail.

---

### 4.5 Pending → Confirmed Flow

Cashback is not immediately withdrawable.

State transitions:

**Purchase:**

- pending → confirmed
- pending → reversed

**Cashback Transaction:**

- pending → available
- pending → reversed

When confirmed:

- Decrease pending balance.
- Increase available balance.

When reversed:

- Remove pending reward.
- Prevent future confirmation.

This simulates real-world merchant settlement delays.

---

### 4.6 Withdrawal Flow

User requests withdrawal of available balance.

Steps:

1. Validate sufficient available balance.
2. Lock wallet row.
3. Deduct available balance.
4. Increase paid balance.
5. Create payout record.

Concurrency considerations:

- Prevent double withdrawal.
- Use:
  - SELECT FOR UPDATE
  - or Optimistic locking with version field.

---

### 4.7 Reversal Handling

If a purchase is later canceled:

1. Mark purchase as reversed.
2. Reverse cashback transaction.
3. Adjust wallet balances accordingly.

Must handle:

- Reversal after confirmation.
- Reversal during pending state.

---

## 5. Concurrency & Consistency Model

Critical sections:

- Purchase ingestion
- Cashback confirmation
- Withdrawal requests

Strategies:

- Use database transactions.
- Enforce uniqueness at DB level.
- Use row-level locking for wallet updates.
- Ensure idempotent operations.

Goal:
No scenario should result in inconsistent wallet balances.

---

## 6. Anti-Fraud & Abuse Prevention

ClickNBack includes basic anti-abuse mechanisms:

- Idempotency enforcement.
- Rate limiting purchase ingestion.
- Monthly cap enforcement.
- Duplicate detection via external purchase ID.
- Suspicious behavior flags (optional extension).

Fraud awareness is a core design goal.

---

## 7. Observability & Auditability

Financial systems require traceability.

ClickNBack includes:

- Structured logging
- Request ID correlation
- Logging of state transitions
- Explicit recording of all wallet changes

Design principle:
Every financial change must be explainable.

---

## 8. Scalability Considerations

The system is designed as a stateless API service.

Potential scaling strategies:

- Horizontal scaling of API nodes.
- Redis-backed rate limiter.
- Message queue for asynchronous confirmations.
- Read replicas for reporting.
- Partitioning by user ID for large-scale deployment.

The initial implementation is monolithic but structured for extensibility.

---

## 9. Architectural Principles

- Layered architecture (API → Service → Repository → DB).
- Business logic isolated from HTTP layer.
- Database as source of truth.
- Strict financial correctness over premature optimization.
- Explicit state machines for clarity.

---

## 10. Technical Focus Areas Demonstrated

This project intentionally explores:

- Idempotency patterns
- Transaction management
- Row-level locking
- Optimistic concurrency control
- Monetary precision handling
- State machine modeling
- Role-based authorization
- Background job simulation
- Reporting and aggregation queries
- Observability patterns

---

## 11. Non-Goals

To keep scope realistic:

- No real payment provider integration.
- No external affiliate APIs.
- No real banking transfers.
- No distributed microservices.

The focus is backend correctness and domain modeling.

---

## 12. Why ClickNBack is a Strong Backend Demonstration

ClickNBack models a financially sensitive, event-driven, concurrency-aware domain within a compact system.

It demonstrates:

- Product alignment
- Domain-driven thinking
- Backend maturity
- Real-world trade-off awareness
- Production-grade concerns in a contained project

It is intentionally small in surface area but deep in engineering rigor.
