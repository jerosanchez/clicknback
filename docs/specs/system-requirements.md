# System Requirements Index

This document provides a unified overview of all system requirements for the ClicknBack cashback backend system, combining functional requirements (FRs) and non-functional requirements (NFRs). It serves as both a comprehensive reference and an index for easy navigation to each requirement.

---

## Overview

The system requirements are organized into two complementary domains:

- **Functional Requirements (FRs)**: Define what the system should do in terms of features, workflows, and user capabilities across 6 domain areas.
- **Non-Functional Requirements (NFRs)**: Define how the system should behave in terms of reliability, performance, security, and operational aspects across 12 key areas.

Together, these requirements ensure ClicknBack operates as a production-grade financial backend serving merchants, offers, purchases, payouts, users, and wallets.

---

## Functional Requirements (FRs)

FRs are organized into 6 domain areas covering merchants, offers, payouts, purchases, users, and wallets. Each FR includes clear user stories, constraints, acceptance criteria, and use cases. FRs are identified with a domain prefix (M, O, PA, PU, U, W) for easy reference.

### User Management (2 FRs)

- **[U-01: User Registration](functional/users/U-01-user-registration.md)** — New users can create accounts with email and secure passwords meeting complexity requirements.
- **[U-02: User Login](functional/users/U-02-user-authentication.md)** — Registered users can authenticate with credentials and receive JWT tokens for platform access.

### Merchant Management (3 FRs)

- **[M-01: Merchant Creation](functional/merchants/M-01-merchant-creation.md)** — Admin users can register new merchants and define their details in the system.
- **[M-02: Merchant Activation](functional/merchants/M-02-merchant-activation.md)** — Admin users can toggle merchant availability status to control active promotions.
- **[M-03: Merchants Listing](functional/merchants/M-03-merchants-listing.md)** — Admin users can view paginated lists of all merchants with filtering and sorting options.

### Offer Management (5 FRs)

- **[O-01: Offer Creation](functional/offers/O-01-offer-creation.md)** — Admin users can create cashback offers for active merchants with terms including amount, dates, and monthly caps.
- **[O-02: Offer Activation](functional/offers/O-02-offer-activation.md)** — Admin users can toggle offer availability status without deletion.
- **[O-03: Offer Details View](functional/offers/O-03-offer-details-view.md)** — Authenticated users can view detailed information about specific active offers.
- **[O-04: Active Offers Listing](functional/offers/O-04-active-offers-listing.md)** — Authenticated users can discover available cashback offers currently active within valid time windows.
- **[O-05: Offers Listing](functional/offers/O-05-offers-listing.md)** — Admin users can view paginated lists of all offers with status and management options.

### Purchase Management (7 FRs)

- **[PU-01: Purchase Ingestion](functional/purchases/PU-01-purchase-ingestion.md)** — External systems can record user purchases via webhook with idempotent external IDs.
- **[PU-02: Purchase Confirmation](functional/purchases/PU-02-purchase-confirmation.md)** — Admin users can confirm pending purchases and release cashback to available balances.
- **[PU-03: Purchase Cashback Calculation](functional/purchases/PU-03-purchase-cashback-calculation.md)** — System automatically calculates and allocates cashback based on active offers, respecting monthly caps.
- **[PU-04: Purchase Details View](functional/purchases/PU-04-purchase-details-view.md)** — Users can view detailed information about their purchases including cashback status.
- **[PU-05: Purchases Listing (Admin)](functional/purchases/PU-05-purchases-listing.md)** — Admin users can view paginated, filterable lists of all purchases across users.
- **[PU-06: List User Purchases](functional/purchases/PU-06-list-user-purchases.md)** — Users can view their purchase history with associated cashback information.
- **[PU-07: Purchase Cancellation](functional/purchases/PU-07-reverse-purchase.md)** — Admin users can reverse/cancel purchases and adjust associated cashback allocations.

### Payout Management (4 FRs)

- **[PA-01: Payout Request](functional/payouts/PA-01-payout-request.md)** — Authenticated users can request withdrawals of available cashback subject to policy constraints.
- **[PA-02: Payout Processing](functional/payouts/PA-02-payout-processing.md)** — Admin users can process payout requests by completing or failing them with appropriate wallet adjustments.
- **[PA-03: Payouts Listing (Admin)](functional/payouts/PA-03-payouts-listing.md)** — Admin users can view paginated, filterable lists of all payouts across users.
- **[PA-04: User Payouts Listing](functional/payouts/PA-04-user-payouts-listing.md)** — Users can audit their payout history with statuses and amounts.

