# NFR-03: Financial Precision

## Overview

The system must use fixed-precision decimal arithmetic (not floating-point) for all monetary calculations to prevent accumulated rounding errors and ensure accurate financial reporting and user trust.

## Motivation

Floating-point arithmetic introduces subtle rounding errors that accumulate across transactions. In a cashback system, even microscopically small errors multiplied across thousands of users lead to significant discrepancies. Regulatory compliance and user trust demand precise financial calculations.

## Definition

- All monetary values must be stored and calculated using Decimal type with fixed precision.
- Currency amounts are represented in the smallest denomination (e.g., cents) as integers or fixed-scale decimals.
- Rounding is applied explicitly and consistently at defined business logic boundaries.

## Acceptance Criteria

- Database stores monetary values as NUMERIC(19, 2) or DECIMAL(19, 2).
- Python code uses `Decimal` type for all monetary calculations, never `float`.
- Unit tests verify calculations for edge cases (very small amounts, large totals).
- Rounding rules are documented (e.g., round to nearest cent, banker's rounding for splits).

## Technical Approach

- Define monetary value as a custom type or always cast to Decimal(10, 2) in services.
- Database schema for wallets and transactions uses NUMERIC(19, 2).
- PyDecimal library with explicit precision context: `Decimal(x).quantize(Decimal('0.01'))`.
- Business logic service layer enforces decimal calculations before database writes.
- Integration tests verify end-to-end financial calculations match expected results.
