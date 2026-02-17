# NFR-10: Logging & Observability

## Overview

The system must maintain comprehensive, structured logs of all significant operations—especially financial transactions—to enable debugging, auditing, compliance, and performance monitoring.

## Motivation

In a financial system, logs are essential for regulatory compliance, fraud detection, and incident investigation. Unstructured or incomplete logs make debugging difficult and can result in compliance violations. Observability enables proactive monitoring of system health.

## Definition

- All financial transactions, state changes, and errors are logged with structured data (JSON format).
- Logs include context: user ID, request ID, operation, timestamp, duration, outcome.
- Log levels are used appropriately: INFO (business events), WARN (recoverable issues), ERROR (failures).
- Logs are centralized and searchable; retention follows compliance requirements (e.g., 7 years for financial records).

## Acceptance Criteria

- Every wallet debit/credit operation logs: user_id, amount, reason, balance_before, balance_after, timestamp.
- Every API request logs: method, path, status_code, duration_ms, user_id, error (if any).
- Logs are structured JSON with consistent field names and types.
- Log aggregation tool (e.g., ELK, CloudWatch) is configured and accessible.
- Logs are retained for at least 1 year; financial transaction logs for 7 years.

## Technical Approach

- Use structured logging library: `structlog` or `python-json-logger`.
- Configure logging with JSON output to stdout; container/logging agent handles centralization.
- Add request ID (UUID) to all logs within a request scope for tracing.
- Implement middleware to log request/response for all API calls.
- Create domain-specific loggers: `transaction_logger`, `audit_logger`, `error_logger`.
- Metrics/monitoring: use Prometheus or StatsD for counters, gauges, histograms.
- Alerts trigger on error rate >5%, P95 latency >1s, or zero transactions in 5 minutes.
