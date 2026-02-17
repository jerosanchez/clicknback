# NFR-11: Performance & Responsiveness

## Overview

The system must respond to user requests within defined latency targets, ensuring a responsive user experience and efficient resource utilization across various load conditions.

## Motivation

Slow responses frustrate users and reduce engagement. Performance is a feature. Meeting latency targets ensures the system scales efficiently and justifies cost of infrastructure.

## Definition

- API endpoints meet defined latency targets (e.g., p95 < 200ms for read endpoints, p95 < 500ms for write endpoints).
- Database queries are optimized with proper indexes and minimal N+1 queries.
- In-memory caching reduces database load for frequently accessed data.
- Load testing verifies performance under expected and peak traffic.

## Acceptance Criteria

- Response time for GET /users/{id}/wallet is p95 < 100ms.
- Response time for POST /users/{id}/wallet/withdraw is p95 < 500ms.
- Database indexes are analyzed; no sequential scans on hot tables in production.
- Load test: 1000 concurrent users maintain p95 < 500ms for read operations.
- Caching strategy is documented: what is cached, TTL, invalidation logic.

## Technical Approach

- Use database indexes on frequently filtered/sorted columns: `CREATE INDEX idx_wallets_user_id ON wallets(user_id)`.
- Implement caching at multiple layers: HTTP cache headers, repository layer (e.g., Redis), computed result caching.
- Add query profiling/analysis to CI/CD: detect N+1 queries before merge.
- Use PostgreSQL EXPLAIN ANALYZE for query optimization.
- Implement pagination (see NFR-07) to prevent large result sets.
- Load testing framework (e.g., Locust, JMeter) to verify performance targets.
- APM (Application Performance Monitoring) tool to identify bottlenecks in production.
