# ADR-013: Asynchronous Purchase Confirmation via Internal Event Broker

## Status

Accepted

## Context

In the initial implementation, purchase confirmation and cashback allocation were performed synchronously via an admin-triggered API endpoint. This tightly coupled the confirmation logic, cashback calculation, and wallet updates, making it difficult to simulate real-world settlement delays, external system checks, and event-driven extensibility.

## Decision

We will decouple purchase confirmation from cashback allocation by introducing an asynchronous, event-driven workflow:

- When a purchase is ingested, it remains in `pending` status.
- A periodic background job simulates bank reconciliation by checking for a matching bank movement (date, amount, merchant name). This job retries verification up to a configurable limit.
- If verification succeeds, the job publishes a `PurchaseConfirmed` event to an internal message broker.
- If verification fails after all retries, a `PurchaseRejected` event is published.
- A separate service subscribes to these events and is responsible for updating purchase status, invoking the cashback calculation engine, and updating wallet balances.
- The internal message broker is implemented as a simple in-memory pub/sub component under the `core` module, but is designed for future replacement with a distributed broker if needed.

## Consequences

- **Separation of concerns:** Verification, confirmation, and reward allocation are handled by distinct components.
- **Security:** Only the background job (trusted system process) can trigger confirmation, reducing risk of privilege escalation or accidental confirmation.
- **Extensibility:** Other modules (e.g., notifications, analytics) can subscribe to confirmation/rejection events without modifying core logic.
- **Realism:** The workflow simulates real-world settlement delays and reconciliation, improving the fidelity of the demo system.
- **Testability:** Each component can be tested in isolation, and event flows can be simulated in integration tests.

## Alternatives Considered

- Keeping synchronous confirmation via admin endpoint (rejected: less realistic, tightly coupled, harder to extend).
- Using an external message broker (rejected for now: unnecessary operational complexity at current scale).

## References

- [Product Overview](../../specs/product-overview.md)
- [PU-02: Purchase Confirmation](../../specs/functional/purchases/PU-02-purchase-confirmation.md)
- [PU-03: Purchase Cashback Calculation](../../specs/functional/purchases/PU-03-purchase-cashback-calculation.md)
