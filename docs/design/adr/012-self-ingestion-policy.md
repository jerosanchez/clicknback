# ADR 012: Restrict Purchase Ingestion to Self (Self-Ingestion Policy)

## Status

Accepted

## Context

The purchase ingestion endpoint (`POST /purchases`) requires a `user_id` in the request
body so that the system can associate the purchase with a specific user account and resolve
the correct cashback offer. The original design anticipated an external-system model where
a trusted third party (e.g. a merchant's payment gateway or a data pipeline) would submit
purchases on behalf of any user, providing the `user_id` in the payload.

This design has two practical problems for the MVP:

### Security: User Enumeration Risk

When any authenticated user can submit a purchase for an arbitrary `user_id`, the error
responses inadvertently become an oracle for probing account existence:

- If `user_id` doesn't exist → `USER_NOT_ELIGIBLE` (404-style semantic)
- If `user_id` exists but is inactive → `USER_NOT_ELIGIBLE` (activation status leak)
- If everything is valid → 201 Created (confirms user existence + activity)

Even though the responses are consistent at the HTTP status code level, the fact that the
caller controls an arbitrary `user_id` creates a surface for systematic account enumeration.
A legitimate user should only ever be able to act on their own account.

### Product Model Mismatch

The MVP targets individual users recording their own purchases through a client application
(mobile or web). The external-system webhook model is a valid future extension — for example,
when a merchant partner wants to push transactions server-to-server — but it is **not**
the primary flow for the MVP and adds complexity (trust model, API key management, role
segregation) that is out of scope right now.

Removing `user_id` from the request body entirely would close the door to external
systems without significant rework, since any future integration would need `user_id`
back in the payload. Keeping `user_id` in the body but enforcing that it must equal the
authenticated caller preserves the schema contract and makes the external-system upgrade
path straightforward: grant the external caller a broader role that is exempt from the
ownership check.

## Decision

Add a **self-ingestion policy** enforced at the service layer that requires the `user_id`
in the request body to match the authenticated user's ID. This policy:

- Lives in `app/purchases/policies.py` as `enforce_purchase_ownership`, following the
  same callable-injection pattern used for all other purchase policies (see ADR 004).
- Is invoked as the **first check** in `PurchaseService.ingest_purchase`, before duplicate
  detection and before any downstream lookups, so that unauthorized requests fail fast
  without triggering unnecessary database work or leaking information about existing records.
- Raises `PurchaseOwnershipViolationException` when the IDs do not match, which the API
  layer maps to a `403 Forbidden` response.

`user_id` is kept in the request body (not removed). This preserves the client's explicit
intent (the user says "I am making this purchase") and keeps the door open for a future
trusted-system role that bypasses the ownership check without changing the API schema.

## Future Extension Path

When external-system ingestion is required, the path is:

1. Introduce a new role (e.g. `service_account` or `webhook`) with a distinct
   `get_current_service_account` dependency.
2. The composition root wires a permissive no-op callable as `enforce_purchase_ownership`
   for service-account-authenticated requests, or bypasses the check via a dedicated
   service-level flag.
3. No schema changes are needed.

## Consequences

### Positive

- Eliminates the user-enumeration surface introduced by arbitrary `user_id` ingestion.
- Aligns the product behaviour with the MVP model (users recording their own purchases).
- Follows the existing policy injection pattern — no new architectural patterns introduced.
- The `user_id` field is preserved in the schema, keeping the external-system upgrade
  path open without any breaking changes.

### Negative / Trade-offs

- Any future external-system ingestion will require a dedicated role and service-level
  plumbing to bypass the ownership check. This is a deliberate deferral.
- A user cannot delegate purchase ingestion to another party (e.g. a shared household
  account submitting on behalf of a sub-user). Multi-user delegation is out of scope
  for the MVP.

## Related

- ADR 004 — Use Callable Injection for Stateless Dependencies (policy injection pattern)
- PU-01 — Purchase Ingestion functional spec
- `app/purchases/policies.py` — `enforce_purchase_ownership`
- `app/purchases/exceptions.py` — `PurchaseOwnershipViolationException`
