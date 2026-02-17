# NFR-07: Pagination & Listing Performance

## Overview

The system must support pagination on all list endpoints to handle large datasets efficiently, preventing memory exhaustion and ensuring responsive user experience even with millions of records.

## Motivation

As data grows, returning all records in a single response is infeasible. Pagination allows clients to retrieve data in manageable chunks. Without it, the API can become slow, memory-intensive, and difficult to use.

## Definition

- All list endpoints must support `limit` and `offset` parameters (or cursor-based pagination).
- Responses include metadata: `total_count`, `page_number`, `page_size`, `has_more`.
- Default page size is reasonable (e.g., 20 items); maximum is capped (e.g., 100 items).
- Sorting is supported on common fields with a consistent sort syntax.

## Acceptance Criteria

- GET /users?limit=20&offset=0 returns paginated results with metadata.
- Requesting `offset=0&limit=100` returns at most 100 records (hard cap).
- Request for out-of-bounds page returns empty result set with appropriate metadata.
- Performance test: fetching a single page takes <200ms even with 10M records.
- Cursor-based pagination (if used) is documented and tested for stability across data mutations.

## Technical Approach

- Implement pagination at the repository layer using `LIMIT` and `OFFSET` SQL clauses.
- Create a reusable `PaginationParams` schema and `paginate()` utility function.
- Return `PaginatedResponse[T]` schema with `items`, `total_count`, `limit`, `offset`.
- Add database indexes on commonly sorted columns (e.g., created_at, status).
- Use cursor-based pagination for extremely large datasets or real-time feeds.
- Load tests verify no N+1 queries or missing indexes degrade performance.
