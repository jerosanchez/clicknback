# ADR-020: Use `/users/me` Prefix for Authenticated-User Self-Resource Endpoints

**Date:** 2026-03-14
**Status:** Accepted

---

## Context

Some API endpoints return resources that are specific to the currently authenticated user, such as listing a user's own purchases or profile information. For these endpoints, it is important to:

1. **Maintain semantic clarity.** Path segments should clearly indicate whether a resource is globally addressable (e.g., by ID) or contextually resolved based on the authenticated user. Endpoints for self-resources should avoid ambiguous or overloaded path segments.

2. **Align with industry conventions.** Major public APIs (e.g., GitHub, Stripe, Google APIs, Microsoft Graph) use a special `me` (or `self`) segment under a `/users` base path to represent the authenticated caller. This convention is widely recognized and immediately understood by developers, recruiters, and code reviewers.

3. **Enable extensibility and consistency.** Using a `/users/me` prefix establishes a clear, extensible pattern for all endpoints that operate on the authenticated user's resources, making the API easier to understand and maintain.

## Decision

All endpoints that operate on resources belonging to the currently authenticated user
are placed under the `/users/me` prefix:

```http
GET /users/me/purchases    # list the caller's own purchases
```

Future self-resource endpoints follow the same pattern:

```http
GET  /users/me/profile
GET  /users/me/cashback-balance
POST /users/me/notifications/read
```

### Implementation

A dedicated `users_router = APIRouter(prefix="/users")` is defined in
`app/purchases/api/public.py` (and can be extended to other modules). This router is
exported from `app/purchases/api/__init__.py` and registered in `app/main.py` alongside
the existing `/purchases` router. The handler function and all service/repository logic
remain unchanged — only the path changes.

### Routing note

Because `/purchases/{purchase_id}` and `/users/me/purchases` live on different router
prefixes, there is no ambiguity risk between the two routes. FastAPI resolves them on
distinct prefixes before any path-parameter matching occurs.

## Consequences

**Positive**:

- Path intent is unambiguous: `me` is a universally recognised placeholder for "the
  authenticated user".
- Easier to onboard new developers and passes a quick readability check for technical
  interviewers reviewing the codebase.
- Establishes a clear, extensible convention for all future self-resource endpoints.

**Negative / trade-offs**:

- The endpoint crosses module boundaries at the path level: a "users" path prefix is
  served by handler logic that lives in the `purchases` module. This is a minor
  cosmetic inconsistency but is preferable to duplicating the handler or creating an
  artificial `users` module just to host a thin proxy.
- Any external clients or documentation that referenced `GET /purchases/mine` must be
  updated. There are no known external integrations at this stage of the MVP, so the
  migration cost is zero.

## Alternatives Considered

| Path | Reason rejected |
| --- | --- |
| `GET /purchases/mine` | `mine` is non-standard; feels idiomatic English but not REST. |
| `GET /purchases?owner=me` | Conflates filtering with ownership context; unusual. |
| `GET /users/{userId}/purchases` | Requires an explicit ID in the path; does not express "caller's own". |
| `GET /me/purchases` | Valid shorthand used by some APIs (GitHub uses `/user`). Rejected in favour of the more explicit `/users/me` hierarchy, which is consistent with the existing `/users` router in this codebase. |
