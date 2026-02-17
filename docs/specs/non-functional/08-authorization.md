# NFR-08: Authorization & Access Control

## Overview

The system must enforce strict access control such that users can only access, modify, or view resources they own, preventing unauthorized access to other users' financial data or resources.

## Motivation

In a multi-tenant cashback system, users' financial data is sensitive. Unauthorized access to another user's wallet or transaction history is a critical security and privacy violation that could lead to regulatory fines and loss of trust.

## Definition

- Ownership checks are mandatory for all user-scoped resource endpoints (wallets, transactions, withdrawals).
- Access is denied with a 403 Forbidden error if the requesting user does not own the resource.
- All security checks are enforced at the API layer and in business logic, not just documentation.
- Ownership is verified from the authenticated user context, not from user-provided input.

## Acceptance Criteria

- GET /users/{user_id}/wallet returns 403 if the authenticated user is not {user_id}.
- List endpoints (GET /users/{user_id}/transactions) filter results to only the authenticated user's records.
- Test: Attempt to access another user's resource; receives 403 Forbidden.
- Test: Admin endpoints require appropriate role or permissions, not just user authentication.
- Audit logs record all access attempts, including denied ones.

## Technical Approach

- Extract authenticated user ID from JWT token or session context.
- Implement `require_ownership(user_id)` decorator or middleware on protected endpoints.
- Service layer verifies ownership before exposing data: `assert wallet.user_id == current_user.id`.
- Repository layer adds implicit ownership filter: `WHERE user_id = ?` for user-scoped queries.
- Never trust user-provided IDs; always filter by authenticated context.
- Integration tests verify both positive (owner access) and negative (non-owner access) scenarios.