### Wallet Management (2 FRs)

- **[W-01: Wallet Summary View](functional/wallets/W-01-wallet-summary-view.md)** — Users can view their wallet balances: pending, available, and paid amounts.
- **[W-02: Wallet Transactions Listing](functional/wallets/W-02-wallet-transactions-listing.md)** — Users can audit paginated wallet transaction history including credits, reversals, and payouts.

### FR Key Relationships & User Journeys

#### New User Onboarding

Users enter the system through **U-01** (registration) and gain access via **U-02** (login). They then typically navigate to **W-01** (wallet summary) to understand their current state.

#### Discovering & Making Purchases

Authenticated users view active offers through **O-04**, check offer details with **O-03**, and eventually their purchases appear through **PU-06** (user purchase list).

#### Purchase Fulfillment Workflow

When external systems ingest purchases (**PU-01**), the system:

1. Records the purchase (idempotent via external_id)
2. Calculates cashback (**PU-03**) respecting offer terms and monthly caps
3. Awaits admin confirmation via **PU-02** to release funds
4. Updates wallet transactions reflecting the cashback credit

#### Admin Lifecycle Management

Admins manage the ecosystem:

- **Merchants**: Create (**M-01**) → Activate/Deactivate (**M-02**) → Monitor (**M-03**)
- **Offers**: Create (**O-01**) → Activate/Deactivate (**O-02**) → Monitor (**O-05**)
- **Purchases**: Confirm (**PU-02**) → Reverse if needed (**PU-07**) → Monitor (**PU-05**)
- **Payouts**: Process (**PA-02**) → Monitor (**PA-03**)

#### User Withdrawal Flow

Users initiate withdrawals via **PA-01** (payout request), and admins process them with **PA-02** (payout processing). Users track their history with **PA-04** (user payouts listing).

### FR Coverage Alignment

#### User Roles & Authorization

- **Anonymous**: Can only call U-01 (registration)
- **Authenticated User**: Can access U-02, O-03, O-04, PU-04, PU-06, PA-01, PA-04, W-01, W-02
- **Admin**: Full access to all FRs including M-*, O-*, PU-*, PA-*, and respective listing endpoints

#### Data Flows

- Purchase flow (**PU-01** → **PU-03** → **PU-02**) ensures atomic cashback allocation
- Wallet consistency across **PA-01**, **PA-02**, **PU-02**, **PU-03**, **PU-07** relies on database transactions and state machine validation
- All listing endpoints (**M-03, O-05, PA-03, PA-04, PU-05, PU-06, W-02**) support pagination and filtering

---

## Non-Functional Requirements (NFRs)

NFRs define how the system should behave in terms of reliability, performance, security, and operational aspects. They are organized into 12 key areas, each with clear definitions, acceptance criteria, and technical approaches suitable for a production cashback backend.

### Data & Financial Quality

- **[NFR-01: Data Integrity](non-functional/01-data-integrity.md)** — Database-level constraints ensure no duplicate emails or invalid states corrupt the system.
- **[NFR-03: Financial Precision](non-functional/03-financial-precision.md)** — Use Decimal arithmetic to prevent rounding errors in monetary calculations.

### Reliability & Consistency

- **[NFR-02: Idempotency](non-functional/02-idempotency.md)** — Retryable operations (especially purchase ingestion) produce consistent results across multiple calls.
- **[NFR-04: Transactionality](non-functional/04-transactionality.md)** — Atomic transactions ensure wallet updates cannot leave the system in an inconsistent state.
- **[NFR-05: Concurrency Safety](non-functional/05-concurrency-safety.md)** — Concurrent operations on shared resources are handled safely without race conditions or oversending.

### Business Logic & Security

- **[NFR-06: State Management & Validation](non-functional/06-state-management.md)** — State machines enforce valid business logic transitions for wallets, transactions, and withdrawal requests.
- **[NFR-08: Authorization & Access Control](non-functional/08-authorization.md)** — Users can only access and modify resources they own; owner checks are enforced at API and business logic layers.

### Scalability & User Experience

- **[NFR-07: Pagination & Listing Performance](non-functional/07-pagination.md)** — All list endpoints support pagination to handle large datasets and ensure responsive performance.
- **[NFR-11: Performance & Responsiveness](non-functional/11-performance.md)** — Response times meet defined SLAs (e.g., p95 < 200ms for reads).

### Operational Excellence

- **[NFR-09: Error Handling & Recovery](non-functional/09-error-handling.md)** — Graceful error handling with standardized responses and automatic retry mechanisms for transient failures.
- **[NFR-10: Logging & Observability](non-functional/10-logging-observability.md)** — Structured logs enable auditing, compliance, and debugging; all financial transactions are logged.
- **[NFR-12: Data Backup & Disaster Recovery](non-functional/12-backup-recovery.md)** — Automated backups with recovery procedures ensure data is never permanently lost.

### NFR Key Relationships

These NFRs are interconnected and collectively form a cohesive quality framework:

- **Financial Precision** (NFR-03) ensures the fundamental trust in calculations.
- **Data Integrity** (NFR-01) + **Transactionality** (NFR-04) + **Concurrency Safety** (NFR-05) form the backbone of a reliable financial system.
- **Idempotency** (NFR-02) protects against network retry issues in error scenarios (NFR-09).
- **Logging & Observability** (NFR-10) enables verification that all other NFRs are met in production.
- **Backup & Recovery** (NFR-12) is the final safety net; combined with error handling (NFR-09), ensures no data loss.

### NFR Compliance & Standards

These NFRs align with industry standards for financial software:

- **SOC 2 Type II**: Logging (NFR-10), Access Control (NFR-08), Backup (NFR-12), Error Handling (NFR-09).
- **PCI DSS**: Authorization (NFR-08), Logging (NFR-10), Data Integrity (NFR-01).
- **ACID Compliance**: Transactionality (NFR-04), Concurrency Safety (NFR-05), Data Integrity (NFR-01).

---

## Implementation Priority

For a demo/MVP, FRs and NFRs should be prioritized together to ensure a cohesive delivery:

### Phase 1 (Essential Foundation)

**FRs**: U-01, U-02, W-01  
**NFRs**: NFR-01, NFR-03, NFR-04, NFR-05, NFR-08  
**Goal**: Core user authentication and wallet infrastructure with financial integrity.

### Phase 2 (Merchant & Offer Ecosystem)

**FRs**: M-01, O-01, O-04, O-03, M-02, M-03, O-05  
**NFRs**: NFR-02, NFR-06, NFR-09  
**Goal**: Enable admin control and user discovery of merchant offers with operational robustness.

### Phase 3 (Purchase & Cashback Processing)

**FRs**: PU-01, PU-03, PU-02, PU-06, PU-04, PU-05, PU-07  
**NFRs**: NFR-07, NFR-10, NFR-11  
**Goal**: Ingest purchases, calculate cashback atomically, and provide comprehensive purchase history with scalability.

### Phase 4 (Payouts & Production Readiness)

**FRs**: PA-01, PA-02, PA-03, PA-04, W-02  
**NFRs**: NFR-12  
**Goal**: Enable user withdrawals and complete observability with backup/recovery capabilities.

---

## System-Wide Quality Framework

The integration of FRs and NFRs creates a comprehensive quality framework:

### Financial Reliability

- FRs (**PU-01**, **PU-03**, **PU-02**) define purchase and cashback workflows.
- NFRs (**NFR-01**, **NFR-03**, **NFR-04**, **NFR-05**) ensure these workflows execute with financial precision and consistency.

### User Experience & Scalability

- FRs (**O-04**, **PU-06**, **W-01**, **W-02**) provide user-facing data retrieval.
- NFRs (**NFR-07**, **NFR-11**) ensure these operations remain responsive at scale.

### Security & Compliance

- FRs (**U-02**, **PA-01**) define access points and sensitive operations.
- NFRs (**NFR-08**, **NFR-10**) enforce authorization and auditable logging.

### Operational Resilience

- FRs (**PU-01**, **PA-02**) define critical business operations.
- NFRs (**NFR-02**, **NFR-09**, **NFR-12**) ensure graceful handling of failures and data recovery.

---

## Related Documents

- [Architecture Overview](../design/architecture-overview.md)
- [Error Handling Strategy](../design/error-handling-strategy.md)
- [Security Strategy](../design/security-strategy.md)
- [Testing Strategy](../design/testing-strategy.md)
- [Product Overview](product-overview.md)
- [Domain Glossary](domain-glossary.md)
